"""Imported account activity and end-of-day values; money is never stored as float."""
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey, UniqueConstraint, CheckConstraint, Index, func
from app.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("account_id", "source", "external_id", name="uq_transaction_source"),
        CheckConstraint("type IN ('deposit','withdrawal','buy','sell','dividend','interest','fee','transfer')", name="ck_transaction_type"),
        CheckConstraint("(type IN ('deposit','sell','dividend','interest') AND amount >= 0) OR (type IN ('withdrawal','buy','fee') AND amount <= 0) OR type = 'transfer'", name="ck_transaction_cash_direction"),
        CheckConstraint("type NOT IN ('buy','sell') OR (security_name IS NOT NULL AND quantity IS NOT NULL AND unit_price IS NOT NULL AND unit_price >= 0 AND ((type = 'buy' AND quantity > 0) OR (type = 'sell' AND quantity < 0)))", name="ck_transaction_trade"),
        CheckConstraint("settlement_date IS NULL OR settlement_date >= trade_date", name="ck_transaction_settlement"),
        Index("ix_transactions_account_date", "account_id", "trade_date"),
    )
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    trade_date = Column(Date, nullable=False)
    settlement_date = Column(Date, nullable=True)
    type = Column(String(16), nullable=False)
    description = Column(String, nullable=False)
    # Signed cash movement. Buys reduce cash; sells increase it. Fees are separate rows.
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    security_name = Column(String, nullable=True)
    # Signed security units. Snapshot of the name survives a position being closed.
    quantity = Column(Numeric(18, 6), nullable=True)
    unit_price = Column(Numeric(18, 6), nullable=True)
    source = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AccountValuation(Base):
    __tablename__ = "account_valuations"
    __table_args__ = (
        UniqueConstraint("account_id", "as_of_date", "currency", name="uq_account_valuation_date_currency"),
        Index("ix_valuations_account_date", "account_id", "as_of_date"),
    )
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    as_of_date = Column(Date, nullable=False)
    currency = Column(String(3), nullable=False)
    cash_balance = Column(Numeric(18, 2), nullable=False)
    investment_value = Column(Numeric(18, 2), nullable=False)
    source = Column(String, nullable=False)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
