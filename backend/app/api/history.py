from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Account, Bank, Client, Transaction, AccountValuation
from app.schemas.history import TransactionPage, TransactionType, ValuationHistory
from app.utils.auth import get_current_user, require_client_access

router = APIRouter(prefix="/clients", tags=["history"])


def history_client(client_ref: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if client_ref == "me":
        if not isinstance(user, Client):
            raise HTTPException(status_code=403, detail="Client access required")
        return user
    try:
        client_id = int(client_ref)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid client ID")
    return require_client_access(db, user, client_id)


def check_filters(db, client, account_id, start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="Start date must not be after end date")
    if account_id is not None:
        account = db.query(Account).join(Bank).filter(Account.id == account_id, Bank.client_id == client.id).first()
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")


@router.get("/{client_ref}/transactions", response_model=TransactionPage)
def transactions(
    client=Depends(history_client), db: Session = Depends(get_db),
    start_date: date | None = None, end_date: date | None = None,
    account_id: int | None = Query(None, gt=0),
    currency: str | None = Query(None, pattern="^[A-Z]{3}$"),
    type: TransactionType | None = None,
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
):
    check_filters(db, client, account_id, start_date, end_date)
    query = db.query(Transaction, Account.name, Bank.name).join(Account, Transaction.account_id == Account.id).join(Bank).filter(Bank.client_id == client.id)
    if start_date:
        query = query.filter(Transaction.trade_date >= start_date)
    if end_date:
        query = query.filter(Transaction.trade_date <= end_date)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if currency:
        query = query.filter(Transaction.currency == currency)
    if type:
        query = query.filter(Transaction.type == type)
    total = query.count()
    rows = query.order_by(Transaction.trade_date.desc(), Transaction.id.desc()).offset(offset).limit(limit).all()
    items = [{**{column.name: getattr(tx, column.name) for column in Transaction.__table__.columns}, 'account_name': account, 'bank_name': bank} for tx, account, bank in rows]
    return {'items': items, 'total': total, 'limit': limit, 'offset': offset}


@router.get("/{client_ref}/valuations", response_model=ValuationHistory)
def valuations(
    client=Depends(history_client), db: Session = Depends(get_db),
    start_date: date | None = None, end_date: date | None = None,
    account_id: int | None = Query(None, gt=0),
    currency: str | None = Query(None, pattern="^[A-Z]{3}$"),
):
    check_filters(db, client, account_id, start_date, end_date)
    base = db.query(AccountValuation).join(Account).join(Bank).filter(Bank.client_id == client.id)
    if account_id:
        base = base.filter(AccountValuation.account_id == account_id)
    if currency:
        base = base.filter(AccountValuation.currency == currency)
    # Coverage is measured against accounts with any recorded history in that currency,
    # across the entire series, not just the requested window. Never fill missing dates.
    expected = {}
    for account, code in base.with_entities(AccountValuation.account_id, AccountValuation.currency).distinct():
        expected.setdefault(code, set()).add(account)
    current_accounts = db.query(Account).join(Bank).filter(Bank.client_id == client.id)
    if account_id:
        current_accounts = current_accounts.filter(Account.id == account_id)
    for account in current_accounts:
        codes = {account.currency} | {position.currency for position in account.positions}
        for code in codes:
            if not currency or code == currency:
                expected.setdefault(code, set()).add(account.id)
    query = base
    if start_date:
        query = query.filter(AccountValuation.as_of_date >= start_date)
    if end_date:
        query = query.filter(AccountValuation.as_of_date <= end_date)
    points = {}
    for row in query.order_by(AccountValuation.as_of_date, AccountValuation.currency):
        key = (row.as_of_date, row.currency)
        point = points.setdefault(key, {'as_of_date': row.as_of_date, 'currency': row.currency, 'cash_balance': Decimal(0), 'investment_value': Decimal(0), 'account_count': 0, 'sources': set()})
        point['cash_balance'] += row.cash_balance
        point['investment_value'] += row.investment_value
        point['account_count'] += 1
        point['sources'].add(row.source)
    for point in points.values():
        point['total_value'] = point['cash_balance'] + point['investment_value']
        point['expected_account_count'] = len(expected[point['currency']])
        point['complete'] = point['account_count'] == point['expected_account_count']
        point['sources'] = sorted(point['sources'])
    return {'items': list(points.values())}
