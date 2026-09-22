from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.dashboard import ClientDashboard
from app.utils.auth import get_current_user, require_client_access


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
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return build_dashboard(require_client_access(db, user, client_id))


def build_dashboard(client):
    total_assets = Decimal("0")

    banks = []

    for bank in client.banks:

        accounts = []

        for account in bank.accounts:

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

        banks.append(
            {
                "id": bank.id,
                "name": bank.name,
                "accounts": accounts
            }
        )

    return {
        "id": client.id,
        "first_name": client.first_name,
        "last_name": client.last_name,
        "total_assets": total_assets,
        "banks": banks
    }