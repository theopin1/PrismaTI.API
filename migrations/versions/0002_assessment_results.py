from alembic import op
from prismati.infrastructure.persistence.models.tables import assessment_results

revision = '0002'
down_revision = '0001'

def upgrade():
    assessment_results.create(op.get_bind())

def downgrade():
    assessment_results.drop(op.get_bind())
