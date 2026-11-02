from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.history import history_client, check_filters
from app.db.database import get_db
from app.models import Account, Bank, AccountValuation, Transaction
from app.schemas.performance import PerformanceReport
from app.services.performance import calculate_performance

router = APIRouter(prefix='/clients', tags=['performance'])


@router.get('/{client_ref}/performance', response_model=PerformanceReport)
def performance(client=Depends(history_client), db: Session = Depends(get_db),
                currency: str = Query(..., pattern='^[A-Z]{3}$'),
                start_date: date | None = None, end_date: date | None = None,
                account_id: int | None = Query(None, gt=0),
                frequency: Literal['monthly', 'quarterly', 'yearly'] = 'monthly'):
    check_filters(db, client, account_id, start_date, end_date)
    accounts = db.query(Account).join(Bank).filter(Bank.client_id == client.id)
    if account_id is not None:
        accounts = accounts.filter(Account.id == account_id)
    accounts = accounts.all()
    ids = [account.id for account in accounts]
    values = db.query(AccountValuation).filter(AccountValuation.account_id.in_(ids), AccountValuation.currency == currency).all()
    txs = db.query(Transaction).filter(Transaction.account_id.in_(ids), Transaction.currency == currency).all()
    expected = {row.account_id for row in values} | {tx.account_id for tx in txs}
    expected |= {account.id for account in accounts if currency in {account.currency, *(p.currency for p in account.positions)}}
    return calculate_performance(values, txs, expected, currency, start_date, end_date, frequency, account_id is not None)
