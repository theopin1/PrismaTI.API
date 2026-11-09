from alembic import context
from sqlalchemy import create_engine
from prismati.bootstrap.config import load_config
from prismati.infrastructure.persistence.models.tables import metadata

url = load_config()['DATABASE_URL']
if context.is_offline_mode():
    context.configure(url=url, target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
