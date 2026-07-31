from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.account import Account
from app.schemas.account import (
    AccountCreate,
    AccountResponse
)


router = APIRouter(
    prefix="/accounts",
    tags=["accounts"]
)


@router.post(
    "",
    response_model=AccountResponse
)
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db)
):

    db_account = Account(
        **account.model_dump()
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return db_account


@router.get(
    "",
    response_model=list[AccountResponse]
)
def get_accounts(
    db: Session = Depends(get_db)
):

    return db.query(Account).all()