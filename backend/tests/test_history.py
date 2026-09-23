from datetime import date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
import test_client_access
from app.models import Account, AccountValuation, Client, Transaction
from seed_history import seed_client_history, SNAPSHOTS, AS_OF, SOURCE


class HistoryTests(test_client_access.ClientAccessTests):
    def add_transaction(self, account=1, day=date(2026, 1, 10), kind='deposit', amount=25, key='one', currency='EUR'):
        tx = Transaction(account_id=account, trade_date=day, settlement_date=day,
                         type=kind, amount=amount, currency=currency, description='Test deposit',
                         source='test', external_id=key)
        self.db.add(tx)
        self.db.commit()
        return tx

    def add_valuation(self, account, day, cash, invested, currency='EUR'):
        self.db.add(AccountValuation(account_id=account, as_of_date=day, currency=currency,
                                     cash_balance=cash, investment_value=invested, source='test'))
        self.db.commit()

    def test_history_access_and_pagination(self):
        for i in range(5):
            self.add_transaction(key=str(i))
        self.add_transaction(account=2)
        self.add_valuation(1, date(2026, 1, 31), 125, 50)
        for resource in ('transactions', 'valuations'):
            self.assertIn(self.api.get(f'/clients/me/{resource}').status_code, (401, 403))
            self.assertEqual(self.api.get(f'/clients/2/{resource}', headers=self.headers()).status_code, 404)
            self.assertEqual(self.api.get(f'/clients/2/{resource}', headers=self.headers('advisor')).status_code, 404)
            self.assertEqual(self.api.get(f'/clients/me/{resource}', headers=self.headers('advisor')).status_code, 403)
            self.assertEqual(self.api.get(f'/clients/1/{resource}?account_id=2', headers=self.headers()).status_code, 404)
            own = self.api.get(f'/clients/me/{resource}', headers=self.headers())
            advisor = self.api.get(f'/clients/1/{resource}', headers=self.headers('advisor'))
            self.assertEqual(own.status_code, 200)
            self.assertEqual(own.json(), advisor.json())
            self.assertEqual(self.api.get(f'/clients/me/{resource}?start_date=2026-02-01&end_date=2026-01-01', headers=self.headers()).status_code, 422)
        first = self.api.get('/clients/me/transactions?limit=2', headers=self.headers()).json()
        second = self.api.get('/clients/me/transactions?limit=2&offset=2', headers=self.headers()).json()
        self.assertEqual(first['total'], 5)
        self.assertFalse({row['id'] for row in first['items']} & {row['id'] for row in second['items']})
        self.assertTrue(all(row['account_id'] == 1 for row in first['items'] + second['items']))
        self.assertEqual(self.api.get('/clients/me/transactions?limit=101', headers=self.headers()).status_code, 422)
        self.assertEqual(self.api.get('/clients/me/transactions?type=unknown', headers=self.headers()).status_code, 422)

    def test_filters_are_inclusive_and_currency_safe(self):
        self.add_transaction()
        self.add_transaction(kind='fee', amount=-2, key='fee')
        self.add_transaction(currency='USD', key='usd')
        self.add_valuation(1, date(2026, 1, 10), '100.01', '20.02')
        self.add_valuation(1, date(2026, 1, 10), '200', '50', 'USD')
        activity = self.api.get('/clients/me/transactions?currency=EUR&type=fee&start_date=2026-01-10&end_date=2026-01-10', headers=self.headers()).json()
        self.assertEqual(activity['total'], 1)
        self.assertEqual(Decimal(activity['items'][0]['amount']), Decimal('-2'))
        points = self.api.get('/clients/me/valuations', headers=self.headers()).json()['items']
        self.assertEqual(len(points), 2)
        self.assertEqual(Decimal(points[0]['total_value']), Decimal('120.03'))
        self.assertEqual(Decimal(points[1]['total_value']), Decimal('250'))
        self.assertEqual(self.api.get('/clients/me/valuations?currency=GBP', headers=self.headers()).json()['items'], [])
        self.assertEqual(self.api.get('/clients/me/transactions?start_date=2027-01-01', headers=self.headers()).json()['total'], 0)

    def test_partial_coverage_is_not_presented_as_full_portfolio(self):
        self.db.add(Account(id=3, bank_id=1, name='Missing history', currency='EUR', account_type='cash', balance=20))
        self.db.commit()
        self.add_valuation(1, date(2026, 1, 10), 100, 50)
        point = self.api.get('/clients/me/valuations', headers=self.headers()).json()['items'][0]
        self.assertFalse(point['complete'])
        self.assertEqual(point['expected_account_count'], 2)
        selected = self.api.get('/clients/me/valuations?account_id=1', headers=self.headers()).json()['items'][0]
        self.assertTrue(selected['complete'])

    def test_seed_is_repeatable_and_reconciles_every_snapshot(self):
        client = self.db.get(Client, 1)
        created = seed_client_history(self.db, client)
        self.db.commit()
        self.assertEqual(created, (53, 13))
        self.assertEqual(seed_client_history(self.db, client), (0, 0))
        ledger = self.db.query(Transaction).filter_by(account_id=1, source=SOURCE).all()
        snapshots = self.db.query(AccountValuation).filter_by(account_id=1).order_by(AccountValuation.as_of_date).all()
        self.assertEqual([point.as_of_date for point in snapshots], SNAPSHOTS)
        for previous, current in zip(snapshots, snapshots[1:]):
            cash_flow = sum((tx.amount for tx in ledger if previous.as_of_date < tx.trade_date <= current.as_of_date), Decimal(0))
            self.assertEqual(previous.cash_balance + cash_flow, current.cash_balance)
        account = self.db.get(Account, 1)
        self.assertEqual(snapshots[-1].as_of_date, AS_OF)
        self.assertEqual(snapshots[-1].cash_balance, account.balance)
        self.assertEqual(snapshots[-1].investment_value, sum((p.market_value for p in account.positions), Decimal(0)))
        self.assertEqual(self.db.query(Transaction).filter_by(account_id=2).count(), 0)

    def test_database_prevents_duplicate_imports_and_invalid_cash_sign(self):
        self.add_transaction()
        with self.assertRaises(IntegrityError):
            self.add_transaction()
        self.db.rollback()
        with self.assertRaises(IntegrityError):
            self.add_transaction(kind='withdrawal', amount=20, key='invalid')
        self.db.rollback()
        self.add_valuation(1, date(2026, 1, 10), 100, 50)
        with self.assertRaises(IntegrityError):
            self.add_valuation(1, date(2026, 1, 10), 200, 50)
        self.db.rollback()
