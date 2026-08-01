from decimal import Decimal
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.advisor import Advisor
from app.schemas.advisor import AdvisorCreate, AdvisorRead, AdvisorLogin
from app.schemas.advisor_dashboard import AdvisorDashboard
from app.utils.auth import hash_password, authenticate_advisor, create_access_token, get_current_advisor, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/advisors", tags=["Advisors"])


@router.post("", response_model=AdvisorRead)
def create_advisor(advisor: AdvisorCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(advisor.password)
    db_advisor = Advisor(
        first_name=advisor.first_name,
        last_name=advisor.last_name,
        email=advisor.email,
        hashed_password=hashed_password
    )
    db.add(db_advisor)
    db.commit()
    db.refresh(db_advisor)
    return db_advisor


@router.post("/login")
def login_advisor(advisor_credentials: AdvisorLogin, db: Session = Depends(get_db)):
    advisor = authenticate_advisor(advisor_credentials.email, advisor_credentials.password, db)
    if not advisor:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(advisor.id)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "advisor_id": advisor.id
    }


@router.get("", response_model=list[AdvisorRead])
def get_advisors(db: Session = Depends(get_db)):
    return db.query(Advisor).all()


@router.get("/dashboard", response_model=AdvisorDashboard)
def get_advisor_dashboard(
    current_advisor: Advisor = Depends(get_current_advisor),
    db: Session = Depends(get_db)
):
    # Refresh the advisor to get latest client data
    advisor = db.query(Advisor).filter(Advisor.id == current_advisor.id).first()
    
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