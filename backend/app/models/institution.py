from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True)

    name = Column(
        String,
        nullable=False
    )

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    client = relationship(
        "Client",
        back_populates="institutions"
    )

    accounts = relationship(
        "Account",
        back_populates="institution"
    )