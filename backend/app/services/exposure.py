"""Single-level look-through of current positions using dated provider compositions."""
from collections import defaultdict
from decimal import Decimal
from itertools import combinations
from app.providers.market_data import ProductNotFound, SnapshotNotFound, ProviderUnavailable

ZERO = Decimal('0')


def analyse_exposure(client, currency, cutoff, provider):
    positions = [(a, p) for b in client.banks for a in b.accounts for p in a.positions if p.currency == currency]
    cash = sum((a.balance for b in client.banks for a in b.accounts if a.currency == currency), ZERO)
    if cash < 0 or any(p.market_value < 0 for _, p in positions):
        raise ValueError('Exposure analysis currently supports non-negative cash and long positions only.')
    investments = sum((p.market_value for _, p in positions), ZERO)
    total = cash + investments
    securities, sources, unresolved = {}, [], []
    fund_values = defaultdict(lambda: defaultdict(lambda: ZERO))
    fund_names, snapshots = {}, {}
    stale_value = ZERO
    for account, position in positions:
        value = position.market_value
        if value == 0:
            continue
        product_id = position.provider_product_id
        issue = None
        snapshot = None
        if not product_id:
            issue = 'No provider mapping'
        else:
            if product_id not in snapshots:
                try:
                    snapshots[product_id] = provider.get_holdings(product_id, cutoff)
                except ProductNotFound:
                    snapshots[product_id] = 'Product not found'
                except SnapshotNotFound:
                    snapshots[product_id] = 'No snapshot on or before cutoff'
                except ProviderUnavailable:
                    snapshots[product_id] = 'Provider unavailable'
            result = snapshots[product_id]
            if isinstance(result, str):
                issue = result
            else:
                snapshot = result
        source = {'position_id': position.id, 'account': account.name, 'position': position.security_name,
                  'product_id': product_id, 'value': value, 'snapshot_date': None,
                  'stale': False, 'coverage': ZERO, 'status': issue or 'Available'}
        sources.append(source)
        if issue:
            unresolved.append({'position': position.security_name, 'account': account.name, 'value': value, 'reason': issue})
            continue
        # Classify direct listings only when the provider explicitly describes a stock
        # and supplies exactly one fully weighted identity. Never match by name/ticker.
        direct = snapshot.product.product_type == 'Stock'
        if direct and (len(snapshot.holdings) != 1 or snapshot.coverage != 1):
            source['status'] = 'Invalid direct-security mapping'
            unresolved.append({'position': position.security_name, 'account': account.name, 'value': value, 'reason': source['status']})
            continue
        source.update(snapshot_date=snapshot.as_of_date, stale=snapshot.stale, coverage=snapshot.coverage)
        if snapshot.stale:
            stale_value += value
        for h in snapshot.holdings:
            amount = value * h.weight
            row = securities.setdefault(h.security_id, {'security_id': h.security_id, 'name': h.name,
                'asset_class': h.asset_class, 'sector': h.sector, 'country': h.country,
                'direct_value': ZERO, 'indirect_value': ZERO, 'contributions': []})
            # Conflicting classifications must not silently be attributed to the first fund.
            for field in ('asset_class', 'sector', 'country'):
                if row[field] != getattr(h, field):
                    row[field] = 'Unknown / conflicting metadata'
            row['direct_value' if direct else 'indirect_value'] += amount
            row['contributions'].append({'position': position.security_name, 'account': account.name,
                'position_id': position.id, 'kind': 'Direct' if direct else 'Via fund',
                'value': amount, 'weight': h.weight, 'snapshot_date': snapshot.as_of_date,
                'stale': snapshot.stale})
            if not direct:
                fund_values[product_id][h.security_id] += amount
                fund_names[product_id] = snapshot.product.name
        if snapshot.unreported_weight:
            unresolved.append({'position': position.security_name, 'account': account.name,
                'value': value * snapshot.unreported_weight, 'reason': 'Undisclosed fund holdings'})
    rows = list(securities.values())
    for row in rows:
        row['total_value'] = row['direct_value'] + row['indirect_value']
        row['portfolio_weight'] = row['total_value'] / total if total else ZERO
    rows.sort(key=lambda row: (-row['total_value'], row['security_id']))
    known = sum((row['total_value'] for row in rows), ZERO)
    unknown = sum((row['value'] for row in unresolved), ZERO)
    allocations = {}
    for field in ('asset_class', 'sector', 'country'):
        buckets = defaultdict(lambda: ZERO)
        for row in rows:
            buckets[row[field] or 'Unknown classification'] += row['total_value']
        if cash:
            buckets['Cash' if field == 'asset_class' else 'Cash / not applicable'] += cash
        if unknown:
            buckets['Unresolved investments'] += unknown
        allocations[field] = [{'name': name, 'value': value, 'portfolio_weight': value / total if total else ZERO}
                              for name, value in sorted(buckets.items(), key=lambda item: (-item[1], item[0]))]
    overlaps = []
    for left, right in combinations(sorted(fund_values), 2):
        shared = sorted(set(fund_values[left]) & set(fund_values[right]))
        if shared:
            overlaps.append({'left': fund_names[left], 'right': fund_names[right],
                'securities': [securities[key]['name'] for key in shared],
                'shared_value': sum((fund_values[left][key] + fund_values[right][key] for key in shared), ZERO)})
    assert cash + known + unknown == total
    return {'currency': currency, 'composition_cutoff': cutoff, 'total_assets': total,
            'cash': cash, 'investment_value': investments, 'resolved_value': known,
            'unresolved_value': unknown, 'investment_coverage': known / investments if investments else None,
            'stale_position_value': stale_value, 'securities': rows, 'allocations': allocations,
            'overlaps': overlaps, 'unresolved': unresolved, 'sources': sources}
