"""Initial schema for the ten core resources."""
from alembic import op
from prismati.infrastructure.persistence.models.tables import metadata

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    metadata.create_all(op.get_bind(), tables=[t for t in metadata.sorted_tables if t.name in ('companies','users','memberships','questionnaires','versions','dimensions','questions','alternatives','assessments','answers')])

def downgrade():
    metadata.drop_all(op.get_bind(), tables=[t for t in metadata.sorted_tables if t.name in ('companies','users','memberships','questionnaires','versions','dimensions','questions','alternatives','assessments','answers')])
