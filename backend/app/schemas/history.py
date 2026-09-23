from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict

TransactionType = Literal['deposit', 'withdrawal', 'buy', 'sell', 'dividend', 'interest', 'fee', 'transfer']


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: int
    account_name: str
    bank_name: str
    trade_date: date
    settlement_date: date | None
    type: TransactionType
    description: str
    amount: Decimal
    currency: str
    security_name: str | None
    quantity: Decimal | None
    unit_price: Decimal | None
    source: str
    external_id: str
    imported_at: datetime


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int


class ValuationPoint(BaseModel):
    as_of_date: date
    currency: str
    cash_balance: Decimal
    investment_value: Decimal
    total_value: Decimal
    account_count: int
    expected_account_count: int
    complete: bool
    sources: list[str]


class ValuationHistory(BaseModel):
    items: list[ValuationPoint]
