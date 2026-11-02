from datetime import date
from decimal import Decimal as D
from types import SimpleNamespace as NS
import unittest
import test_client_access
from app.models import Account, Client, Transaction, AccountValuation
from app.services.performance import calculate_performance
from seed_history import seed_client_history


def valuation(day, cash, invested='0', account=1, currency='EUR'):
    return NS(as_of_date=date.fromisoformat(day), cash_balance=D(cash), investment_value=D(invested), account_id=account, currency=currency, source='test')


def tx(day, amount, kind='deposit', account=1, currency='EUR'):
    return NS(trade_date=date.fromisoformat(day), settlement_date=date.fromisoformat(day), amount=D(amount), type=kind, account_id=account, currency=currency)


def report(values, txs=(), **kwargs):
    return calculate_performance(values, txs, kwargs.pop('expected', {1}), 'EUR', **kwargs)


class PerformanceCalculationTests(unittest.TestCase):
    def test_timed_flow_and_bridge(self):
        values = [valuation('2026-01-01', '100'), valuation('2026-01-21', '120', '5')]
        result = report(values, [tx('2026-01-11', '20')])['summary']
        self.assertEqual(result['net_flows'], D(20))
        self.assertEqual(result['investment_gain'], D(5))
        self.assertEqual(result['weighted_capital'], D(110))
        self.assertEqual(result['return_rate'], D(5) / D(110))
        self.assertEqual(result['opening_value'] + result['net_flows'] + result['investment_gain'], result['closing_value'])

    def test_opening_excluded_closing_zero_weight_withdrawals(self):
        values = [valuation('2026-01-01', '100'), valuation('2026-01-21', '80', '10')]
        result = report(values, [tx('2026-01-01', '100'), tx('2026-01-21', '-20', 'withdrawal')])['summary']
        self.assertEqual(result['contributions'], 0)
        self.assertEqual(result['withdrawals'], 20)
        self.assertEqual(result['weighted_capital'], 100)
        self.assertEqual(result['return_rate'], D('.1'))

    def test_trades_income_fees_are_not_external(self):
        values = [valuation('2026-01-01', '100'), valuation('2026-01-21', '89', '30')]
        rows = [tx('2026-01-05', '-40', 'buy'), tx('2026-01-06', '20', 'sell'), tx('2026-01-07', '10', 'dividend'), tx('2026-01-08', '-1', 'fee')]
        result = report(values, rows)['summary']
        self.assertEqual(result['net_flows'], 0)
        self.assertEqual(result['income'], 10)
        self.assertEqual(result['fees'], 1)
        self.assertEqual(result['investment_gain'], 19)
        self.assertEqual(result['return_rate'], D('.19'))

    def test_partial_coverage_and_reconciliation_block_returns(self):
        values = [valuation('2026-01-01', '100'), valuation('2026-01-21', '120')]
        self.assertIsNone(report(values)['summary']['return_rate'])
        self.assertIsNone(report(values, [tx('2026-01-11', '20')], expected={1, 2})['summary']['investment_gain'])
        # Missing middle snapshot must not be hidden by complete endpoints.
        values += [valuation('2026-01-01', '100', account=2), valuation('2026-01-31', '120'), valuation('2026-01-31', '100', account=2)]
        self.assertIsNone(report(values, [tx('2026-01-11', '20')], expected={1, 2})['summary']['return_rate'])

    def test_transfers_block_portfolio_but_cross_account_boundary(self):
        values = [valuation('2026-01-01', '100'), valuation('2026-01-21', '80'), valuation('2026-01-01', '100', account=2), valuation('2026-01-21', '120', account=2)]
        rows = [tx('2026-01-11', '-20', 'transfer'), tx('2026-01-11', '20', 'transfer', account=2)]
        self.assertIsNone(report(values, rows, expected={1, 2})['summary']['return_rate'])
        result = report(values, rows, account_scope=True)['summary']
        self.assertEqual(result['net_flows'], -20)
        self.assertEqual(result['return_rate'], 0)

    def test_delayed_settlement_zero_capital_and_currency_isolation(self):
        values = [valuation('2026-01-01', '100'), valuation('2026-01-21', '120')]
        cashflow = tx('2026-01-11', '20'); cashflow.settlement_date = date(2026, 1, 12)
        self.assertIsNone(report(values, [cashflow])['summary']['return_rate'])
        zero = report([valuation('2026-01-01', '0'), valuation('2026-01-21', '0')])['summary']
        self.assertIsNone(zero['return_rate'])
        self.assertEqual(zero['investment_gain'], 0)
        values = [valuation('2026-01-01', '100'), valuation('2026-01-21', '100', '10'), valuation('2026-01-21', '500', currency='USD')]
        self.assertEqual(report(values, [tx('2026-01-11', '500', currency='USD')])['summary']['return_rate'], D('.1'))

    def test_period_grouping_actual_dates_and_insufficient_data(self):
        values = [valuation('2025-12-31', '100'), valuation('2026-01-31', '100', '10'), valuation('2026-02-28', '100', '20'), valuation('2026-03-31', '100', '30'), valuation('2026-04-15', '100', '35')]
        quarterly = report(values, frequency='quarterly')
        self.assertEqual(len(quarterly['periods']), 2)
        self.assertFalse(quarterly['periods'][0]['partial_period'])
        self.assertTrue(quarterly['periods'][1]['partial_period'])
        self.assertEqual(quarterly['periods'][0]['return_rate'], D('.3'))
        self.assertEqual(len(report(values, frequency='yearly')['periods']), 1)
        selected = report(values, start_date=date(2026, 1, 10), end_date=date(2026, 3, 10))
        self.assertEqual(selected['summary']['start_date'], date(2026, 1, 31))
        self.assertEqual(selected['summary']['end_date'], date(2026, 2, 28))
        self.assertIsNone(report(values, start_date=date(2026, 4, 1))['summary'])
        self.assertIsNone(report([])['summary'])


