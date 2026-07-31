from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)

    security_name = Column(
        String,
        nullable=False
    )

    ticker = Column(String, nullable=True)

    asset_type = Column(String, nullable=True)


    quantity = Column(
        Numeric(18, 6),
        nullable=False
    )

    '''
    Some assets need decimals:

    Bitcoin:
    0.153423 BTC

    ETF:
    12.456 shares

    Gold:
    25.75 ounces
    '''

    market_value = Column(
        Numeric(18, 2),
        nullable=False
    )

    currency = Column(
        String,
        nullable=False
    )

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False
    )

    account = relationship(
        "Account",
        back_populates="positions"
    )