"""Add transactions and dated account valuations."""
from alembic import op
import sqlalchemy as sa

revision = "d291b830f142"
down_revision = "c7e82a194301"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("settlement_date", sa.Date()),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("security_name", sa.String()),
        sa.Column("quantity", sa.Numeric(18, 6)),
        sa.Column("unit_price", sa.Numeric(18, 6)),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("account_id", "source", "external_id", name="uq_transaction_source"),
        sa.CheckConstraint("type IN ('deposit','withdrawal','buy','sell','dividend','interest','fee','transfer')", name="ck_transaction_type"),
        sa.CheckConstraint("(type IN ('deposit','sell','dividend','interest') AND amount >= 0) OR (type IN ('withdrawal','buy','fee') AND amount <= 0) OR type = 'transfer'", name="ck_transaction_cash_direction"),
        sa.CheckConstraint("type NOT IN ('buy','sell') OR (security_name IS NOT NULL AND quantity IS NOT NULL AND unit_price IS NOT NULL AND unit_price >= 0 AND ((type = 'buy' AND quantity > 0) OR (type = 'sell' AND quantity < 0)))", name="ck_transaction_trade"),
        sa.CheckConstraint("settlement_date IS NULL OR settlement_date >= trade_date", name="ck_transaction_settlement"),
    )
    op.create_index("ix_transactions_account_date", "transactions", ["account_id", "trade_date"])
    op.create_table(
        "account_valuations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("cash_balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("investment_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("account_id", "as_of_date", "currency", name="uq_account_valuation_date_currency"),
    )
    op.create_index("ix_valuations_account_date", "account_valuations", ["account_id", "as_of_date"])


def downgrade():
    op.drop_table("account_valuations")
    op.drop_table("transactions")
