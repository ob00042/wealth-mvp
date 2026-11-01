from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class Product(BaseModel):
    id: str
    name: str
    ticker: str
    product_type: str
    currency: str = Field(pattern=r'^[A-Z]{3}$')
    manager: str
    source: str = 'fictional-provider-v1'
    synthetic: bool = True


class Constituent(BaseModel):
    security_id: str
    name: str
    asset_class: str
    sector: str
    country: str
    currency: str = Field(pattern=r'^[A-Z]{3}$')
    weight: Decimal = Field(gt=0, le=1)


class HoldingsSnapshot(BaseModel):
    product_id: str
    as_of_date: date
    holdings: list[Constituent]

    @model_validator(mode='after')
    def validate_holdings(self):
        if sum((h.weight for h in self.holdings), Decimal(0)) > 1:
            raise ValueError('Constituent weights cannot exceed 100%')
        ids = [h.security_id for h in self.holdings]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate constituent identifier')
        return self


class ProductHoldings(BaseModel):
    product: Product
    as_of_date: date
    requested_as_of: date
    available_dates: list[date]
    age_days: int
    stale: bool
    stale_after_days: int
    coverage: Decimal
    unreported_weight: Decimal
    holdings: list[Constituent]
