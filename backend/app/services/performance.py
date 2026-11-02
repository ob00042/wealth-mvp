"""Non-annualised Modified Dietz on end-of-day snapshots and cash flows."""
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

ZERO = Decimal(0)


def period_result(points, transactions, expected, account_scope=False):
    start, end = points[0]['date'], points[-1]['date']
    rows = [tx for tx in transactions if start < tx.trade_date <= end]
    issues = []
    if start == end:
        issues.append('At least two distinct valuation dates are required.')
    if any(set(point['accounts']) != expected for point in points):
        issues.append('Some valuation dates have incomplete account coverage.')
    # Each account must reconcile separately; opposite errors cannot cancel out.
    for previous, current in zip(points, points[1:]):
        for account in expected & set(previous['accounts']) & set(current['accounts']):
            movement = sum((tx.amount for tx in rows if tx.account_id == account and previous['date'] < tx.trade_date <= current['date']), ZERO)
            if previous['accounts'][account].cash_balance + movement != current['accounts'][account].cash_balance:
                issues.append('Cash does not reconcile with recorded transactions between snapshots.')
    if any(tx.settlement_date is None or tx.settlement_date != tx.trade_date for tx in rows):
        issues.append('Unknown or delayed settlement requires cash-timing reconciliation before calculating performance.')
    if not account_scope and any(tx.type == 'transfer' for tx in rows):
        issues.append('Transfers are not linked as internal or external; portfolio performance is unavailable for this period.')
    if any(row.cash_balance < 0 or row.investment_value < 0 for point in points for row in point['accounts'].values()):
        issues.append('Negative balances require a leverage-aware performance method.')
    external = [tx for tx in rows if tx.type in ('deposit', 'withdrawal') or (account_scope and tx.type == 'transfer')]
    deposits = sum((tx.amount for tx in external if tx.amount > 0), ZERO)
    withdrawals = -sum((tx.amount for tx in external if tx.amount < 0), ZERO)
    flow = deposits - withdrawals
    opening = sum((row.cash_balance + row.investment_value for row in points[0]['accounts'].values()), ZERO)
    closing = sum((row.cash_balance + row.investment_value for row in points[-1]['accounts'].values()), ZERO)
    days = (end - start).days
    weighted = sum((tx.amount * Decimal((end - tx.trade_date).days) / Decimal(days) for tx in external), ZERO) if days else ZERO
    denominator = opening + weighted
    gain = closing - opening - flow
    if denominator <= 0:
        issues.append('Return is undefined because weighted invested capital is zero or negative.')
    valid_gain = not [issue for issue in issues if not issue.startswith('Return is undefined')]
    return dict(start_date=start, end_date=end, opening_value=opening, closing_value=closing,
                contributions=deposits, withdrawals=withdrawals, net_flows=flow,
                investment_gain=gain if valid_gain else None,
                weighted_capital=denominator, return_rate=gain / denominator if not issues else None,
                income=sum((tx.amount for tx in rows if tx.type in ('dividend', 'interest')), ZERO),
                fees=-sum((tx.amount for tx in rows if tx.type == 'fee'), ZERO),
                issues=sorted(set(issues)), valid=not issues)


def calculate_performance(valuations, transactions, expected, currency, start_date=None, end_date=None, frequency='monthly', account_scope=False):
    grouped = {}
    for row in valuations:
        if row.currency != currency or row.account_id not in expected:
            continue
        if (start_date and row.as_of_date < start_date) or (end_date and row.as_of_date > end_date):
            continue
        grouped.setdefault(row.as_of_date, {})[row.account_id] = row
    points = [dict(date=day, accounts=rows) for day, rows in sorted(grouped.items())]
    transactions = [tx for tx in transactions if tx.currency == currency and tx.account_id in expected]
    result = dict(currency=currency, method='Modified Dietz', frequency=frequency,
                  requested_start=start_date, requested_end=end_date, expected_account_count=len(expected),
                  sources=sorted({row.source for point in points for row in point['accounts'].values()}),
                  summary=None, periods=[], issues=[])
    if len(points) < 2:
        result['issues'] = ['At least two valuation snapshots in the selected range are required.']
        return result
    result['summary'] = period_result(points, transactions, expected, account_scope)
    # Group observed intervals by calendar bucket. Missing month/quarter boundaries
    # are never interpolated; actual dates are shown and marked partial.
    def key(day):
        return (day.year, day.month if frequency == 'monthly' else (day.month-1)//3+1 if frequency == 'quarterly' else 1)
    groups = []
    for i in range(1, len(points)):
        bucket = key(points[i]['date'])
        if not groups or groups[-1][0] != bucket:
            groups.append((bucket, [points[i-1], points[i]]))
        else:
            groups[-1][1].append(points[i])
    for (year, number), subset in groups:
        month = number if frequency == 'monthly' else (number-1)*3+1 if frequency == 'quarterly' else 1
        last_month = month if frequency == 'monthly' else month+2 if frequency == 'quarterly' else 12
        calendar_start = date(year, month, 1) - timedelta(days=1)
        calendar_end = date(year, last_month, monthrange(year, last_month)[1])
        label = f'{year}-{month:02d}' if frequency == 'monthly' else f'{year} Q{number}' if frequency == 'quarterly' else str(year)
        period = period_result(subset, transactions, expected, account_scope)
        period.update(label=label, partial_period=subset[0]['date'] != calendar_start or subset[-1]['date'] != calendar_end)
        result['periods'].append(period)
    return result
