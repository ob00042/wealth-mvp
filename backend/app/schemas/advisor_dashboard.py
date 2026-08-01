from decimal import Decimal
from pydantic import BaseModel


class ClientSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    total_assets: Decimal


class AdvisorDashboard(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    clients: list[ClientSummary]