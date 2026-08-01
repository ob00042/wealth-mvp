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

    bank_id = Column(
        Integer,
        ForeignKey("banks.id"),
        nullable=False
    )

    bank = relationship(
        "Bank",
        back_populates="accounts"
    )

    positions = relationship(
        "Position",
        back_populates="account",
        cascade="all, delete"
    )