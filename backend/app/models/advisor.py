from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Advisor(Base):
    __tablename__ = "advisors"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)


    clients = relationship(
        "Client",
        back_populates="advisor"
    )