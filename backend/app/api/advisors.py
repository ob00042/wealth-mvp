from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.advisor import Advisor
from app.schemas.advisor import AdvisorCreate, AdvisorRead
from app.schemas.advisor_dashboard import AdvisorDashboard

router = APIRouter(prefix="/advisors", tags=["Advisors"])


@router.post("", response_model=AdvisorRead)
def create_advisor(advisor: AdvisorCreate, db: Session = Depends(get_db)):
    db_advisor = Advisor(**advisor.model_dump())
    db.add(db_advisor)
    db.commit()
    db.refresh(db_advisor)
    return db_advisor


@router.get("", response_model=list[AdvisorRead])
def get_advisors(db: Session = Depends(get_db)):
    return db.query(Advisor).all()


@router.get("/{advisor_id}/dashboard", response_model=AdvisorDashboard)
def get_advisor_dashboard(advisor_id: int, db: Session = Depends(get_db)):
    advisor = db.query(Advisor).filter(Advisor.id == advisor_id).first()
    
    if not advisor:
        raise HTTPException(status_code=404, detail="Advisor not found")
    
    clients_summary = []
    
    for client in advisor.clients:
        total_assets = Decimal("0")
        
        for bank in client.banks:
            for account in bank.accounts:
                total_assets += account.balance
                
                for position in account.positions:
                    total_assets += position.market_value
        
        clients_summary.append({
            "id": client.id,
            "first_name": client.first_name,
            "last_name": client.last_name,
            "total_assets": total_assets
        })
    
    return {
        "id": advisor.id,
        "first_name": advisor.first_name,
        "last_name": advisor.last_name,
        "email": advisor.email,
        "clients": clients_summary
    }