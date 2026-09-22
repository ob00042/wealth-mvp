from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.client import Client
from app.models.bank import Bank
from app.models.advisor import Advisor
from app.schemas.bank import BankCreate, BankRead
from app.utils.auth import get_current_user, get_current_advisor, require_client_access

router = APIRouter(prefix="/banks", tags=["banks"])


@router.post("", response_model=BankRead)
def create_bank(bank: BankCreate, advisor=Depends(get_current_advisor), db: Session = Depends(get_db)):
    parent = db.get(Client, bank.client_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Client not found")
    require_client_access(db, advisor, parent.id)
    record = Bank(**bank.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[BankRead])
def get_banks(user=Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Bank).join(Client)
    if isinstance(user, Advisor):
        return query.filter(Client.advisor_id == user.id).all()
    return query.filter(Client.id == user.id).all()
