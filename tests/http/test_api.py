from contextlib import contextmanager
from flask import Flask
import pytest
from prismati.presentation.http.blueprints.api import build_api

class DummyDatabase:
    @contextmanager
    def transaction(self): yield None

class DummyRepository:
    def __init__(self, session): pass

def client():
    app=Flask(__name__)
    app.config.update(TESTING=True,SECRET_KEY='test-key')
    app.register_blueprint(build_api(DummyDatabase(),DummyRepository),url_prefix='/api')
    return app.test_client()

def test_health():
    assert client().get('/api/saude').json == {'status':'ok'}

def test_requires_authentication():
    assert client().get('/api/empresas').status_code == 401

def test_login_requires_json_object():
    assert client().post('/api/autenticacao/entrar',json=[]).status_code == 400

def test_unknown_resource():
    assert client().get('/api/unknown').status_code == 404


@pytest.mark.parametrize('resource', [
    'empresas', 'usuarios', 'vinculos', 'questionarios', 'versoes',
    'dimensoes', 'perguntas', 'alternativas', 'avaliacoes', 'respostas',
])
def test_portuguese_resources_require_authentication(resource):
    api = client()
    for method in ('GET', 'POST'):
        assert api.open('/api/' + resource, method=method).status_code == 401
    for method in ('GET', 'PATCH', 'DELETE'):
        assert api.open('/api/' + resource + '/123', method=method).status_code == 401


def test_portuguese_publish_requires_authentication():
    assert client().post('/api/versoes/123/publicar').status_code == 401


@pytest.mark.parametrize('path', [
    '/companies', '/users', '/memberships', '/questionnaires', '/versions',
    '/dimensions', '/questions', '/alternatives', '/assessments', '/answers',
    '/health',
])
def test_english_resources_are_not_exposed(path):
    assert client().get('/api' + path).status_code == 404
