import hashlib
import os
import secrets
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps
from io import BytesIO
from urllib.parse import urlsplit
from uuid import uuid4

from flask import abort, current_app, g, jsonify, request, send_file
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from prismati.application.use_cases.catalog import CatalogService
from prismati.infrastructure.persistence.models.tables import login_limits, evidence, audit


def now():
    return datetime.now(timezone.utc)


def limit_login(database):
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    stamp = int(time.time())
    key = hashlib.sha256((request.remote_addr or '').encode()).hexdigest()[:32]
    with database.transaction() as session:
        insert = pg_insert if session.bind.dialect.name == 'postgresql' else sqlite_insert
        session.execute(insert(login_limits).values(id=key, inicio=stamp, tentativas=0).on_conflict_do_nothing())
        row = session.execute(select(login_limits).where(login_limits.c.id == key).with_for_update()).mappings().one()
        start, count = (stamp, 0) if stamp - row['inicio'] >= 300 else (row['inicio'], row['tentativas'])
        if count >= 20:
            abort(429, 'Limite de tentativas atingido. Aguarde cinco minutos.')
        session.execute(login_limits.update().where(login_limits.c.id == key).values(inicio=start, tentativas=count+1))


def deliver(email, token, action):
    host = os.getenv('SMTP_HOST')
    if not host or not os.getenv('SMTP_FROM'):
        abort(503, 'Configure SMTP_HOST e SMTP_FROM para enviar e-mail.')
    message = EmailMessage()
    message['From'] = os.environ['SMTP_FROM']
    message['To'] = email
    message['Subject'] = 'PrismaTI — ' + action
    message.set_content(f'Use este código em {action}: {token}')
    with smtplib.SMTP(host, int(os.getenv('SMTP_PORT', '587')), timeout=15) as smtp:
        if os.getenv('SMTP_STARTTLS', '1') == '1':
            smtp.starttls()
        if os.getenv('SMTP_USER'):
            smtp.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
        smtp.send_message(message)


