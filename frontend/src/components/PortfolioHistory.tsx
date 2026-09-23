'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { money, number } from '@/lib/format';

type AccountOption = { id: number; name: string; bankName: string };
type Valuation = {
  as_of_date: string; currency: string; cash_balance: string; investment_value: string;
  total_value: string; account_count: number; expected_account_count: number;
  complete: boolean; sources: string[];
};
type Transaction = {
  id: number; trade_date: string; settlement_date: string | null; type: string;
  description: string; account_name: string; bank_name: string; amount: string;
  currency: string; security_name: string | null; quantity: string | null;
  unit_price: string | null; source: string; external_id: string;
};
type ActivityPage = { items: Transaction[]; total: number; limit: number; offset: number };
const types = ['deposit', 'withdrawal', 'buy', 'sell', 'dividend', 'interest', 'fee', 'transfer'];
const dateLabel = (date: string) => new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${date}T00:00:00Z`));
const signedMoney = (amount: string | number, currency: string) => `${Number(amount) > 0 ? '+' : ''}${money(amount, currency)}`;
const label = (type: string) => type.charAt(0).toUpperCase() + type.slice(1);

function ValuationChart({ items, currency }: { items: Valuation[]; currency: string }) {
  const [focusedDate, setFocusedDate] = useState('');
  const selected = items.find(item => item.as_of_date === focusedDate) || items.at(-1)!;
  const values = items.map(item => Number(item.total_value));
  const low = Math.min(...values);
  const high = Math.max(...values);
  const padding = Math.max((high - low) * .2, Math.abs(high) * .015, 1);
  const floor = low - padding;
  const ceiling = high + padding;
  const firstTime = Date.parse(items[0].as_of_date);
  const timeRange = Date.parse(items.at(-1)!.as_of_date) - firstTime;
  const x = (point: Valuation) => 85 + (timeRange ? (Date.parse(point.as_of_date) - firstTime) / timeRange : .5) * 785;
  const y = (point: Valuation) => 210 - (Number(point.total_value) - floor) / (ceiling - floor) * 175;
  const compact = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 });
  return <div className="valuation-chart">
    <div className="chart-reading"><div><span>{dateLabel(selected.as_of_date)}{!selected.complete && ' · Partial coverage'}</span><strong>{money(selected.total_value, currency)}</strong></div><div className="chart-key"><i />Portfolio value</div></div>
    <svg viewBox="0 0 900 255" role="img" aria-label={`Portfolio valuations in ${currency}, ${dateLabel(items[0].as_of_date)} to ${dateLabel(items.at(-1)!.as_of_date)}. Exact values are available in the valuation history table below.`}>
      {[0, 1, 2, 3].map(tick => { const height = 35 + tick * 175 / 3; return <g key={tick}><line x1="85" x2="870" y1={height} y2={height} stroke="#e6ece8" /><text x="72" y={height + 4} textAnchor="end" fill="#718277" fontSize="11">{compact.format(ceiling - tick * (ceiling - floor) / 3)}</text></g>; })}
      {items.slice(1).map((point, index) => point.complete && items[index].complete ? <line key={point.as_of_date} x1={x(items[index])} y1={y(items[index])} x2={x(point)} y2={y(point)} stroke="#3d7161" strokeWidth="2.5" /> : null)}
      <line x1={x(selected)} x2={x(selected)} y1="28" y2="214" stroke="#a7bdb0" strokeDasharray="4 4" />
      {items.map(point => <circle key={point.as_of_date} cx={x(point)} cy={y(point)} r={point.as_of_date === selected.as_of_date ? 5 : 3.5} fill={point.complete ? '#3d7161' : '#bc8253'} stroke="white" strokeWidth="2" onMouseEnter={() => setFocusedDate(point.as_of_date)}><title>{dateLabel(point.as_of_date)}: {money(point.total_value, currency)}</title></circle>)}
      <text x="85" y="245" fill="#718277" fontSize="11">{dateLabel(items[0].as_of_date)}</text>
      {items.length > 1 && <text x="870" y="245" textAnchor="end" fill="#718277" fontSize="11">{dateLabel(items.at(-1)!.as_of_date)}</text>}
    </svg>
    <label className="chart-date-selector">Inspect a snapshot<select value={selected.as_of_date} onChange={event => setFocusedDate(event.target.value)}>{items.map(point => <option key={point.as_of_date} value={point.as_of_date}>{dateLabel(point.as_of_date)}</option>)}</select></label>
  </div>;
}

export default function PortfolioHistory({ clientId, currency, accounts }: { clientId?: number; currency: string; accounts: AccountOption[] }) {
  const router = useRouter();
  const [accountId, setAccountId] = useState('');
  const [transactionType, setTransactionType] = useState('');
  const [dates, setDates] = useState({ start: '', end: '' });
  const [offset, setOffset] = useState(0);
  const [retry, setRetry] = useState(0);
  const [state, setState] = useState<{ key: string; valuations: Valuation[]; activity: ActivityPage } | null>(null);
  const [failure, setFailure] = useState<{ key: string; message: string } | null>(null);
  const requestKey = JSON.stringify([clientId, currency, accountId, transactionType, dates.start, dates.end, offset, retry]);
  const invalidDates = Boolean(dates.start && dates.end && dates.start > dates.end);

  useEffect(() => {
    if (invalidDates) return;
    const controller = new AbortController();
    const query = new URLSearchParams({ currency });
    if (accountId) query.set('account_id', accountId);
    if (dates.start) query.set('start_date', dates.start);
    if (dates.end) query.set('end_date', dates.end);
    const activityQuery = new URLSearchParams(query);
    activityQuery.set('limit', '10');
    activityQuery.set('offset', String(offset));
    if (transactionType) activityQuery.set('type', transactionType);
    const base = `http://localhost:8000/clients/${clientId === undefined ? 'me' : clientId}`;
    const load = async () => {
      try {
        const responses = await Promise.all([
          fetch(`${base}/valuations?${query}`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }, signal: controller.signal }),
          fetch(`${base}/transactions?${activityQuery}`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }, signal: controller.signal }),
        ]);
        if (responses.some(response => response.status === 401 || response.status === 403)) {
          ['token', 'role', 'advisor_id', 'client_id'].forEach(key => localStorage.removeItem(key));
          router.replace('/login');
          return;
        }
        for (const response of responses) {
          if (!response.ok) {
            const data = await response.json();
            throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to load portfolio history');
          }
        }
        const [valuations, activity] = await Promise.all(responses.map(response => response.json()));
        if (!controller.signal.aborted) setState({ key: requestKey, valuations: valuations.items, activity });
      } catch (error) {
        if (!controller.signal.aborted) setFailure({ key: requestKey, message: error instanceof Error ? error.message : 'Unable to load portfolio history' });
      }
    };
    load();
    return () => controller.abort();
  }, [clientId, currency, accountId, transactionType, dates.start, dates.end, offset, retry, requestKey, invalidDates, router]);

  const ready = state?.key === requestKey && !invalidDates;
  const error = failure?.key === requestKey ? failure.message : '';
  const points = ready ? state.valuations : [];
  const activity = ready ? state.activity : null;
  const first = points[0];
  const last = points.at(-1);
  const hasDemo = points.some(point => point.sources.includes('demo-history-v1')) || activity?.items.some(item => item.source === 'demo-history-v1');
  const comparable = points.length > 1 && points.every(point => point.complete);

  return <section className="history-section" aria-label="Transactions and historical valuations">
    <div className="history-title"><div><p className="eyebrow">THE STORY BEHIND YOUR PORTFOLIO</p><h2>Activity & history</h2></div>{hasDemo && <span className="tag">SYNTHETIC DEMO HISTORY</span>}</div>
    <div className="history-filters">
      <label>Account<select value={accountId} onChange={event => { setAccountId(event.target.value); setOffset(0); }}><option value="">All accounts</option>{accounts.map(account => <option key={account.id} value={account.id}>{account.bankName} · {account.name}</option>)}</select></label>
      <label>From<input type="date" value={dates.start} onInput={event => { setDates({ ...dates, start: event.currentTarget.value }); setOffset(0); }} /></label>
      <label>To<input type="date" value={dates.end} onInput={event => { setDates({ ...dates, end: event.currentTarget.value }); setOffset(0); }} /></label>
      <button className="history-reset" onClick={() => { setAccountId(''); setDates({ start: '', end: '' }); setTransactionType(''); setOffset(0); }}>Reset filters</button>
      <span className="tag">{currency}</span>
    </div>
    {invalidDates ? <p role="alert" className="error-message">From date must be on or before To date.</p> : error ? <div className="error-message" role="alert">{error} <button className="text-link" onClick={() => setRetry(retry + 1)}>Try again</button></div> : !ready ? <p className="history-loading" role="status">Loading portfolio history…</p> : <>
      <section className="panel history-valuations"><div className="panel-heading"><div><h3>Historical valuations</h3><p>Dated cash and investment values in {currency}.</p></div><span className="tiny-label">{points.length} SNAPSHOTS</span></div>
      {first && last ? <>
        <div className="history-summary"><div><span>Opening snapshot · {dateLabel(first.as_of_date)}</span><strong>{money(first.total_value, currency)}</strong></div><div><span>Closing snapshot · {dateLabel(last.as_of_date)}</span><strong>{money(last.total_value, currency)}</strong></div><div><span>Change in value · includes cash flows</span><strong>{comparable ? signedMoney(Number(last.total_value) - Number(first.total_value), currency) : '—'}</strong></div></div>
        {!points.every(point => point.complete) && <p className="coverage-note">Some dates have partial account coverage. Lines are broken at those dates and change in value is unavailable. See account coverage below.</p>}
        <ValuationChart items={points} currency={currency} />
        <details className="valuation-records"><summary>View valuation history <span>{points.length} dated snapshots</span></summary><div className="table-scroll"><table className="data-table"><thead><tr><th>As of date</th><th className="numeric">Cash balance</th><th className="numeric">Investments</th><th className="numeric">Total value</th><th>Account coverage</th></tr></thead><tbody>{[...points].reverse().map(point => <tr key={point.as_of_date}><td>{dateLabel(point.as_of_date)}</td><td className="numeric">{money(point.cash_balance, currency)}</td><td className="numeric">{money(point.investment_value, currency)}</td><td className="numeric strong-cell">{money(point.total_value, currency)}</td><td>{point.account_count} / {point.expected_account_count}{!point.complete && ' · Partial'}</td></tr>)}</tbody></table></div></details>
      </> : <p className="empty-state">No recorded valuations for these filters.</p>}
      <p className="panel-footnote">Snapshots are end-of-day values. Change in value includes deposits and withdrawals and is not an investment return. Currencies are not converted.</p></section>
      <section className="panel transaction-panel"><div className="panel-heading"><div><h3>Transactions</h3><p>Signed cash movements: positive adds cash, negative reduces cash.</p></div><label className="transaction-type">Transaction type<select value={transactionType} onChange={event => { setTransactionType(event.target.value); setOffset(0); }}><option value="">All types</option>{types.map(type => <option key={type} value={type}>{label(type)}</option>)}</select></label></div>
        <div className="table-scroll"><table className="data-table transaction-table"><thead><tr><th>Trade date</th><th>Activity</th><th>Account</th><th className="numeric">Quantity</th><th className="numeric">Unit price</th><th className="numeric">Cash amount ({currency})</th></tr></thead><tbody>{activity?.items.map(item => <tr key={item.id}><td>{dateLabel(item.trade_date)}<small className="cell-subtext">Settled {item.settlement_date ? dateLabel(item.settlement_date) : '—'}</small></td><td><span className={`transaction-badge type-${item.type}`}>{label(item.type)}</span><span className="transaction-description">{item.description}</span><small className="cell-subtext">{item.source === 'demo-history-v1' ? 'Demo' : item.source} · {item.external_id}</small></td><td>{item.account_name}<small className="cell-subtext">{item.bank_name}</small></td><td className="numeric">{item.quantity === null ? '—' : number(item.quantity)}</td><td className="numeric">{item.unit_price === null ? '—' : money(item.unit_price, item.currency)}</td><td className={`numeric ${Number(item.amount) < 0 ? 'cash-out' : 'cash-in'}`}>{signedMoney(item.amount, item.currency)}</td></tr>)}</tbody></table></div>
        {activity?.items.length === 0 && <p className="empty-state">No transactions match these filters.</p>}
        <div className="history-pagination"><span>{activity?.total ? `${activity.offset + 1}–${Math.min(activity.offset + activity.limit, activity.total)} of ${activity.total} transactions` : '0 transactions'}</span><div><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 10))}>← Previous</button><button disabled={!activity || offset + activity.limit >= activity.total} onClick={() => setOffset(offset + 10)}>Next →</button></div></div>
      </section>
    </>}
  </section>;
}
