from flask import Blueprint, request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from prismati.application.use_cases.catalog import CatalogService
from prismati.presentation.http.routes import RESOURCES
from prismati.domain.exceptions.domain_exceptions import (DomainException,ForbiddenError,NotFoundError,ConflictError,ValidationError)


def build_api(database, repository_factory):
    api = Blueprint('api',__name__)

    def serializer():
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'],salt='prismati-access-v1')

    def actor(repo):
        header = request.headers.get('Authorization','')
        if not header.startswith('Bearer '): raise Unauthorized()
        try:
            uid = serializer().loads(header[7:],max_age=3600)
        except (BadSignature,SignatureExpired):
            raise Unauthorized()
        user = repo.get('users',uid)
        if not user or user['status'] != 'ACTIVE': raise Unauthorized()
        from flask import g
        g.actor_id = user['id']
        return user

    @api.get('/saude')
    def health():
        return {'status':'ok'}

    @api.post('/autenticacao/entrar')
    def login():
        payload = request.get_json()
        if not isinstance(payload,dict) or not isinstance(payload.get('email'),str) or not isinstance(payload.get('senha'),str):
            raise ValidationError('Informe email e senha.')
        from .workflows import limit_login
        limit_login(database)
        with database.transaction() as session:
            repo = repository_factory(session)
            users = repo.list('users',{'email':payload['email'].strip().lower()})
            if not users or not check_password_hash(users[0]['senha_hash'],payload['senha']) or users[0]['status'] != 'ACTIVE':
                raise Unauthorized()
            user = users[0]
            service = CatalogService(repo,generate_password_hash)
            service.authorize(user,'users',user)
            return {'access_token':serializer().dumps(user['id']), 'token_type':'Bearer','expires_in':3600}

    @api.route('/<resource>',methods=['GET','POST'])
    @api.route('/<resource>/<identifier>',methods=['GET','PATCH','DELETE'])
    def crud(resource,identifier=None):
        resource = RESOURCES.get(resource)
        if resource is None: raise NotFoundError()
        with database.transaction() as session:
            repo = repository_factory(session)
            user = actor(repo)
            service = CatalogService(repo,generate_password_hash)
            if request.method == 'GET':
                if identifier: return service.read(user,resource,identifier)
                try:
                    offset = int(request.args.get('offset',0))
                    limit = int(request.args.get('limit',50))
                    if offset < 0 or not 1 <= limit <= 100: raise ValueError()
                except ValueError: raise ValidationError('Paginação inválida: offset >= 0; limit entre 1 e 100.')
                return service.listing(user,resource,offset,limit)
            if request.method == 'DELETE':
                service.delete(user,resource,identifier)
                return '',204
            return service.save(user,resource,request.get_json(),identifier), 201 if request.method == 'POST' else 200

    @api.post('/avaliacoes/<identifier>/finalizar')
    def finalize(identifier):
        with database.transaction() as session:
            repo = repository_factory(session)
            return CatalogService(repo, generate_password_hash).finalize(actor(repo), identifier)

    @api.get('/avaliacoes/<identifier>/resultado')
    def result(identifier):
        with database.transaction() as session:
            repo = repository_factory(session)
            return CatalogService(repo, generate_password_hash).result(actor(repo), identifier)

    @api.post('/versoes/<identifier>/publicar')
    def publish(identifier):
        with database.transaction() as session:
            repo = repository_factory(session)
            return CatalogService(repo,generate_password_hash).publish(actor(repo),identifier)

    @api.app_errorhandler(DomainException)
    def domain_error(error):
        status = 403 if isinstance(error,ForbiddenError) else 404 if isinstance(error,NotFoundError) else 409 if isinstance(error,ConflictError) else 400
        return {'error':type(error).__name__,'message':str(error)},status

    @api.app_errorhandler(Unauthorized)
    def unauthorized(error):
        return {'error':'Unauthorized','message':'Credenciais inválidas ou sessão expirada.'},401

    @api.app_errorhandler(IntegrityError)
    def integrity(error):
        return {'error':'Conflict','message':'Registro duplicado, vínculo inválido ou recurso ainda referenciado.'},409

    @api.app_errorhandler(OperationalError)
    def unavailable(error):
        current_app.logger.error('Banco indisponível.')
        return {'error':'Unavailable','message':'Banco de dados indisponível.'},503

    @api.app_errorhandler(HTTPException)
    def http_error(error):
        return {'error':error.name,'message':error.description},error.code

    from .workflows import register_workflows
    register_workflows(api, database, repository_factory, actor)
    return api


class Unauthorized(Exception):
    pass
