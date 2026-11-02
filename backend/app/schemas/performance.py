from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class PerformancePeriod(BaseModel):
    start_date: date
    end_date: date
    opening_value: Decimal
    closing_value: Decimal
    contributions: Decimal
    withdrawals: Decimal
    net_flows: Decimal
    investment_gain: Decimal | None
    weighted_capital: Decimal
    return_rate: Decimal | None
    income: Decimal
    fees: Decimal
    issues: list[str]
    valid: bool


class PeriodRow(PerformancePeriod):
    label: str
    partial_period: bool


class PerformanceReport(BaseModel):
    currency: str
    method: str
    frequency: str
    requested_start: date | None
    requested_end: date | None
    expected_account_count: int
    sources: list[str]
    summary: PerformancePeriod | None
    periods: list[PeriodRow]
    issues: list[str]
