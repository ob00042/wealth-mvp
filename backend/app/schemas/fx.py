from datetime import date
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field, model_validator


class CurrencyValue(BaseModel):
    currency: str
    original_value: Decimal
    rate: Decimal | None
    converted_value: Decimal | None


class ConvertedPosition(CurrencyValue):
    institution: str
    account: str
    name: str
    kind: str


class ReportingValuation(BaseModel):
    reporting_currency: str
    requested_as_of: date
    rate_date: date | None
    source: str
    synthetic: bool
    stale: bool
    stale_after_days: int
    supported_currencies: list[str]
    complete: bool
    missing_currencies: list[str]
    total_assets: Decimal | None
    converted_subtotal: Decimal
    cash: Decimal
    investments: Decimal
    currency_breakdown: list[CurrencyValue]
    rows: list[ConvertedPosition]


CurrencyCode = Annotated[str, Field(pattern='^[A-Z]{3}$')]
PositiveRate = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]


class FxSnapshot(BaseModel):
    as_of_date: date
    base_currency: CurrencyCode
    rates: dict[CurrencyCode, PositiveRate]

    @model_validator(mode='after')
    def validate_base(self):
        if self.rates.get(self.base_currency) != Decimal(1):
            raise ValueError('Base currency rate must equal 1')
        return self


class FxRates(FxSnapshot):
    requested_as_of: date
    source: str
    synthetic: bool
    supported_currencies: list[str]
    age_days: int
    stale: bool
    stale_after_days: int
