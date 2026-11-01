'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

type LinkedPosition = { provider_product_id?: string | null; security_name: string };
type Holding = { security_id: string; name: string; asset_class: string; sector: string; country: string; currency: string; weight: string };
type ProductData = {
  product: { id: string; name: string; ticker: string; currency: string; manager: string; source: string; synthetic: boolean };
  as_of_date: string; age_days: number; stale: boolean; stale_after_days: number;
  available_dates: string[]; coverage: string; unreported_weight: string; holdings: Holding[];
};
const percent = (value: string | number) => `${(Number(value) * 100).toFixed(1)}%`;

export default function ProductHoldings({ positions }: { positions: LinkedPosition[] }) {
  const products = [...new Map(positions.filter(p => p.provider_product_id).map(p => [p.provider_product_id!, p])).values()];
  const [selected, setSelected] = useState('');
  const [cutoff, setCutoff] = useState('');
  const [retry, setRetry] = useState(0);
  const productId = products.some(p => p.provider_product_id === selected) ? selected : products[0]?.provider_product_id;
  const key = JSON.stringify([productId, cutoff, retry]);
  const [result, setResult] = useState<{ key: string; data?: ProductData; error?: string } | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!productId) return;
    const controller = new AbortController();
    async function load() {
      try {
        const query = cutoff ? `?as_of=${encodeURIComponent(cutoff)}` : '';
        const response = await fetch(`http://localhost:8000/market-data/products/${encodeURIComponent(productId!)}/holdings${query}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }, signal: controller.signal,
        });
        if (response.status === 401 || response.status === 403) {
          ['token', 'role', 'advisor_id', 'client_id'].forEach(item => localStorage.removeItem(item));
          router.replace('/login');
          return;
        }
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to load product holdings');
        if (!controller.signal.aborted) setResult({ key, data });
      } catch (error) {
        if (!controller.signal.aborted) setResult({ key, error: error instanceof Error ? error.message : 'Unable to load product holdings' });
      }
    }
    load();
    return () => controller.abort();
  }, [productId, cutoff, retry, key, router]);

  if (!products.length) return null;
  const data = result?.key === key ? result.data : undefined;
  const error = result?.key === key ? result.error : undefined;
  return <section className="history-section" aria-label="Product holdings from the mock data provider">
    <div className="history-title"><div><p className="eyebrow">INSIDE YOUR INVESTMENTS</p><h2>Product holdings</h2></div><span className="tag">FICTIONAL DATA PROVIDER</span></div>
    <div className="history-filters">
      <label>Investment product<select value={productId || ''} onChange={event => { setSelected(event.target.value); setCutoff(''); }}>
        {products.map(p => <option key={p.provider_product_id} value={p.provider_product_id!}>{p.security_name}</option>)}
      </select></label>
      <label>Holdings on or before<input type="date" value={cutoff} onInput={event => setCutoff(event.currentTarget.value)} /></label>
      <button className="history-reset" onClick={() => setCutoff('')}>Latest available</button>
    </div>
    <section className="panel">
      {error ? <div className="error-message" role="alert">{error} <button className="text-link" onClick={() => setRetry(retry + 1)}>Try again</button></div> : !data ? <p className="history-loading" role="status">Loading product holdings…</p> : <>
        <div className="panel-heading"><div><h3>{data.product.name}</h3><p>{data.product.ticker} · {data.product.currency} · {data.product.manager}</p></div><span className="tag">As of {data.as_of_date}</span></div>
        <div className="product-metadata"><span><strong>{data.holdings.length}</strong> reported holdings</span><span><strong>{percent(data.coverage)}</strong> coverage</span><span>{data.age_days} days between requested date and snapshot</span></div>
        {data.stale && <p className="coverage-note">Stale snapshot: holdings are more than {data.stale_after_days} days older than the requested date.</p>}
        {Number(data.unreported_weight) > 0 && <p className="coverage-note">Partial holdings: {percent(data.unreported_weight)} is unreported. The disclosed weights have not been scaled up.</p>}
        <div className="table-scroll"><table className="data-table"><thead><tr><th>Underlying security</th><th>Asset class</th><th>Sector</th><th>Country</th><th>Security currency</th><th className="numeric">Product weight</th></tr></thead><tbody>
          {data.holdings.map(h => <tr key={h.security_id}><td className="strong-cell">{h.name}<small className="cell-subtext">{h.security_id}</small></td><td>{h.asset_class}</td><td>{h.sector}</td><td>{h.country}</td><td>{h.currency}</td><td className="numeric">{percent(h.weight)}</td></tr>)}
          {Number(data.unreported_weight) > 0 && <tr><td colSpan={5}>Unreported holdings</td><td className="numeric">{percent(data.unreported_weight)}</td></tr>}
        </tbody></table></div>
        <p className="panel-footnote">Entirely fictional product data · Source: {data.product.source}. This is not Bloomberg data. Product weights describe the investment’s composition, not additional portfolio assets. Security currency is not a measure of currency risk.</p>
      </>}
    </section>
  </section>;
}
