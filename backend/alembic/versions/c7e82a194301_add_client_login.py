"""Add optional login credentials for existing clients."""
from alembic import op
import sqlalchemy as sa

revision = "c7e82a194301"
down_revision = "3660f44a9735"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("clients", sa.Column("email", sa.String(), nullable=True))
    op.add_column("clients", sa.Column("hashed_password", sa.String(), nullable=True))
    op.create_index("ix_clients_email", "clients", ["email"], unique=True)


def downgrade():
    op.drop_index("ix_clients_email", table_name="clients")
    op.drop_column("clients", "hashed_password")
    op.drop_column("clients", "email")
