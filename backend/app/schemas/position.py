from decimal import Decimal
from pydantic import BaseModel


class PositionCreate(BaseModel):
    security_name: str
    quantity: Decimal
    market_value: Decimal
    currency: str
    account_id: int


class PositionResponse(BaseModel):
    id: int
    security_name: str
    quantity: Decimal
    market_value: Decimal
    currency: str

    class Config:
        from_attributes = True