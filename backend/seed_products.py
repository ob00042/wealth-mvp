"""Add fictional demo product positions; never replace existing client holdings."""
from decimal import Decimal
from app.db.database import SessionLocal
from app.models import Advisor, Client, Account, Position
from app.providers.market_data import get_market_data_provider
from seed_history import seed_client_history

DEMO_ACCOUNT = 'Fictional Product Demo Portfolio'
PROFILES = [
    ('Jane', 'Doe', 'USD', [('demo-atlas-usd', '200', '20000'), ('demo-nova-usd', '100', '10000'), ('demo-cedar-usd', '30', '3000')]),
    ('Mister', 'Agapitos', 'EUR', [('demo-atlas-eur', '300', '30000'), ('demo-horizon-eur', '200', '20000'), ('demo-cedar-eur', '50', '5000')]),
]


def seed_demo_products(db):
    catalog = {p.id: p for p in get_market_data_provider().list_products()}
    advisor = db.query(Advisor).filter_by(email='john.smith@example.com').one()
    results = []
    for first, last, currency, positions in PROFILES:
        client = db.query(Client).filter_by(advisor_id=advisor.id, first_name=first, last_name=last).one()
        banks = sorted(client.banks, key=lambda bank: bank.id)
        if not banks:
            raise ValueError(f'{first} {last} has no bank for the demo account')
        bank = banks[0]
        account = db.query(Account).filter_by(bank_id=bank.id, name=DEMO_ACCOUNT).one_or_none()
        if account is None:
            account = Account(bank=bank, name=DEMO_ACCOUNT, currency=currency,
                              account_type='Investment', balance=Decimal('15000'))
            db.add(account)
            db.flush()
        if account.currency != currency:
            raise ValueError('Existing demo account has a different currency')
        added = 0
        for product_id, quantity, value in positions:
            existing = db.query(Position).filter_by(account_id=account.id, provider_product_id=product_id).one_or_none()
            if existing is None:
                product = catalog[product_id]
                db.add(Position(account=account, provider_product_id=product_id,
                                security_name=product.name, ticker=product.ticker,
                                asset_type=product.product_type, quantity=Decimal(quantity),
                                market_value=Decimal(value), currency=currency))
                added += 1
        db.flush()
        # History for new accounts reconciles to their current cash and position values.
        # The history seeder skips every existing transaction and snapshot key.
        transactions, valuations = seed_client_history(db, client)
        results.append(f'{first} {last}: added {added} positions, {transactions} transactions, {valuations} account snapshots')
    return results


if __name__ == '__main__':
    with SessionLocal() as db:
        results = seed_demo_products(db)
        db.commit()
        print('\n'.join(results))
