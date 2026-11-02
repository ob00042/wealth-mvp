'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { money, palette } from '@/lib/format';

type Contribution = { position: string; account: string; position_id: number; kind: string; value: string; weight: string; snapshot_date: string; stale: boolean };
type Security = { security_id: string; name: string; asset_class: string; sector: string; country: string; direct_value: string; indirect_value: string; total_value: string; portfolio_weight: string; contributions: Contribution[] };
type Allocation = { name: string; value: string; portfolio_weight: string };
type Analysis = {
  currency: string; composition_cutoff: string; total_assets: string; cash: string;
  investment_value: string; resolved_value: string; unresolved_value: string;
  investment_coverage: string | null; stale_position_value: string;
  securities: Security[]; allocations: Record<string, Allocation[]>;
  overlaps: { left: string; right: string; securities: string[]; shared_value: string }[];
  unresolved: { position: string; account: string; value: string; reason: string }[];
  sources: { position_id: number; account: string; position: string; value: string; snapshot_date: string | null; stale: boolean; coverage: string; status: string }[];
};
const percent = (value: string | number) => `${(Number(value) * 100).toFixed(1)}%`;

export default function PortfolioExposure({ clientId, currency }: { clientId?: number; currency: string }) {
  const router = useRouter();
  const [cutoff, setCutoff] = useState('');
  const [retry, setRetry] = useState(0);
  const [search, setSearch] = useState('');
  const [overlapOnly, setOverlapOnly] = useState(false);
  const key = JSON.stringify([clientId, currency, cutoff, retry]);
  const [result, setResult] = useState<{ key: string; data?: Analysis; error?: string } | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const query = new URLSearchParams({ currency });
        if (cutoff) query.set('as_of', cutoff);
        const response = await fetch(`http://localhost:8000/clients/${clientId ?? 'me'}/exposure?${query}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }, signal: controller.signal,
        });
        if (response.status === 401 || response.status === 403) {
          ['token', 'role', 'advisor_id', 'client_id'].forEach(item => localStorage.removeItem(item));
          router.replace('/login');
          return;
        }
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to analyse portfolio exposure');
        if (!controller.signal.aborted) setResult({ key, data });
      } catch (error) {
        if (!controller.signal.aborted) setResult({ key, error: error instanceof Error ? error.message : 'Unable to analyse portfolio exposure' });
      }
    }
    load();
    return () => controller.abort();
  }, [clientId, currency, cutoff, retry, key, router]);
  const data = result?.key === key ? result.data : undefined;
  const error = result?.key === key ? result.error : undefined;
  const securities = data?.securities.filter(s => `${s.name} ${s.sector} ${s.country}`.toLowerCase().includes(search.toLowerCase()) && (!overlapOnly || s.contributions.length > 1)) || [];

  return <section className="history-section" aria-label="Combined portfolio exposure">
    <div className="history-title"><div><p className="eyebrow">THE WHOLE PICTURE</p><h2>Portfolio exposure</h2></div><span className="tag">FICTIONAL PROVIDER · {currency}</span></div>
    <p className="exposure-intro">See shared underlying investments across direct holdings and funds. Values use your current positions in {currency}, with no currency conversion.</p>
    <div className="history-filters"><label>Fund composition on or before<input type="date" value={cutoff} onInput={e => setCutoff(e.currentTarget.value)} /></label><button className="history-reset" onClick={() => setCutoff('')}>Latest available</button><span className="exposure-date-note">Changing this date does not reconstruct a historical portfolio.</span></div>
    {error ? <div className="error-message" role="alert">{error} <button className="text-link" onClick={() => setRetry(retry + 1)}>Try again</button></div> : !data ? <p className="history-loading" role="status">Analysing portfolio exposure…</p> : <>
      <div className="metrics-grid exposure-metrics">
        <div className="metric-card primary-metric"><p>Investment coverage</p><strong>{data.investment_coverage === null ? '—' : percent(data.investment_coverage)}</strong><small>{money(data.resolved_value, currency)} resolved out of {money(data.investment_value, currency)} investments. Excludes cash.</small></div>
        <div className="metric-card"><p>Unresolved investments</p><strong>{money(data.unresolved_value, currency)}</strong><small>Unmapped, unavailable or undisclosed holdings</small></div>
        <div className="metric-card"><p>Largest resolved exposure</p><strong>{data.securities[0] ? percent(data.securities[0].portfolio_weight) : '—'}</strong><small>{data.securities[0]?.name || 'No resolved securities'} · share of total assets</small></div>
        <div className="metric-card"><p>Stale source positions</p><strong>{money(data.stale_position_value, currency)}</strong><small>Position value using stale snapshots; included in analysis</small></div>
      </div>
      {Number(data.stale_position_value) > 0 && <p className="coverage-note">Some compositions are stale relative to {data.composition_cutoff}. Resolved coverage includes these estimates; review source dates below.</p>}
      {Number(data.unresolved_value) > 0 && <p className="coverage-note">Exposure is incomplete. Unresolved investments are retained in all allocation totals, so disclosed holdings are not scaled up to 100%.</p>}
      <div className="exposure-allocation-grid">{[['asset_class', 'Asset classes'], ['sector', 'Sectors'], ['country', 'Countries']].map(([field, title]) => <section className="panel" key={field}><div className="panel-heading"><div><h3>{title}</h3><p>Share of total assets, including cash</p></div></div><div className="bank-bars">{data.allocations[field].map((bucket, i) => <div className="bank-bar" key={bucket.name}><div><span>{bucket.name}</span><strong>{percent(bucket.portfolio_weight)}</strong></div><div className="bar-track"><div style={{ width: `${Number(bucket.portfolio_weight) * 100}%`, background: palette[i % palette.length] }} /></div><small className="exposure-bucket-value">{money(bucket.value, currency)}</small></div>)}{data.allocations[field].length === 0 && <p className="empty-state">No assets in {currency}.</p>}</div></section>)}</div>
      <section className="panel"><div className="panel-heading"><div><h3>Combined security exposure</h3><p>Largest exposures first. Expand a security to trace its direct and indirect sources.</p></div><label className="search-field"><input aria-label="Search exposures" placeholder="Search security, sector, country" value={search} onChange={e => setSearch(e.target.value)} /></label></div>
        <label className="exposure-checkbox"><input type="checkbox" checked={overlapOnly} onChange={e => setOverlapOnly(e.target.checked)} />Only securities held through multiple positions</label>
        <div className="table-scroll"><table className="data-table"><thead><tr><th>Security / sources</th><th className="numeric">Direct</th><th className="numeric">Via funds</th><th className="numeric">Combined</th><th className="numeric">% of total assets</th></tr></thead><tbody>{securities.map(s => <tr key={s.security_id}><td><details className="exposure-sources"><summary>{s.name}<small className="cell-subtext">{s.sector} · {s.country}</small></summary><ul>{s.contributions.map((c, i) => <li key={`${c.position_id}-${i}`}><strong>{c.kind}: {c.position}</strong><span>{c.account} · {money(c.value, currency)} · product weight {percent(c.weight)}</span><span>Composition: {c.snapshot_date}{c.stale ? ' · Stale' : ''}</span></li>)}</ul></details></td><td className="numeric">{money(s.direct_value, currency)}</td><td className="numeric">{money(s.indirect_value, currency)}</td><td className="numeric strong-cell">{money(s.total_value, currency)}</td><td className="numeric">{percent(s.portfolio_weight)}</td></tr>)}</tbody></table></div>
        {securities.length === 0 && <p className="empty-state">No resolved securities match this view.</p>}
        <p className="panel-footnote">Reconciliation: {money(data.resolved_value, currency)} resolved + {money(data.unresolved_value, currency)} unresolved + {money(data.cash, currency)} cash = {money(data.total_assets, currency)} total assets. Underlying holdings replace fund values in the breakdown; they are never added twice. Classification uses provider security IDs, not inferred company-name matches.</p>
      </section>
      <section className="panel exposure-following"><div className="panel-heading"><div><h3>Fund overlap</h3><p>Shared disclosed securities between pairs of funds in this currency.</p></div></div><div className="table-scroll"><table className="data-table"><thead><tr><th>Fund pair</th><th>Shared securities</th><th className="numeric">Exposure in shared securities</th></tr></thead><tbody>{data.overlaps.map((pair, i) => <tr key={i}><td>{pair.left}<small className="cell-subtext">{pair.right}</small></td><td className="exposure-wrap">{pair.securities.join(', ')}</td><td className="numeric">{money(pair.shared_value, currency)}</td></tr>)}</tbody></table></div>{data.overlaps.length === 0 && <p className="empty-state">No overlap found in the available disclosed fund holdings.</p>}<p className="panel-footnote">Each amount sums exposure from both funds to their shared securities. Pair totals can overlap with other pairs and must not be added together. Undisclosed holdings may hide further overlap.</p></section>
      <details className="panel credentials-panel"><summary>Coverage and source details <span>{data.sources.length} positions</span></summary><div className="table-scroll"><table className="data-table"><thead><tr><th>Position</th><th>Composition date</th><th className="numeric">Disclosed</th><th>Status</th></tr></thead><tbody>{data.sources.map(s => <tr key={s.position_id}><td>{s.position}<small className="cell-subtext">{s.account}</small></td><td>{s.snapshot_date || '—'}</td><td className="numeric">{percent(s.coverage)}</td><td>{s.status}{s.stale ? ' · Stale' : ''}</td></tr>)}</tbody></table></div>{data.unresolved.length > 0 && <div className="table-scroll"><table className="data-table"><thead><tr><th>Unresolved position</th><th>Reason</th><th className="numeric">Value</th></tr></thead><tbody>{data.unresolved.map((item, i) => <tr key={i}><td>{item.position}<small className="cell-subtext">{item.account}</small></td><td>{item.reason}</td><td className="numeric">{money(item.value, currency)}</td></tr>)}</tbody></table></div>}</details>
      <p className="panel-footnote">Fictional data, not Bloomberg data. One level of fund holdings is analysed. Security classifications are not issuer-level consolidation or FX risk measures. No trade recommendations are generated.</p>
    </>}
  </section>;
}
