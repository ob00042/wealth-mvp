from decimal import Decimal
from pydantic import BaseModel


class PositionBase(BaseModel):
    security_name: str
    provider_product_id: str | None = None
    ticker: str | None = None
    asset_type: str | None = None
    quantity: Decimal
    market_value: Decimal
    currency: str
    account_id: int


class PositionCreate(PositionBase):
    pass


class PositionRead(PositionBase):
    id: int

    class Config:
        from_attributes = True