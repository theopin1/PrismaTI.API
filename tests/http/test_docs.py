from flask import Flask
from prismati.presentation.http.blueprints.docs import build_docs

def test_docs_and_spec():
    app = Flask(__name__)
    app.register_blueprint(build_docs())
    client = app.test_client()
    assert client.get('/docs').status_code == 200
    assert client.get('/documentacao').status_code == 200
    spec = client.get('/openapi.json').json
    assert spec['servers'] == [{'url': '/api'}]
    assert spec['paths']['/autenticacao/entrar']['post']['security'] == []
    assert 'senha_hash' not in str(spec)
    assert spec['paths']['/usuarios']['post']['requestBody']['content']['application/json']['schema']['properties']['senha']['minLength'] == 7
    assert len(spec['paths']) == 34
    assert 'delete' not in spec['paths']['/avaliacoes/{id}']
    assert '/saude' in spec['paths']
    assert '/versoes/{id}/publicar' in spec['paths']
    for resource in ('empresas', 'usuarios', 'vinculos', 'questionarios', 'versoes',
                     'dimensoes', 'perguntas', 'alternativas', 'avaliacoes', 'respostas'):
        assert '/' + resource in spec['paths']
        assert '/' + resource + '/{id}' in spec['paths']
