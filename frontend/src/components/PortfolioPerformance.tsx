'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { money } from '@/lib/format';

type Period = {
  start_date: string; end_date: string; opening_value: string; closing_value: string;
  contributions: string; withdrawals: string; net_flows: string; investment_gain: string | null;
  return_rate: string | null; income: string; fees: string; issues: string[];
  label?: string; partial_period?: boolean;
};
type Report = { currency: string; sources: string[]; summary: Period | null; periods: Period[]; issues: string[] };
type Account = { id: number; name: string; bankName: string };
const percent = (value: string | null) => value === null ? 'Unavailable' : `${(Number(value) * 100).toFixed(2)}%`;

function ReturnChart({ periods }: { periods: Period[] }) {
  const [selection, setSelection] = useState('');
  const selected = periods.find(p => p.end_date === selection) ?? periods.at(-1);
  if (!selected) return null;
  const maximum = Math.max(...periods.map(p => Math.abs(Number(p.return_rate ?? 0))), .01);
  const step = 760 / periods.length;
  return <div className="performance-chart">
    <label>Inspect period<select value={selected.end_date} onChange={e => setSelection(e.target.value)}>{periods.map(p => <option key={p.end_date} value={p.end_date}>{p.label}{p.partial_period ? ' (partial period)' : ''}</option>)}</select></label>
    <p>{selected.start_date} → {selected.end_date} · <strong>{percent(selected.return_rate)}</strong></p>
    <svg viewBox="0 0 840 260" role="img" aria-label="Modified Dietz returns by period. Each bar is a separate period, not a cumulative return. Exact dates and values are in the table below.">
      <line x1="40" x2="800" y1="120" y2="120" stroke="#9aa6ad" />
      <text x="4" y="124" fontSize="11" fill="#65737c">0%</text>
      {periods.map((p, index) => {
        const amount = Number(p.return_rate ?? 0);
        const height = Math.abs(amount) / maximum * 90;
        const x = 40 + index * step + step * .15;
        return <g key={p.end_date} onMouseEnter={() => setSelection(p.end_date)}>
          {p.return_rate === null ? <text x={x + step * .35} y="110" textAnchor="middle" fontSize="14" fill="#8b6e48">—</text> : <rect x={x} y={amount >= 0 ? 120 - height : 120} width={step * .7} height={Math.max(height, 1)} fill={amount < 0 ? '#a46d54' : '#3d5b71'} opacity={selected.end_date === p.end_date ? 1 : .65} />}
          <title>{p.label}: {percent(p.return_rate)}; {p.start_date} to {p.end_date}</title>
          <text transform={`translate(${x + step * .35},230) rotate(-35)`} textAnchor="end" fontSize="10" fill="#65737c">{p.label}</text>
        </g>;
      })}
    </svg>
  </div>;
}

