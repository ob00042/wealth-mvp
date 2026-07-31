from decimal import Decimal
from pydantic import BaseModel


class AccountCreate(BaseModel):
    name: str
    account_type: str
    currency: str
    balance: Decimal
    institution_id: int


class AccountResponse(BaseModel):
    id: int
    name: str
    account_type: str
    currency: str
    balance: Decimal

    class Config:
        from_attributes = True