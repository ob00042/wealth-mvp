"""Add a reproducible demo ledger and valuations without changing current balances.

Run after alembic upgrade head. Re-runs skip existing source IDs and snapshot keys.
This fixture is explicitly synthetic, not a bank integration or a transaction engine.
"""
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from app.db.database import SessionLocal
from app.models import Advisor, Client, Transaction, AccountValuation

SOURCE = 'demo-history-v1'
AS_OF = date(2026, 9, 22)
OPENING = date(2025, 9, 30)
MONTHS = [(2025, m) for m in (10, 11, 12)] + [(2026, m) for m in range(1, 10)]
SNAPSHOTS = [OPENING] + [min(date(y, m, monthrange(y, m)[1]), AS_OF) for y, m in MONTHS]
# Synthetic market prices fluctuate; the last snapshot exactly matches current holdings.
PRICE_FACTORS = [Decimal(x) for x in ('0.88', '0.90', '0.89', '0.93', '0.94', '0.91', '0.95', '0.97', '0.96', '0.98', '1.01', '0.99', '1.00')]


def cents(value):
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def seed_client_history(db, client):
    added_transactions = added_valuations = 0
    accounts = sorted((a for b in client.banks for a in b.accounts), key=lambda a: a.id)
    for index, account in enumerate(accounts):
        if any(p.currency != account.currency for p in account.positions):
            raise ValueError('Demo fixture expects all account holdings in the account currency')
        ledger = []

        def add(day, kind, amount, description, key, security=None, quantity=None, price=None):
            ledger.append(dict(account_id=account.id, trade_date=day, settlement_date=day,
                               type=kind, description=description, amount=cents(amount),
                               currency=account.currency, source=SOURCE, external_id=key,
                               security_name=security, quantity=quantity, unit_price=price))

        for month_index, (year, month) in enumerate(MONTHS):
            key = f'{year}-{month:02d}'
            add(date(year, month, 3), 'deposit', 500 + index * 150, 'Scheduled contribution', f'{key}-deposit')
            add(date(year, month, 12), 'withdrawal', -(180 + index * 30), 'Personal distribution', f'{key}-withdrawal')
            add(date(year, month, 18), 'interest', Decimal(8 + index * 3) + Decimal(month_index) / 10, 'Account interest', f'{key}-interest')
            add(date(year, month, 20), 'fee', -15, 'Monthly account service fee', f'{key}-fee')
        for position_index, position in enumerate(sorted(account.positions, key=lambda p: p.id)):
            if position.quantity <= 0:
                raise ValueError('Demo history expects positive position quantities')
            # Start with 95% of the current units, buy 10%, then sell 5%.
            buy_units = (position.quantity * Decimal('.10')).quantize(Decimal('.000001'))
            sell_units = (position.quantity * Decimal('.05')).quantize(Decimal('.000001'))
            price = position.market_value / position.quantity
            buy_price = (price * Decimal('.94')).quantize(Decimal('.000001'))
            sell_price = (price * Decimal('.98')).quantize(Decimal('.000001'))
            add(date(2026, 1, 15), 'buy', -buy_units * buy_price, f'Purchase of {position.security_name}', f'position-{position_index}-buy', position.security_name, buy_units, buy_price)
            add(date(2026, 6, 15), 'sell', sell_units * sell_price, f'Sale of {position.security_name}', f'position-{position_index}-sell', position.security_name, -sell_units, sell_price)
            for month in (3, 6, 9):
                add(date(2026, month, 16), 'dividend', position.quantity * Decimal('.45'), f'Investment income from {position.security_name}', f'position-{position_index}-income-{month}', position.security_name)

        existing_ids = {key for (key,) in db.query(Transaction.external_id).filter_by(account_id=account.id, source=SOURCE)}
        for row in ledger:
            if row['external_id'] not in existing_ids:
                db.add(Transaction(**row))
                added_transactions += 1
        opening_cash = account.balance - sum((row['amount'] for row in ledger), Decimal(0))
        for day, factor in zip(SNAPSHOTS, PRICE_FACTORS):
            if db.query(AccountValuation.id).filter_by(account_id=account.id, as_of_date=day, currency=account.currency).first():
                continue
            cash = opening_cash + sum((row['amount'] for row in ledger if row['trade_date'] <= day), Decimal(0))
            investment_value = Decimal(0)
            for position in account.positions:
                remaining_units = sum((row['quantity'] for row in ledger if row['security_name'] == position.security_name and row['quantity'] is not None and row['trade_date'] > day), Decimal(0))
                units = position.quantity - remaining_units
                investment_value += cents(position.market_value * (units / position.quantity) * factor)
            db.add(AccountValuation(account_id=account.id, as_of_date=day, currency=account.currency,
                                    cash_balance=cash, investment_value=investment_value, source=SOURCE))
            added_valuations += 1
    db.flush()
    return added_transactions, added_valuations


def seed_demo_history(db):
    advisor = db.query(Advisor).filter_by(email='john.smith@example.com').one()
    result = []
    for first, last in [('Jane', 'Doe'), ('Mister', 'Agapitos')]:
        client = db.query(Client).filter_by(advisor_id=advisor.id, first_name=first, last_name=last).one()
        result.append((f'{first} {last}', *seed_client_history(db, client)))
    return result


if __name__ == '__main__':
    with SessionLocal() as db:
        results = seed_demo_history(db)
        db.commit()
        for name, transactions, valuations in results:
            print(f'{name}: added {transactions} transactions and {valuations} account valuations ({OPENING} to {AS_OF}).')
