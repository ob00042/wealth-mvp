from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientLogin, ClientCredentials
from app.utils.auth import (get_current_user, get_current_advisor, get_current_client,
                            visible_clients, require_client_access, hash_password,
                            verify_password, create_access_token)
from app.api.dashboard import build_dashboard
from app.schemas.dashboard import ClientDashboard

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/login")
def login_client(credentials: ClientLogin, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.email == credentials.email.lower()).first()
    if not client or not client.hashed_password or not verify_password(credentials.password, client.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {
        "access_token": create_access_token({"sub": str(client.id), "role": "client"}),
        "token_type": "bearer", "role": "client", "client_id": client.id,
    }


@router.get("/me/dashboard", response_model=ClientDashboard)
def my_dashboard(client=Depends(get_current_client)):
    return build_dashboard(client)


@router.put("/{client_id}/credentials", response_model=ClientRead)
def set_credentials(client_id: int, credentials: ClientCredentials,
                    advisor=Depends(get_current_advisor), db: Session = Depends(get_db)):
    client = require_client_access(db, advisor, client_id)
    if len(credentials.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=422, detail="Password must be at most 72 bytes")
    client.email = credentials.email.lower()
    client.hashed_password = hash_password(credentials.password)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email is already in use")
    db.refresh(client)
    return client


@router.post("", response_model=ClientRead)
def create_client(client: ClientCreate, advisor=Depends(get_current_advisor), db: Session = Depends(get_db)):
    if client.advisor_id != advisor.id:
        raise HTTPException(status_code=403, detail="Cannot create clients for another advisor")
    db_client = Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.get("", response_model=list[ClientRead])
def get_clients(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return visible_clients(db, user).all()
