from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.bank import Bank
from app.schemas.bank import (
    BankCreate,
    BankRead
)


router = APIRouter(
    prefix="/banks",
    tags=["banks"]
)


@router.post(
    "",
    response_model=BankRead
)
def create_bank(
    bank: BankCreate,
    db: Session = Depends(get_db)
):

    db_bank = Bank(
        **bank.model_dump()
    )

    db.add(db_bank)
    db.commit()
    db.refresh(db_bank)

    return db_bank


@router.get(
    "",
    response_model=list[BankRead]
)
def get_banks(
    db: Session = Depends(get_db)
):

    return db.query(Bank).all()
