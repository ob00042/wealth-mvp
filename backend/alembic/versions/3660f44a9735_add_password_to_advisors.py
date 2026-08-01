"""add_password_to_advisors

Revision ID: 3660f44a9735
Revises: 51d7d2626974
Create Date: 2026-08-01 13:15:45.193973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3660f44a9735'
down_revision: Union[str, Sequence[str], None] = '51d7d2626974'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add column as nullable first to handle existing data
    op.add_column('advisors', sa.Column('hashed_password', sa.String(), nullable=True))
    
    # Update existing advisors with a default hashed password (password: "temp123")
    op.execute("UPDATE advisors SET hashed_password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5N7f5y/LfPT2q' WHERE hashed_password IS NULL")
    
    # Then make it NOT NULL
    op.alter_column('advisors', 'hashed_password', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('advisors', 'hashed_password')
