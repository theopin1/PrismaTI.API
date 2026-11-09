from itsdangerous import URLSafeTimedSerializer
from prismati.bootstrap.app_factory import create_app
from prismati.infrastructure.persistence.models.tables import metadata, TABLES


def seeded_app(url="sqlite://"):
    app = create_app({'DATABASE_URL': url, 'SECRET_KEY': 'test-key'})
    db = app.extensions['database']
    metadata.create_all(db.engine)
    with db.transaction() as session:
        def insert(resource, **row):
            session.execute(TABLES[resource].insert().values(**row))

        insert('companies', id='c', razao_social='Empresa', cnpj='12345678000190',
               segmento='TI', porte='PME', status='ACTIVE', criado_em='hoje')
        insert('users', id='u', nome='Gestor', email='g@example.com', senha_hash='hash',
               role='MANAGER', status='ACTIVE', data_criacao='hoje')
        insert('memberships', id='m', usuario_id='u', empresa_id='c', criado_em='hoje')
        insert('questionnaires', id='i', nome='Instrumento', descricao='', status='ACTIVE')
        insert('versions', id='v', questionario_id='i', versao='1', versao_metodologia='1', status='PUBLISHED')
        insert('dimensions', id='d', versao_questionario_id='v', nome='TI', descricao='', ordem=1, codigo='D')
        insert('questions', id='q', dimensao_id='d', texto='Pergunta', ordem=1, codigo='Q', explicacao='', orientacao_evidencia='')
        insert('alternatives', id='alt', pergunta_id='q', descricao='Alternativa', ordem=1, pontuacao=3)
        insert('assessments', id='a', empresa_id='c', gestor_usuario_id='u', versao_questionario_id='v', status='IN_PROGRESS', iniciada_em='hoje')
        insert('answers', id='r', avaliacao_id='a', pergunta_id='q', versao_questionario_id='v',
               tipo_resposta='SCORED', alternativa_id='alt', atualizado_por='u', atualizado_em='hoje')
    return app


def test_finalize_store_and_lock_answers():
    app = seeded_app()
    token = URLSafeTimedSerializer('test-key', salt='prismati-access-v1').dumps('u')
    client = app.test_client()
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + token
    url = '/api/avaliacoes/a'
    assert client.get(url + '/resultado').status_code == 404
    response = client.post(url + '/finalizar')
    assert response.status_code == 200
    assert response.json['maturidade_geral'] == 75
    assert response.json['dimensoes'][0]['maturidade'] == 75
    assert client.get(url + '/resultado').json == response.json
    assert client.post(url + '/finalizar').json == response.json
    assert client.get(url).json['status'] == 'FINALIZED'
    assert client.delete('/api/respostas/r').status_code == 409

def test_workflows(monkeypatch):
    import io
    import json
    from prismati.presentation.http.blueprints import workflows, report_worker
    app = seeded_app()
    client = app.test_client()
    signer = URLSafeTimedSerializer('test-key', salt='prismati-access-v1')
    db = app.extensions['database']
    with db.transaction() as session:
        session.execute(TABLES['users'].insert().values(id='admin', nome='Admin', email='a@example.com',
            senha_hash='hash', role='ADMIN', status='ACTIVE', data_criacao='hoje'))
    delivered = []
    monkeypatch.setattr(workflows,'deliver', lambda email,token,action: delivered.append(token))
    monkeypatch.setenv('SMTP_HOST','mock')
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + signer.dumps('admin')
    assert client.post('/api/convites',json={'empresa_id':'c','email':'new@example.com'}).status_code==201
    data = dict(token=delivered.pop(),nome='Novo',senha='nova-senha')
    assert client.post('/api/convites/aceitar',json=data).status_code==201
    assert client.post('/api/convites/aceitar',json=data).status_code==400
    assert client.post('/api/autenticacao/recuperar-senha',json={'email':'new@example.com'}).status_code==202
    assert client.post('/api/autenticacao/redefinir-senha',json={'token':delivered.pop(),'senha':'alterada'}).status_code==204
    assert client.post('/api/autenticacao/entrar',json={'email':'new@example.com','senha':'alterada'}).status_code==200
    assert client.get('/api/auditoria').json
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + signer.dumps('u')
    assert client.get('/api/auditoria').status_code==403
    path = '/api/respostas/r/evidencias'
    assert client.post(path,json={'url':'https://example.org/doc'}).status_code==201
    file = client.post(path,data={'arquivo':(io.BytesIO(b'documento'),'prova.txt')})
    assert client.get('/api/evidencias/'+file.json['id']).data==b'documento'
    assert len(client.get(path).json)==2
    client.post('/api/avaliacoes/a/finalizar')
    assert client.delete('/api/evidencias/'+file.json['id']).status_code==409
    monkeypatch.setenv('AI_API_KEY','test')
    monkeypatch.setenv('AI_MODEL','test')
    monkeypatch.setattr(report_worker,'urlopen',lambda *args,**kwargs: io.BytesIO(json.dumps({
        'choices':[{'message':{'content':'Resultado de maturidade: 75%'}}], 'usage':{'total_tokens':30}}).encode()))
    job = client.post('/api/avaliacoes/a/relatorios')
    assert job.status_code==202
    assert report_worker.process_next(db)
    assert not report_worker.process_next(db)
    assert client.get('/api/avaliacoes/a/relatorios').json[0]['uso']['total_tokens']==30
    assert client.get('/api/relatorios/'+job.json['id']+'/pdf').data.startswith(b'%PDF')
    for _ in range(20):
        last = client.post('/api/autenticacao/entrar',json={'email':'bad','senha':'bad'})
    assert last.status_code==429


def test_postgres_finalization_race():
    import os
    import pytest
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from uuid import uuid4
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from prismati.bootstrap.config import load_config
    from prismati.application.use_cases.catalog import CatalogService
    from prismati.infrastructure.persistence.repositories.catalog import SqlCatalog
    from prismati.domain.exceptions.domain_exceptions import ConflictError
    if not os.getenv('PRISMATI_TEST_POSTGRES'):
        pytest.skip('Defina PRISMATI_TEST_POSTGRES=1 para testar o bloqueio no PostgreSQL local.')
    url = make_url(load_config()['DATABASE_URL'])
    engine = create_engine(url)
    for finalize_first in (True, False):
        schema = 'test_prisma_' + uuid4().hex
        with engine.begin() as conn:
            conn.execute(text('CREATE SCHEMA '+schema))
        try:
            app = seeded_app(url.update_query_dict({'options':'-csearch_path='+schema}))
            db = app.extensions['database']
            started = Event()
            def operate(session, close):
                service = CatalogService(SqlCatalog(session),lambda s:s)
                actor = service.require('users','u')
                if close:
                    return service.finalize(actor,'a')
                return service.save(actor,'answers',dict(tipo_resposta='NS',alternativa_id=None),'r')
            def contender():
                with db.transaction() as session:
                    started.set()
                    return operate(session,not finalize_first)
            with ThreadPoolExecutor(1) as pool:
                with db.transaction() as session:
                    operate(session,finalize_first)
                    future = pool.submit(contender)
                    assert started.wait(5)
                    from concurrent.futures import TimeoutError
                    with pytest.raises(TimeoutError):
                        future.result(timeout=0.3)
                if finalize_first:
                    with pytest.raises(ConflictError):
                        future.result(timeout=5)
                else:
                    assert future.result(timeout=5)['maturidade_geral'] is None
            db.engine.dispose()
        finally:
            with engine.begin() as conn:
                conn.execute(text('DROP SCHEMA '+schema+' CASCADE'))
    engine.dispose()
