from decimal import Decimal
from pydantic import BaseModel


class PositionDashboard(BaseModel):
    security_name: str
    quantity: Decimal
    market_value: Decimal
    currency: str


class AccountDashboard(BaseModel):
    id: int
    name: str
    account_type: str
    currency: str
    balance: Decimal
    positions: list[PositionDashboard]


class InstitutionDashboard(BaseModel):
    id: int
    name: str
    accounts: list[AccountDashboard]


class ClientDashboard(BaseModel):
    id: int
    name: str
    total_assets: Decimal
    institutions: list[InstitutionDashboard]