from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.client import Client
from app.schemas.dashboard import ClientDashboard


router = APIRouter(
    prefix="/clients",
    tags=["dashboard"]
)


@router.get(
    "/{client_id}/dashboard",
    response_model=ClientDashboard
)
def get_dashboard(
    client_id: int,
    db: Session = Depends(get_db)
):

    client = (
        db.query(Client)
        .filter(Client.id == client_id)
        .first()
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    total_assets = Decimal("0")

    institutions = []

    for institution in client.institutions:

        accounts = []

        for account in institution.accounts:

            total_assets += account.balance

            positions = []

            for position in account.positions:

                total_assets += position.market_value

                positions.append(
                    {
                        "security_name": position.security_name,
                        "quantity": position.quantity,
                        "market_value": position.market_value,
                        "currency": position.currency
                    }
                )

            accounts.append(
                {
                    "id": account.id,
                    "name": account.name,
                    "account_type": account.account_type,
                    "currency": account.currency,
                    "balance": account.balance,
                    "positions": positions
                }
            )

        institutions.append(
            {
                "id": institution.id,
                "name": institution.name,
                "accounts": accounts
            }
        )

    return {
        "id": client.id,
        "name": client.name,
        "total_assets": total_assets,
        "institutions": institutions
    }