from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)

    first_name = Column(String, nullable=False)

    last_name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=True)
    hashed_password = Column(String, nullable=True)

    advisor_id = Column(
        Integer,
        ForeignKey("advisors.id"),
        nullable=False
    )



    advisor = relationship(
        "Advisor",
        back_populates="clients"
    )

    banks = relationship(
        "Bank",
        back_populates="client"
    )