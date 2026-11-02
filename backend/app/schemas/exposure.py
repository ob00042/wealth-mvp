from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class Contribution(BaseModel):
    position: str
    account: str
    position_id: int
    kind: str
    value: Decimal
    weight: Decimal
    snapshot_date: date
    stale: bool


class SecurityExposure(BaseModel):
    security_id: str
    name: str
    asset_class: str
    sector: str
    country: str
    direct_value: Decimal
    indirect_value: Decimal
    total_value: Decimal
    portfolio_weight: Decimal
    contributions: list[Contribution]


class Allocation(BaseModel):
    name: str
    value: Decimal
    portfolio_weight: Decimal


class Unresolved(BaseModel):
    position: str
    account: str
    value: Decimal
    reason: str


class Source(BaseModel):
    position_id: int
    account: str
    position: str
    product_id: str | None
    value: Decimal
    snapshot_date: date | None
    stale: bool
    coverage: Decimal
    status: str


class Overlap(BaseModel):
    left: str
    right: str
    securities: list[str]
    shared_value: Decimal


class PortfolioExposure(BaseModel):
    currency: str
    composition_cutoff: date
    total_assets: Decimal
    cash: Decimal
    investment_value: Decimal
    resolved_value: Decimal
    unresolved_value: Decimal
    investment_coverage: Decimal | None
    stale_position_value: Decimal
    securities: list[SecurityExposure]
    allocations: dict[str, list[Allocation]]
    overlaps: list[Overlap]
    unresolved: list[Unresolved]
    sources: list[Source]
