from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.client import Client
from app.models.bank import Bank
from app.models.account import Account
from app.models.advisor import Advisor
from app.schemas.account import AccountCreate, AccountRead
from app.utils.auth import get_current_user, get_current_advisor, require_client_access

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead)
def create_account(account: AccountCreate, advisor=Depends(get_current_advisor), db: Session = Depends(get_db)):
    parent = db.get(Bank, account.bank_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Bank not found")
    require_client_access(db, advisor, parent.client_id)
    record = Account(**account.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[AccountRead])
def get_accounts(user=Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Account).join(Bank).join(Client)
    if isinstance(user, Advisor):
        return query.filter(Client.advisor_id == user.id).all()
    return query.filter(Client.id == user.id).all()
