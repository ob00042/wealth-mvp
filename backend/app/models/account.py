from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False
    )

    account_type = Column(
        String,
        nullable=False
    )

    currency = Column(
        String,
        nullable=False
    )

    balance = Column(
        Numeric(18,2),
        nullable=False
    )

    institution_id = Column(
        Integer,
        ForeignKey("institutions.id"),
        nullable=False
    )

    institution = relationship(
        "Institution",
        back_populates="accounts"
    )

    positions = relationship(
        "Position",
        back_populates="account",
        cascade="all, delete"
    )