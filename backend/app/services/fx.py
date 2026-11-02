"""Current portfolio translation using explicitly synthetic, dated FX quotes."""
from datetime import date
from decimal import Decimal

from app.providers.fx import FxProvider, FxSnapshotNotFound, get_fx_provider


def translate_portfolio(client, target, cutoff, provider: FxProvider | None = None):
    provider = provider if provider is not None else get_fx_provider()
    currencies = provider.supported_currencies()
    if target not in currencies:
        raise ValueError('Unsupported reporting currency')
    try:
        snapshot = provider.get_rates(cutoff)
    except FxSnapshotNotFound:
        snapshot = None
    day = snapshot.as_of_date if snapshot else None
    quotes = snapshot.rates if snapshot else {}
    rows = []
    for bank in client.banks:
        for account in bank.accounts:
            rows.append(dict(institution=bank.name, account=account.name, name=account.name,
                             kind='Cash', currency=account.currency, original_value=account.balance))
            for position in account.positions:
                rows.append(dict(institution=bank.name, account=account.name, name=position.security_name,
                                 kind='Investment', currency=position.currency, original_value=position.market_value))
    totals = {'Cash': Decimal(0), 'Investment': Decimal(0)}
    buckets = {}
    missing = set()
    for row in rows:
        code = row['currency']
        value = Decimal(row['original_value'])
        rate = Decimal(1) if code == target else quotes[target] / quotes[code] if code in quotes and target in quotes else None
        converted = value * rate if rate is not None else Decimal(0) if value == 0 else None
        row.update(rate=rate, converted_value=converted)
        if converted is None:
            missing.add(code)
        else:
            totals[row['kind']] += converted
        bucket = buckets.setdefault(code, dict(currency=code, original_value=Decimal(0), converted_value=Decimal(0), rate=rate))
        bucket['original_value'] += value
        if converted is None:
            bucket['converted_value'] = None
        elif bucket['converted_value'] is not None:
            bucket['converted_value'] += converted
    subtotal = sum(totals.values(), Decimal(0))
    return dict(reporting_currency=target, requested_as_of=cutoff, rate_date=day,
                source=snapshot.source if snapshot else provider.source,
                synthetic=snapshot.synthetic if snapshot else provider.synthetic,
                stale=snapshot.stale if snapshot else False,
                stale_after_days=snapshot.stale_after_days if snapshot else provider.stale_after_days,
                supported_currencies=currencies, complete=not missing,
                missing_currencies=sorted(missing), total_assets=subtotal if not missing else None,
                converted_subtotal=subtotal, cash=totals['Cash'], investments=totals['Investment'],
                currency_breakdown=sorted(buckets.values(), key=lambda r: r['currency']), rows=rows)
