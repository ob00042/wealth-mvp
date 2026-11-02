from datetime import date
from decimal import Decimal as D
from types import SimpleNamespace as NS
import unittest
import test_client_access
from app.main import app
from app.models import Position
from app.providers.market_data import FictionalMarketDataProvider, ProviderUnavailable, get_market_data_provider
from app.services.exposure import analyse_exposure


def portfolio(items, cash='15000', currency='USD'):
    positions = [NS(id=i, provider_product_id=product, security_name=product or 'Unmapped', market_value=D(value), currency=code)
                 for i, (product, value, code) in enumerate(items, 1)]
    return NS(banks=[NS(accounts=[NS(name='Test account', balance=D(cash), currency=currency, positions=positions)])])


class ExposureCalculationTests(unittest.TestCase):
    def setUp(self):
        self.provider = FictionalMarketDataProvider()
        self.client = portfolio([('demo-atlas-usd', '20000', 'USD'), ('demo-nova-usd', '10000', 'USD'), ('demo-cedar-usd', '3000', 'USD'), (None, '21500', 'USD')])

    def analyse(self, client=None, currency='USD', cutoff=date(2026, 11, 1), provider=None):
        return analyse_exposure(client or self.client, currency, cutoff, provider or self.provider)

    def test_combined_exposure_reconciliation_and_overlap(self):
        result = self.analyse()
        cedar = next(s for s in result['securities'] if s['security_id'] == 'demo-cedar')
        self.assertEqual((cedar['direct_value'], cedar['indirect_value'], cedar['total_value']), (D('3000'), D('9500'), D('12500')))
        self.assertEqual(len(cedar['contributions']), 3)
        self.assertEqual(result['total_assets'], D('69500'))
        self.assertEqual(result['resolved_value'], D('33000'))
        self.assertEqual(result['unresolved_value'], D('21500'))
        for rows in result['allocations'].values():
            self.assertEqual(sum(r['value'] for r in rows), result['total_assets'])
        self.assertEqual(len(result['overlaps']), 1)
        self.assertEqual(result['overlaps'][0]['shared_value'], D('23000'))

    def test_partial_eur_coverage(self):
        client = portfolio([('demo-atlas-eur', '30000', 'EUR'), ('demo-horizon-eur', '20000', 'EUR'), ('demo-cedar-eur', '5000', 'EUR')], currency='EUR')
        result = self.analyse(client, 'EUR')
        self.assertEqual(result['unresolved_value'], D('2000'))
        self.assertEqual(result['resolved_value'], D('53000'))
        self.assertEqual(next(s['total_value'] for s in result['securities'] if s['security_id'] == 'demo-cedar'), D('14500'))
        self.assertEqual(result['total_assets'], D('70000'))

    def test_currency_isolation_and_zero(self):
        client = portfolio([('demo-atlas-usd', '20000', 'USD'), ('demo-cedar-eur', '5000', 'EUR')])
        result = self.analyse(client, 'EUR')
        self.assertEqual(result['total_assets'], D('5000'))
        self.assertEqual(result['cash'], 0)
        self.assertIsNone(self.analyse(client, 'GBP')['investment_coverage'])
        self.assertEqual(self.analyse(portfolio([], cash='0'))['securities'], [])

    def test_dates_stale_and_missing_snapshots(self):
        old = self.analyse(cutoff=date(2026, 8, 1))
        self.assertEqual(next(s['total_value'] for s in old['securities'] if s['security_id'] == 'demo-cedar'), D('14000'))
        self.assertEqual(old['total_assets'], self.analyse()['total_assets'])
        self.assertEqual(self.analyse(cutoff=date(2026, 12, 1))['stale_position_value'], D('33000'))
        missing = self.analyse(cutoff=date(2020, 1, 1))
        self.assertEqual(missing['resolved_value'], 0)
        self.assertEqual(missing['unresolved_value'], missing['investment_value'])

    def test_provider_failures_preserve_assets(self):
        class Unavailable:
            def get_holdings(self, *args):
                raise ProviderUnavailable()
        result = self.analyse(provider=Unavailable())
        self.assertEqual(result['unresolved_value'], D('54500'))
        self.assertEqual(result['resolved_value'], 0)
        self.assertTrue(any(s['status'] == 'Provider unavailable' for s in result['sources']))
        self.assertEqual(self.analyse(portfolio([('missing', '10', 'USD')]))['unresolved'][0]['reason'], 'Product not found')

    def test_duplicate_products_and_conflicting_metadata(self):
        result = self.analyse(portfolio([('demo-atlas-usd', '20000', 'USD'), ('demo-atlas-usd', '10000', 'USD')]))
        self.assertEqual(next(s['total_value'] for s in result['securities'] if s['security_id'] == 'demo-cedar'), D('7500'))
        self.assertEqual(result['overlaps'], [])
        for snapshot in self.provider.snapshots:
            if snapshot.product_id == 'demo-nova-usd':
                snapshot.holdings[0].sector = 'Conflicting sector'
        self.assertEqual(next(s['sector'] for s in self.analyse()['securities'] if s['security_id'] == 'demo-cedar'), 'Unknown / conflicting metadata')

    def test_negative_values_rejected(self):
        for client in (portfolio([(None, '-10', 'USD')]), portfolio([], cash='-1')):
            with self.assertRaises(ValueError):
                self.analyse(client)


class ExposureApiTests(test_client_access.ClientAccessTests):
    def test_access_validation_and_response(self):
        self.db.add(Position(account_id=1, security_name='Atlas', provider_product_id='demo-atlas-eur', quantity=1, market_value=20000, currency='EUR'))
        self.db.commit()
        url = '/clients/me/exposure?currency=EUR&as_of=2026-09-22'
        self.assertIn(self.api.get(url).status_code, (401, 403))
        result = self.api.get(url, headers=self.headers())
        self.assertEqual(result.status_code, 200)
        self.assertEqual(D(result.json()['resolved_value']), D('20000'))
        self.assertEqual(D(result.json()['unresolved_value']), D('50'))
        self.assertEqual(self.api.get('/clients/1/exposure?currency=EUR', headers=self.headers('advisor')).status_code, 200)
        for role in ('advisor', 'client'):
            self.assertEqual(self.api.get('/clients/2/exposure?currency=EUR', headers=self.headers(role)).status_code, 404)
        self.assertEqual(self.api.get(url, headers=self.headers('advisor')).status_code, 403)
        for query in ('currency=eur', 'currency=EUR&as_of=2999-01-01', ''):
            self.assertEqual(self.api.get('/clients/me/exposure?' + query, headers=self.headers()).status_code, 422)

    def test_provider_outage_partial_response(self):
        self.db.query(Position).filter_by(id=1).update({'provider_product_id': 'demo-cedar-eur'})
        self.db.commit()
        class Unavailable:
            def get_holdings(self, *args):
                raise ProviderUnavailable()
        app.dependency_overrides[get_market_data_provider] = lambda: Unavailable()
        result = self.api.get('/clients/me/exposure?currency=EUR', headers=self.headers())
        self.assertEqual(result.status_code, 200)
        self.assertEqual(D(result.json()['unresolved_value']), D('50'))
        self.assertEqual(result.json()['sources'][0]['status'], 'Provider unavailable')
