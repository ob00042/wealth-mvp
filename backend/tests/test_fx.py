from datetime import date
from decimal import Decimal as D
from types import SimpleNamespace as NS
import unittest
import test_client_access
from app.services.fx import translate_portfolio


def portfolio(code='EUR', cash='100', investments=(('USD', '112'), ('GBP', '84'))):
    return NS(banks=[NS(name='Bank', accounts=[NS(name='Account', currency=code, balance=D(cash), positions=[NS(security_name=c, currency=c, market_value=D(v)) for c, v in investments])])])


class FxCalculationTests(unittest.TestCase):
    def test_cross_currency_reconciliation(self):
        result = translate_portfolio(portfolio(), 'EUR', date(2026, 9, 22))
        self.assertEqual(result['total_assets'], D('300'))
        self.assertEqual(result['cash'], D('100'))
        self.assertEqual(result['investments'], D('200'))
        for field in ('rows', 'currency_breakdown'):
            self.assertEqual(sum(r['converted_value'] for r in result[field]), result['total_assets'])
        usd = translate_portfolio(portfolio(), 'USD', date(2026, 9, 22))
        self.assertAlmostEqual(usd['total_assets'], D('336'))
        self.assertEqual(usd['rows'][1]['rate'], D(1))

    def test_dates(self):
        old = translate_portfolio(portfolio(), 'USD', date(2026, 7, 1))
        self.assertEqual(old['rate_date'], date(2026, 6, 30))
        self.assertEqual(old['cash'], D('110'))
        self.assertFalse(old['stale'])
        self.assertTrue(translate_portfolio(portfolio(), 'EUR', date(2026, 12, 1))['stale'])

    def test_missing_rates(self):
        result = translate_portfolio(portfolio(investments=(('CAD', '500'),)), 'EUR', date(2026, 9, 22))
        self.assertFalse(result['complete'])
        self.assertIsNone(result['total_assets'])
        self.assertEqual(result['converted_subtotal'], D('100'))
        self.assertEqual(result['missing_currencies'], ['CAD'])
        self.assertIsNone(result['rows'][1]['converted_value'])
        self.assertEqual(result['rows'][1]['original_value'], D('500'))
        before = translate_portfolio(portfolio(), 'EUR', date(2020, 1, 1))
        self.assertIsNone(before['rate_date'])
        self.assertEqual(before['converted_subtotal'], D('100'))
        self.assertFalse(before['complete'])

    def test_identity_empty_zero_and_negative(self):
        result = translate_portfolio(portfolio(cash='-10', investments=()), 'EUR', date(2020, 1, 1))
        self.assertTrue(result['complete'])
        self.assertEqual(result['total_assets'], D('-10'))
        result = translate_portfolio(portfolio(cash='0', code='CAD', investments=()), 'EUR', date(2020, 1, 1))
        self.assertTrue(result['complete'])
        self.assertEqual(result['total_assets'], 0)
        self.assertEqual(translate_portfolio(NS(banks=[]), 'JPY', date(2026, 9, 22))['total_assets'], 0)
        with self.assertRaises(ValueError):
            translate_portfolio(portfolio(), 'CAD', date(2026, 9, 22))


class FxApiTests(test_client_access.ClientAccessTests):
    def test_access_validation(self):
        url = '/clients/me/reporting-valuation?currency=USD&as_of=2026-09-22'
        self.assertIn(self.api.get(url).status_code, (401, 403))
        response = self.api.get(url, headers=self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['complete'])
        self.assertEqual(D(response.json()['total_assets']), D('168'))
        self.assertEqual(self.api.get('/clients/1/reporting-valuation', headers=self.headers('advisor')).status_code, 200)
        for role in ('advisor', 'client'):
            self.assertEqual(self.api.get('/clients/2/reporting-valuation', headers=self.headers(role)).status_code, 404)
        self.assertEqual(self.api.get(url, headers=self.headers('advisor')).status_code, 403)
        for query in ('currency=eur', 'currency=CAD', 'currency=EUR&as_of=2999-01-01'):
            self.assertEqual(self.api.get('/clients/me/reporting-valuation?' + query, headers=self.headers()).status_code, 422)


class FxProviderTests(unittest.TestCase):
    def test_snapshot_selection_and_validation(self):
        from app.providers.fx import FictionalFxProvider, FxSnapshotNotFound
        from app.schemas.fx import FxSnapshot
        provider = FictionalFxProvider()
        rates = provider.get_rates(date(2026, 9, 21))
        self.assertEqual(rates.as_of_date, date(2026, 6, 30))
        self.assertTrue(rates.stale)
        self.assertEqual(rates.rates['USD'], D('1.10'))
        with self.assertRaises(FxSnapshotNotFound):
            provider.get_rates(date(2020, 1, 1))
        for rates in ({'EUR': '2'}, {'EUR': '1', 'USD': '0'}, {'EUR': '1', 'USD': '-1'}, {'EUR': '1', 'USD': 'NaN'}):
            with self.assertRaises(ValueError):
                FxSnapshot(as_of_date=date(2026, 9, 22), base_currency='EUR', rates=rates)

    def test_missing_target_quote_remains_unresolved(self):
        from app.providers.fx import FictionalFxProvider
        provider = FictionalFxProvider()
        del provider.snapshots[-1].rates['USD']
        result = translate_portfolio(portfolio(), 'USD', date(2026, 9, 22), provider)
        self.assertFalse(result['complete'])
        self.assertEqual(result['converted_subtotal'], D('112'))
        self.assertEqual(result['missing_currencies'], ['EUR', 'GBP'])


class FxProviderApiTests(test_client_access.ClientAccessTests):
    def test_rates_auth_dates_and_provenance(self):
        url = '/market-data/fx/rates?as_of=2026-09-22'
        self.assertIn(self.api.get(url).status_code, (401, 403))
        for role in ('advisor', 'client'):
            result = self.api.get(url, headers=self.headers(role))
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['rates']['USD'], '1.12')
            self.assertEqual(result.json()['base_currency'], 'EUR')
            self.assertTrue(result.json()['synthetic'])
        self.assertEqual(self.api.get('/market-data/fx/rates?as_of=2020-01-01', headers=self.headers()).status_code, 404)
        self.assertEqual(self.api.get('/market-data/fx/rates?as_of=2999-01-01', headers=self.headers()).status_code, 422)

    def test_both_endpoints_use_injected_provider_and_outage(self):
        from app.main import app
        from app.providers.fx import FictionalFxProvider, get_fx_provider, FxProviderUnavailable
        provider = FictionalFxProvider()
        provider.snapshots[-1].rates['USD'] = D('2')
        app.dependency_overrides[get_fx_provider] = lambda: provider
        rates = self.api.get('/market-data/fx/rates?as_of=2026-09-22', headers=self.headers())
        self.assertEqual(D(rates.json()['rates']['USD']), D('2'))
        result = self.api.get('/clients/me/reporting-valuation?currency=USD&as_of=2026-09-22', headers=self.headers())
        self.assertEqual(D(result.json()['total_assets']), D('300'))
        class Unavailable(FictionalFxProvider):
            def get_rates(self, as_of):
                raise FxProviderUnavailable()
        app.dependency_overrides[get_fx_provider] = lambda: Unavailable()
        for url in ('/market-data/fx/rates', '/clients/me/reporting-valuation'):
            result = self.api.get(url, headers=self.headers())
            self.assertEqual(result.status_code, 503)
            self.assertEqual(result.json()['detail'], 'FX provider is unavailable')
