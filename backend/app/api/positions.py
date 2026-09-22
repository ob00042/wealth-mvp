from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.client import Client
from app.models.bank import Bank
from app.models.account import Account
from app.models.position import Position
from app.models.advisor import Advisor
from app.schemas.position import PositionCreate, PositionRead
from app.utils.auth import get_current_user, get_current_advisor, require_client_access

router = APIRouter(prefix="/positions", tags=["positions"])


@router.post("", response_model=PositionRead)
def create_position(position: PositionCreate, advisor=Depends(get_current_advisor), db: Session = Depends(get_db)):
    parent = db.get(Account, position.account_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Account not found")
    require_client_access(db, advisor, parent.bank.client_id)
    record = Position(**position.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[PositionRead])
def get_positions(user=Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Position).join(Account).join(Bank).join(Client)
    if isinstance(user, Advisor):
        return query.filter(Client.advisor_id == user.id).all()
    return query.filter(Client.id == user.id).all()
