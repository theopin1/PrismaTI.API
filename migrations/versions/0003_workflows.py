from alembic import op
from prismati.infrastructure.persistence.models.tables import access_links, evidence, reports, audit, login_limits

revision = '0003'
down_revision = '0002'
tables = (access_links, evidence, reports, audit, login_limits)

def upgrade():
    for table in tables:
        table.create(op.get_bind())

def downgrade():
    for table in reversed(tables):
        table.drop(op.get_bind())