export default function PortfolioPerformance({ clientId, currency, accounts }: { clientId?: number; currency: string; accounts: Account[] }) {
  const [accountId, setAccountId] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [frequency, setFrequency] = useState('monthly');
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ key: string; data?: Report; error?: string } | null>(null);
  const router = useRouter();
  const key = JSON.stringify([clientId, currency, accountId, start, end, frequency, retry]);
  const invalid = Boolean(start && end && start > end);
  useEffect(() => {
    if (invalid) return;
    const controller = new AbortController();
    async function load() {
      try {
        const query = new URLSearchParams({ currency, frequency });
        if (accountId) query.set('account_id', accountId);
        if (start) query.set('start_date', start);
        if (end) query.set('end_date', end);
        const response = await fetch(`http://localhost:8000/clients/${clientId ?? 'me'}/performance?${query}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }, signal: controller.signal,
        });
        if (response.status === 401 || response.status === 403) { router.replace('/login'); return; }
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to load performance');
        if (!controller.signal.aborted) setResult({ key, data });
      } catch (error) {
        if (!controller.signal.aborted) setResult({ key, error: error instanceof Error ? error.message : 'Unable to load performance' });
      }
    }
    load();
    return () => controller.abort();
  }, [clientId, currency, accountId, start, end, frequency, retry, key, invalid, router]);
  const current = result?.key === key ? result : null;
  const data = current?.data;
  const summary = data?.summary;
  const amount = (value: string | null) => value === null ? 'Unavailable' : money(value, currency);
  return <section className="history-section performance-section" aria-label="Portfolio performance">
    <div className="history-title"><div><p className="eyebrow">UNDERSTAND YOUR RETURNS</p><h2>Performance</h2></div><span className="tag">{currency} · MODIFIED DIETZ</span></div>
    <div className="history-filters">
      <label>Performance account<select value={accountId} onChange={e => setAccountId(e.target.value)}><option value="">All accounts</option>{accounts.map(a => <option key={a.id} value={a.id}>{a.bankName} · {a.name}</option>)}</select></label>
      <label>Performance from<input type="date" value={start} onInput={e => setStart(e.currentTarget.value)} /></label>
      <label>Performance to<input type="date" value={end} onInput={e => setEnd(e.currentTarget.value)} /></label>
      <label>Period grouping<select value={frequency} onChange={e => setFrequency(e.target.value)}><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="yearly">Yearly</option></select></label>
      <button className="history-reset" onClick={() => { setStart(''); setEnd(''); setAccountId(''); }}>All recorded history</button>
    </div>
    {invalid ? <p className="error-message" role="alert">From date must be on or before To date.</p> : current?.error ? <p role="alert" className="error-message">{current.error} <button onClick={() => setRetry(n => n + 1)}>Retry</button></p> : !data ? <p role="status" className="history-loading">Calculating performance…</p> : <section className="panel">
      <div className="panel-heading"><div><h3>{start || end ? 'Selected range' : 'Since first recorded valuation'}</h3><p>{summary ? `${summary.start_date} → ${summary.end_date} · actual valuation dates used` : 'No calculable period'}</p></div>{data.sources.includes('demo-history-v1') && <span className="tag">SYNTHETIC DEMO HISTORY</span>}</div>
      {[...data.issues, ...(summary?.issues ?? [])].map(issue => <p className="coverage-note" key={issue}>{issue}</p>)}
      {summary && <>
        <div className="history-summary"><div><span>Investment gain / loss</span><strong>{amount(summary.investment_gain)}</strong></div><div><span>Modified Dietz return · not annualised</span><strong>{percent(summary.return_rate)}</strong></div><div><span>Net external cash flow</span><strong>{amount(summary.net_flows)}</strong></div></div>
        <p className="panel-footnote">Opening {amount(summary.opening_value)} + contributions {amount(summary.contributions)} − withdrawals {amount(summary.withdrawals)} + investment gain/loss {amount(summary.investment_gain)} = closing {amount(summary.closing_value)}. {summary.investment_gain === null && 'This bridge cannot be verified until the issues above are resolved.'}</p>
        <p className="panel-footnote">Recorded income: {amount(summary.income)} · recorded fees: {amount(summary.fees)}. Both are already reflected in gain/loss; do not add or subtract them again.</p>
        <ReturnChart periods={data.periods} />
        <div className="table-scroll"><table className="data-table"><thead><tr><th>Period / actual dates</th><th className="numeric">Opening</th><th className="numeric">Net flows</th><th className="numeric">Gain / loss</th><th className="numeric">Closing</th><th className="numeric">Return</th></tr></thead><tbody>{data.periods.map(period => <tr key={period.end_date}><td>{period.label}{period.partial_period && ' · Partial period'}<small className="cell-subtext">{period.start_date} → {period.end_date}</small>{period.issues.map(issue => <small className="cell-subtext" key={issue}>{issue}</small>)}</td><td className="numeric">{amount(period.opening_value)}</td><td className="numeric">{amount(period.net_flows)}</td><td className="numeric">{amount(period.investment_gain)}</td><td className="numeric">{amount(period.closing_value)}</td><td className="numeric">{percent(period.return_rate)}</td></tr>)}</tbody></table></div>
      </>}
      <details className="reporting-details"><summary>How performance is calculated</summary><p className="panel-footnote">Modified Dietz estimates returns using cash-flow timing: gain ÷ (opening value + time-weighted external flows). Flows occur at end of day; opening-date flows are already in the opening valuation, and closing-date flows have zero weight. Results are calculated directly for each displayed period and are not annualised or summed.</p><p className="panel-footnote">Deposits and withdrawals are external flows. Purchases and sales stay inside the portfolio; dividends and interest contribute to returns, and recorded fees reduce them. For a selected account, transfers cross that account’s boundary and count as flows. For the whole portfolio, unclassified transfers block returns until their internal/external status is known.</p><p className="panel-footnote">Only recorded snapshots within the requested dates are used. Missing boundary dates are not estimated. Cash reconciliation is required at every observed interval; it cannot prove that every source transaction was imported. Account opening/closing dates are not yet modelled, so coverage is conservative. Original currencies only; no FX conversion or benchmark comparison.</p></details>
    </section>}
  </section>;
}
