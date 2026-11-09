import click
from flask import Flask
from werkzeug.security import generate_password_hash
from prismati.bootstrap.config import load_config
from prismati.infrastructure.persistence.database import Database
from prismati.infrastructure.persistence.repositories.catalog import SqlCatalog
from prismati.application.use_cases.catalog import CatalogService
from prismati.presentation.http.blueprints.api import build_api
from prismati.presentation.http.blueprints.docs import build_docs


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(load_config() if config is None else config)
    database = Database(app.config['DATABASE_URL'])
    app.extensions['database'] = database
    app.register_blueprint(build_api(database, SqlCatalog), url_prefix='/api')
    app.register_blueprint(build_docs())

    @app.cli.command('create-admin')
    @click.option('--nome', prompt=True)
    @click.option('--email', prompt=True)
    @click.option('--senha', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(nome, email, senha):
        """Cria o primeiro administrador, sem senha padrÃ£o."""
        with database.transaction() as session:
            service = CatalogService(SqlCatalog(session),generate_password_hash)
            service.save({'role':'ADMIN','status':'ACTIVE'}, 'users',
                         dict(nome=nome,email=email,senha=senha,role='ADMIN',status='ACTIVE'))
        click.echo('Administrador criado.')

    from prismati.presentation.http.blueprints.report_worker import register_worker
    register_worker(app, database)
    return app