def register_workflows(api, db, factory, actor):
    def route(path, methods, public=False):
        def decorate(fn):
            @api.route(path, methods=methods)
            @wraps(fn)
            def handle(**params):
                with db.transaction() as session:
                    repo = factory(session)
                    user = None if public else actor(repo)
                    return fn(repo, CatalogService(repo, generate_password_hash), user, **params)
            return handle
        return decorate

    def body():
        data = request.get_json()
        if not isinstance(data, dict):
            abort(400)
        return data

    def admin(user):
        if user['role'] != 'ADMIN':
            abort(403)

    def issue(repo, email, kind, hours, **fields):
        token = secrets.token_urlsafe(32)
        repo.save('access_links', dict(id=str(uuid4()), digest=hashlib.sha256(token.encode()).hexdigest(),
            email=email, tipo=kind, expira=(now()+timedelta(hours=hours)).isoformat(), **fields))
        deliver(email, token, kind)

    def consume(repo, data, kind):
        token = data.get('token')
        if not isinstance(token, str):
            abort(400)
        rows = repo.list('access_links', {'digest': hashlib.sha256(token.encode()).hexdigest(), 'tipo': kind})
        link = repo.get('access_links', rows[0]['id'], True) if rows else None
        if not link or link['usado'] or link['expira'] <= now().isoformat():
            abort(400, 'Código inválido ou expirado.')
        link['usado'] = now().isoformat()
        repo.save('access_links', link)
        return link

    @route('/convites', ['POST'])
    def invite(repo, service, user):
        admin(user)
        data = body()
        email = data.get('email')
        role = data.get('role', 'MANAGER')
        if not isinstance(email, str) or '@' not in email or role not in ('MANAGER', 'IT_RESPONSIBLE'):
            abort(400)
        email = email.strip().lower()
        company = service.require('companies', data.get('empresa_id'))
        if company['status'] != 'ACTIVE' or repo.list('users', {'email': email}):
            abort(409)
        issue(repo, email, 'aceitar convite', 72, empresa_id=company['id'], perfil=role)
        return '', 201

    @route('/convites/aceitar', ['POST'], True)
    def accept(repo, service, user):
        data = body()
        link = consume(repo, data, 'aceitar convite')
        if service.require('companies', link['empresa_id'])['status'] != 'ACTIVE':
            abort(409)
        system = {'role':'ADMIN','status':'ACTIVE'}
        created = service.save(system, 'users', dict(nome=data.get('nome',''), email=link['email'],
            senha=data.get('senha'), role=link['perfil'], status='ACTIVE'))
        g.actor_id = created['id']
        service.save(system, 'memberships', dict(empresa_id=link['empresa_id'], usuario_id=created['id']))
        return created, 201

    @route('/autenticacao/recuperar-senha', ['POST'], True)
    def recover(repo, service, user):
        email = body().get('email')
        if not isinstance(email,str):
            abort(400)
        if not os.getenv('SMTP_HOST'):
            abort(503, 'Configure SMTP para recuperar a senha.')
        users = repo.list('users', {'email':email.strip().lower(), 'status':'ACTIVE'})
        if users:
            issue(repo, users[0]['email'], 'redefinir senha', 1, usuario_id=users[0]['id'])
        return '', 202

    @route('/autenticacao/redefinir-senha', ['POST'], True)
    def reset(repo, service, user):
        data = body()
        link = consume(repo, data, 'redefinir senha')
        g.actor_id = link['usuario_id']
        service.save({'role':'ADMIN','status':'ACTIVE'}, 'users', {'senha':data.get('senha')}, link['usuario_id'])
        return '', 204

    @route('/respostas/<identifier>/evidencias', ['GET','POST'])
    def attachments(repo, service, user, identifier):
        answer = service.require('answers', identifier)
        service.authorize(user, 'answers', answer, request.method == 'POST')
        if request.method == 'GET':
            query = select(evidence.c.id, evidence.c.nome, evidence.c.url).where(evidence.c.resposta_id==identifier)
            return jsonify([dict(r) for r in repo.session.execute(query).mappings()])
        service.writable('answers', answer)
        file = request.files.get('arquivo')
        if file:
            name, url, content = file.filename, None, file.read(10*1024*1024+1)
            if len(content)>10*1024*1024:
                abort(413)
        else:
            data = body()
            url = data.get('url')
            if not isinstance(url,str) or urlsplit(url).scheme not in ('http','https') or not urlsplit(url).hostname:
                abort(400)
            name, content = url, None
        eid = str(uuid4())
        repo.save('evidence', dict(id=eid,resposta_id=identifier,autor=user['id'],nome=name,url=url,arquivo=content))
        return {'id':eid}, 201

    @route('/evidencias/<identifier>', ['GET','DELETE'])
    def attachment(repo, service, user, identifier):
        item = service.require('evidence',identifier)
        answer = service.require('answers',item['resposta_id'])
        service.authorize(user,'answers',answer,request.method=='DELETE')
        if request.method=='DELETE':
            service.writable('answers',answer)
            repo.delete('evidence',identifier)
            return '',204
        if item['url']:
            return {'url':item['url']}
        return send_file(BytesIO(item['arquivo']),download_name=item['nome'],as_attachment=True,mimetype='application/octet-stream')

    @route('/auditoria', ['GET'])
    def events(repo, service, user):
        admin(user)
        return jsonify([dict(r) for r in repo.session.execute(select(audit).order_by(audit.c.data.desc()).limit(100)).mappings()])

    @route('/avaliacoes/<identifier>/relatorios', ['POST','GET'])
    def report_jobs(repo, service, user, identifier):
        service.result(user,identifier)
        if request.method=='GET':
            return jsonify(repo.list('reports',{'avaliacao_id':identifier}))
        if user['role'] not in ('MANAGER','ADMIN'):
            abort(403)
        if not os.getenv('AI_API_KEY') or not os.getenv('AI_MODEL'):
            abort(503,'Configure AI_API_KEY e AI_MODEL.')
        service.require('assessments', identifier, True)
        if len(repo.list('reports', {'avaliacao_id':identifier})) >= int(os.getenv('AI_REPORT_LIMIT','10')):
            abort(429, 'Limite de gerações desta avaliação atingido.')
        job = repo.save('reports',dict(id=str(uuid4()),avaliacao_id=identifier,status='PENDING',criado_em=now().isoformat()))
        return job,202

    @route('/relatorios/<identifier>/pdf', ['GET'])
    def pdf(repo, service, user, identifier):
        job = service.require('reports',identifier)
        service.read(user,'assessments',job['avaliacao_id'])
        if job['status']!='COMPLETED':
            abort(409)
        from .report_worker import render_pdf
        return send_file(render_pdf(job['texto']),mimetype='application/pdf',as_attachment=True,download_name='relatorio.pdf')
