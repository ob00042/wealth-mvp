import unittest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError
import test_client_access
from app.models import Advisor, Client, Account, Position, AccountValuation, Transaction
from app.providers.market_data import (FictionalMarketDataProvider, ProductNotFound,
    SnapshotNotFound, ProviderUnavailable, get_market_data_provider)
from app.schemas.market_data import HoldingsSnapshot
from app.main import app
from seed_products import seed_demo_products, DEMO_ACCOUNT


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = FictionalMarketDataProvider()

    def test_dated_snapshots_and_canonical_overlap(self):
        old = self.provider.get_holdings('demo-atlas-usd', date(2026, 8, 1))
        latest = self.provider.get_holdings('demo-atlas-usd', date(2026, 11, 1))
        self.assertEqual(old.as_of_date, date(2026, 6, 30))
        self.assertEqual(latest.as_of_date, date(2026, 9, 22))
        self.assertEqual(old.holdings[0].weight, Decimal('.30'))
        self.assertEqual(latest.holdings[0].weight, Decimal('.25'))
        nova = self.provider.get_holdings('demo-nova-usd', date(2026, 11, 1))
        direct = self.provider.get_holdings('demo-cedar-usd', date(2026, 11, 1))
        self.assertEqual(latest.holdings[0].security_id, nova.holdings[0].security_id)
        self.assertEqual(latest.holdings[0].security_id, direct.holdings[0].security_id)
        self.assertEqual(latest.coverage, Decimal(1))
        self.assertTrue(latest.product.synthetic)

    def test_missing_stale_and_partial_data(self):
        with self.assertRaises(ProductNotFound):
            self.provider.get_holdings('unknown', date(2026, 11, 1))
        with self.assertRaises(SnapshotNotFound):
            self.provider.get_holdings('demo-atlas-usd', date(2025, 1, 1))
        self.assertTrue(self.provider.get_holdings('demo-atlas-usd', date(2026, 12, 1)).stale)
        partial = self.provider.get_holdings('demo-horizon-eur', date(2026, 11, 1))
        self.assertEqual(partial.coverage, Decimal('.90'))
        self.assertEqual(partial.unreported_weight, Decimal('.10'))

    def test_invalid_fixture_weights_are_rejected(self):
        snapshot = self.provider.snapshots[0].model_dump()
        snapshot['holdings'][0]['weight'] = Decimal('1')
        with self.assertRaises(ValidationError):
            HoldingsSnapshot.model_validate(snapshot)


class MarketDataApiTests(test_client_access.ClientAccessTests):
    def test_api_requires_login_and_has_clear_failures(self):
        self.assertIn(self.api.get('/market-data/products').status_code, (401, 403))
        for role in ('advisor', 'client'):
            self.assertEqual(self.api.get('/market-data/products', headers=self.headers(role)).status_code, 200)
            response = self.api.get('/market-data/products/demo-atlas-usd/holdings?as_of=2026-08-01', headers=self.headers(role))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['as_of_date'], '2026-06-30')
        self.assertEqual(self.api.get('/market-data/products/missing/holdings', headers=self.headers()).status_code, 404)
        self.assertEqual(self.api.get('/market-data/products/demo-atlas-usd/holdings?as_of=2020-01-01', headers=self.headers()).status_code, 404)
        self.assertEqual(self.api.get('/market-data/products/demo-atlas-usd/holdings?as_of=2999-01-01', headers=self.headers()).status_code, 422)
        class Unavailable:
            def get_holdings(self, *args):
                raise ProviderUnavailable()
        app.dependency_overrides[get_market_data_provider] = lambda: Unavailable()
        self.assertEqual(self.api.get('/market-data/products/demo-atlas-usd/holdings', headers=self.headers()).status_code, 503)

    def test_seed_is_additive_repeatable_and_matches_history(self):
        advisor = self.db.get(Advisor, 1)
        advisor.email = 'john.smith@example.com'
        jane, mister = self.db.get(Client, 1), self.db.get(Client, 2)
        jane.first_name, jane.last_name = 'Jane', 'Doe'
        mister.first_name, mister.last_name, mister.advisor_id = 'Mister', 'Agapitos', 1
        self.db.commit()
        before = [(p.id, p.market_value) for p in self.db.query(Position).all()]
        seed_demo_products(self.db)
        self.db.commit()
        counts = [self.db.query(model).count() for model in (Account, Position, Transaction, AccountValuation)]
        seed_demo_products(self.db)
        self.db.commit()
        self.assertEqual(counts, [self.db.query(model).count() for model in (Account, Position, Transaction, AccountValuation)])
        for position_id, value in before:
            self.assertEqual(self.db.get(Position, position_id).market_value, value)
        demo_accounts = self.db.query(Account).filter_by(name=DEMO_ACCOUNT).all()
        self.assertEqual(len(demo_accounts), 2)
        for account in demo_accounts:
            self.assertEqual(len(account.positions), 3)
            self.assertTrue(all(p.provider_product_id for p in account.positions))
            latest = self.db.query(AccountValuation).filter_by(account_id=account.id).order_by(AccountValuation.as_of_date.desc()).first()
            self.assertEqual(latest.cash_balance, account.balance)
            self.assertEqual(latest.investment_value, sum(p.market_value for p in account.positions))
        response = self.api.get('/clients/me/dashboard', headers=self.headers())
        linked = [p for b in response.json()['banks'] for a in b['accounts'] for p in a['positions'] if p['provider_product_id']]
        self.assertEqual(len(linked), 3)
