from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.client import Client
from app.schemas.client import (
    ClientCreate,
    ClientRead
)


router = APIRouter(
    prefix="/clients",
    tags=["clients"]
)


@router.post(
    "",
    response_model=ClientRead
)
def create_client(
    client: ClientCreate,
    db: Session = Depends(get_db)
):

    db_client = Client(
        first_name=client.first_name,
        last_name=client.last_name,
        advisor_id=client.advisor_id
    )

    db.add(db_client)
    db.commit()
    db.refresh(db_client)

    return db_client


@router.get(
    "",
    response_model=list[ClientRead]
)
def get_clients(
    db: Session = Depends(get_db)
):

    return db.query(Client).all()