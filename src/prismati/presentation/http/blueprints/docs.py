"""OpenAPI e Swagger UI para os endpoints implementados."""
from dataclasses import MISSING, fields
from flask import Blueprint, render_template_string
from prismati.application.use_cases.catalog import EDITABLE, ENTITIES, CNPJ_PATTERN
from prismati.presentation.http.routes import RESOURCES


def specification():
    spec = {
        'openapi': '3.0.3',
        'info': {'title': 'PrismaTI API', 'version': '0.1.0',
                 'description': 'CRUDs básicos. Faça login e cole o access_token em Authorize. Evidências e IA ainda não estão integradas.'},
        'servers': [{'url': '/api'}],
        'security': [{'bearerAuth': []}],
        'components': {'securitySchemes': {'bearerAuth': {'type': 'http', 'scheme': 'bearer'}}},
        'paths': {},
    }

    def operation(summary, tag, success='200', schema=None, public=False):
        result = {'summary': summary, 'tags': [tag], 'responses': {
            success: {'description': 'Operação concluída'},
            '400': {'description': 'Dados inválidos'},
            '401': {'description': 'Autenticação necessária ou inválida'},
            '403': {'description': 'Sem permissão'},
            '404': {'description': 'Recurso não encontrado'},
            '409': {'description': 'Conflito ou recurso protegido'},
            '503': {'description': 'Banco indisponível'},
        }}
        if public: result['security'] = []
        if schema:
            result['requestBody'] = {'required': True, 'content': {'application/json': {'schema': schema}}}
        return result

    spec['paths']['/saude'] = {'get': operation('Verificar API', 'Sistema', public=True)}
    spec['paths']['/autenticacao/entrar'] = {'post': operation('Obter token de acesso', 'Autenticação', public=True, schema={
        'type': 'object', 'required': ['email', 'senha'], 'properties': {
            'email': {'type': 'string', 'format': 'email'},
            'senha': {'type': 'string', 'format': 'password'},
        }})}
    for route, resource in RESOURCES.items():
        entity = ENTITIES[resource]
        properties = {}
        for name in sorted(EDITABLE[resource]):
            prop = {'type': 'integer' if name in ('ordem', 'pontuacao') else 'string'}
            if name in ('ordem', 'pontuacao'): prop['minimum'] = 0
            if name == 'pontuacao': prop['maximum'] = 4
            if name.endswith('_id'): prop['format'] = 'uuid'
            if name == 'senha': prop.update(format='password', minLength=7)
            if name == 'email': prop['format'] = 'email'
            if name == 'cnpj':
                prop.update(pattern='^' + CNPJ_PATTERN + '$', minLength=14,
                            description='Após remover pontos, barras (/ e \\) e hífens: 14 caracteres, sendo os primeiros 12 letras ou números e os últimos dois números. Salvo sem máscara e em maiúsculas.',
                            example='12.ABC.345/01DE-35')
            if name == 'role': prop['enum'] = ['ADMIN', 'MANAGER', 'IT_RESPONSIBLE']
            if resource == 'users' and name == 'status':
                prop.update(enum=['ACTIVE', 'INACTIVE', 'PENDING'], example='ACTIVE', default='PENDING')
            if name == 'tipo_resposta': prop['enum'] = ['SCORED', 'NA', 'NS']
            if name in ('alternativa_id', 'justificativa'): prop['nullable'] = True
            properties[name] = prop
        required = [f.name for f in fields(entity) if f.default is MISSING and f.default_factory is MISSING and f.name in properties]
        if resource == 'users': required.append('senha')
        schema = {'type': 'object', 'additionalProperties': False, 'properties': properties, 'required': required}
        listing = operation('Listar ' + route, route)
        listing['parameters'] = [
            {'name': 'offset', 'in': 'query', 'schema': {'type': 'integer', 'minimum': 0, 'default': 0}},
            {'name': 'limit', 'in': 'query', 'schema': {'type': 'integer', 'minimum': 1, 'maximum': 100, 'default': 50}},
        ]
        spec['paths']['/' + route] = {'get': listing, 'post': operation('Criar ' + route, route, '201', schema)}
        detail = {
            'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'string', 'format': 'uuid'}}],
            'get': operation('Consultar por ID', route),
            'patch': operation('Atualizar campos', route, schema={k:v for k,v in schema.items() if k != 'required'}),
        }
        if resource != 'assessments':
            detail['delete'] = operation('Inativar registro' if resource in ('companies','users') else 'Excluir registro não protegido',route,'204')
        spec['paths']['/' + route + '/{id}'] = detail
    spec['paths']['/versoes/{id}/publicar'] = {
        'parameters': [{'name':'id','in':'path','required':True,'schema':{'type':'string','format':'uuid'}}],
        'post': operation('Publicar versão (30 perguntas, sete dimensões)', 'versoes'),
    }
    for action, method, summary in [('finalizar', 'post', 'Finalizar avaliação e calcular maturidade'),
                                    ('resultado', 'get', 'Consultar resultado salvo')]:
        spec['paths']['/avaliacoes/{id}/' + action] = {
            'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}],
            method: operation(summary, 'avaliacoes'),
        }
    workflows = [
        ('/convites', 'post', 'Enviar convite', ['email','empresa_id'], False),
        ('/convites/aceitar', 'post', 'Aceitar convite', ['token','nome','senha'], True),
        ('/autenticacao/recuperar-senha', 'post', 'Solicitar código por e-mail', ['email'], True),
        ('/autenticacao/redefinir-senha', 'post', 'Redefinir senha', ['token','senha'], True),
        ('/respostas/{id}/evidencias', 'get', 'Listar evidências', [], False),
        ('/respostas/{id}/evidencias', 'post', 'Anexar arquivo ou link', ['url'], False),
        ('/evidencias/{id}', 'get', 'Obter evidência', [], False),
        ('/evidencias/{id}', 'delete', 'Excluir evidência', [], False),
        ('/auditoria', 'get', 'Consultar as últimas 100 operações', [], False),
        ('/avaliacoes/{id}/relatorios', 'post', 'Solicitar nova geração', [], False),
        ('/avaliacoes/{id}/relatorios', 'get', 'Consultar gerações e relatórios', [], False),
        ('/relatorios/{id}/pdf', 'get', 'Baixar relatório em PDF', [], False),
    ]
    for path, method, summary, names, public in workflows:
        target = spec['paths'].setdefault(path,{})
        if '{id}' in path:
            target['parameters'] = [{'name':'id','in':'path','required':True,'schema':{'type':'string'}}]
        schema = {'type':'object','required':names,'properties':{n:{'type':'string'} for n in names}} if names else None
        if path == '/convites':
            schema['properties']['role'] = {'type':'string','enum':['MANAGER','IT_RESPONSIBLE'],'default':'MANAGER'}
        success = '200'
        if method == 'delete' or path.endswith('redefinir-senha'):
            success = '204'
        elif method == 'post':
            success = '202' if path.endswith(('relatorios','recuperar-senha')) else '201'
        group = path.split('/')[1]
        tag = 'Autenticação' if group == 'autenticacao' else group
        entry = operation(summary, tag, success, schema, public)
        if method == 'post' and path.endswith('/evidencias'):
            entry['requestBody']['content']['multipart/form-data'] = {'schema':{'type':'object','required':['arquivo'],'properties':{'arquivo':{'type':'string','format':'binary'}}}}
        target[method] = entry
    return spec


def build_docs():
    docs = Blueprint('docs', __name__)

    @docs.get('/openapi.json')
    def openapi():
        return specification()

    @docs.get('/docs')
    @docs.get('/docs/')
    @docs.get('/documentacao')
    @docs.get('/documentacao/')
    def swagger():
        return render_template_string('''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>PrismaTI — Swagger</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css"></head>
<body><div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url: {{ url_for('docs.openapi')|tojson }}, dom_id: '#swagger-ui',
persistAuthorization: false, validatorUrl: null});</script></body></html>''')

    return docs
