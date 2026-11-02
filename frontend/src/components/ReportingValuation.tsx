'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { money } from '@/lib/format';

type CurrencyValue = { currency: string; original_value: string; converted_value: string | null; rate: string | null };
type Row = CurrencyValue & { institution: string; account: string; name: string; kind: string };
type Valuation = {
  reporting_currency: string; rate_date: string | null; source: string; stale: boolean;
  complete: boolean; missing_currencies: string[]; total_assets: string | null;
  converted_subtotal: string; cash: string; investments: string;
  currency_breakdown: CurrencyValue[]; rows: Row[];
};
const currencies = ['EUR', 'USD', 'GBP', 'CHF', 'JPY'];

export default function ReportingValuation({ clientId }: { clientId?: number }) {
  const [currency, setCurrency] = useState('EUR');
  const [cutoff, setCutoff] = useState('');
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ key: string; data?: Valuation; error?: string } | null>(null);
  const router = useRouter();
  const key = JSON.stringify([clientId, currency, cutoff, retry]);
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const query = new URLSearchParams({ currency });
        if (cutoff) query.set('as_of', cutoff);
        const response = await fetch(`http://localhost:8000/clients/${clientId ?? 'me'}/reporting-valuation?${query}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }, signal: controller.signal,
        });
        if (response.status === 401 || response.status === 403) {
          router.replace('/login');
          return;
        }
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to convert portfolio');
        if (!controller.signal.aborted) setResult({ key, data });
      } catch (error) {
        if (!controller.signal.aborted) setResult({ key, error: error instanceof Error ? error.message : 'Unable to convert portfolio' });
      }
    }
    load();
    return () => controller.abort();
  }, [clientId, currency, cutoff, retry, key, router]);
  const current = result?.key === key ? result : null;
  const data = current?.data;
  const value = (amount: string | null) => amount === null ? 'Unavailable' : money(Number(amount), currency);
  return <section className="panel reporting-panel" aria-label="Reporting currency valuation">
    <div className="panel-heading"><div><h2>Consolidated portfolio</h2><p>All currencies translated into one reporting currency · Demo FX rates</p></div></div>
    <div className="reporting-controls">
      <label>Reporting currency<select value={currency} onChange={e => setCurrency(e.target.value)}>{currencies.map(code => <option key={code}>{code}</option>)}</select></label>
      <label>FX rates on or before<input type="date" value={cutoff} max={new Date().toISOString().slice(0, 10)} onInput={e => setCutoff(e.currentTarget.value)} /></label>
      {cutoff && <button className="button" onClick={() => setCutoff('')}>Latest available rates</button>}
    </div>
    {!current && <p className="empty-state" role="status">Converting portfolio…</p>}
    {current?.error && <div className="empty-state" role="alert"><p>{current.error}</p><button className="button" onClick={() => setRetry(n => n + 1)}>Retry</button></div>}
    {data && <>
      <div className="reporting-metrics metrics-grid">
        <section className="metric-card primary-metric"><p>{data.complete ? 'Total assets' : 'Converted subtotal'} <span>{currency}</span></p><strong>{value(data.complete ? data.total_assets : data.converted_subtotal)}</strong><small>{data.complete ? 'All accounts and holdings included' : 'Incomplete — missing rates excluded'}</small></section>
        <section className="metric-card"><p>Converted cash</p><strong>{value(data.cash)}</strong><small>{data.complete ? 'Across all accounts' : 'Available rates only'}</small></section>
        <section className="metric-card"><p>Converted investments</p><strong>{value(data.investments)}</strong><small>{data.complete ? 'Across all holdings' : 'Available rates only'}</small></section>
      </div>
      {!data.complete && <p className="currency-note" role="alert">Missing FX rates for {data.missing_currencies.join(', ')}. A complete portfolio total is unavailable; original amounts remain visible below.</p>}
      <p className="currency-note">{data.source} · {data.rate_date ? `Rates dated ${data.rate_date}` : 'No dated FX snapshot available for this cutoff'}. {data.stale ? 'Rates are stale (over 45 days old at the selected cutoff). ' : ''}These are fictional rates, not live market quotes.</p>
      <div className="table-scroll"><table className="data-table"><caption className="reporting-caption">Portfolio by original valuation currency</caption><thead><tr><th>Original currency</th><th className="numeric">Original value</th><th className="numeric">Rate to {currency}</th><th className="numeric">Value in {currency}</th></tr></thead><tbody>{data.currency_breakdown.map(row => <tr key={row.currency}><td>{row.currency}</td><td className="numeric">{money(Number(row.original_value), row.currency)}</td><td className="numeric">{row.rate === null ? 'Missing' : Number(row.rate).toLocaleString('en', { maximumFractionDigits: 8 })}</td><td className="numeric">{value(row.converted_value)}</td></tr>)}</tbody></table></div>
      <details className="reporting-details"><summary>Converted account and holding values</summary><div className="table-scroll"><table className="data-table"><thead><tr><th>Account / holding</th><th>Institution / account</th><th>Type</th><th className="numeric">Original value</th><th className="numeric">Value in {currency}</th></tr></thead><tbody>{data.rows.map((row, i) => <tr key={i}><td>{row.name}</td><td>{row.institution}<br />{row.account}</td><td>{row.kind}</td><td className="numeric">{money(Number(row.original_value), row.currency)}</td><td className="numeric">{value(row.converted_value)}</td></tr>)}</tbody></table></div></details>
      <div className="panel-footnote">Rate means {currency} per 1 unit of original currency. Current portfolio values × selected FX rates; changing the rate date does not reconstruct historical holdings or calculate investment returns. Currency grouping describes valuation currencies, not underlying economic FX risk. Totals are calculated before display rounding.</div>
    </>}
  </section>;
}
