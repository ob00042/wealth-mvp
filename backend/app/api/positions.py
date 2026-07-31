from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.position import Position
from app.schemas.position import (
    PositionCreate,
    PositionResponse
)


router = APIRouter(
    prefix="/positions",
    tags=["positions"]
)


@router.post(
    "",
    response_model=PositionResponse
)
def create_position(
    position: PositionCreate,
    db: Session = Depends(get_db)
):

    db_position = Position(
        **position.model_dump()
    )

    db.add(db_position)
    db.commit()
    db.refresh(db_position)

    return db_position


@router.get(
    "",
    response_model=list[PositionResponse]
)
def get_positions(
    db: Session = Depends(get_db)
):

    return db.query(Position).all()