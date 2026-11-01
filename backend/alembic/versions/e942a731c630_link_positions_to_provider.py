"""Optional provider product identifier for positions."""
from alembic import op
import sqlalchemy as sa
revision = 'e942a731c630'
down_revision = 'd291b830f142'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('positions', sa.Column('provider_product_id', sa.String(), nullable=True))


def downgrade():
    op.drop_column('positions', 'provider_product_id')