class PerformanceApiTests(test_client_access.ClientAccessTests):
    def test_demo_calculation_and_access(self):
        self.db.get(Account, 1).balance = D('10000')
        seed_client_history(self.db, self.db.get(Client, 1)); self.db.commit()
        url = '/clients/me/performance?currency=EUR'
        result = self.api.get(url, headers=self.headers())
        self.assertEqual(result.status_code, 200)
        data = result.json()
        self.assertEqual(len(data['periods']), 12)
        self.assertTrue(data['summary']['valid'])
        self.assertTrue(all(row['valid'] for row in data['periods']))
        self.assertEqual(data['summary']['start_date'], '2025-09-30')
        self.assertEqual(data['summary']['end_date'], '2026-09-22')
        self.assertEqual(self.api.get('/clients/1/performance?currency=EUR', headers=self.headers('advisor')).json(), data)
        self.assertIn(self.api.get(url).status_code, (401, 403))
        self.assertEqual(self.api.get(url, headers=self.headers('advisor')).status_code, 403)
        for role in ('client', 'advisor'):
            self.assertEqual(self.api.get('/clients/2/performance?currency=EUR', headers=self.headers(role)).status_code, 404)
        self.assertEqual(self.api.get(url+'&account_id=2', headers=self.headers()).status_code, 404)
        for query in ('currency=eur', 'currency=EUR&frequency=daily', 'currency=EUR&start_date=2026-02-01&end_date=2026-01-01'):
            self.assertEqual(self.api.get('/clients/me/performance?'+query, headers=self.headers()).status_code, 422)

    def test_missing_account_history_is_not_ignored(self):
        self.db.get(Account, 1).balance = D('10000')
        seed_client_history(self.db, self.db.get(Client, 1))
        self.db.add(Account(id=3, bank_id=1, name='Unimported', currency='EUR', account_type='cash', balance=20)); self.db.commit()
        result = self.api.get('/clients/me/performance?currency=EUR', headers=self.headers()).json()
        self.assertIsNone(result['summary']['return_rate'])
        selected = self.api.get('/clients/me/performance?currency=EUR&account_id=1', headers=self.headers()).json()
        self.assertTrue(selected['summary']['valid'])
