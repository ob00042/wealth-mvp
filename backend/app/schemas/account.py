from decimal import Decimal
from pydantic import BaseModel


class AccountBase(BaseModel):
    name: str
    account_type: str
    currency: str
    balance: Decimal
    bank_id: int


class AccountCreate(AccountBase):
    pass


class AccountRead(AccountBase):
    id: int

    class Config:
        from_attributes = True