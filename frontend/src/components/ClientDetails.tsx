'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import WealthShell, { StateView } from '@/components/WealthShell';
import { money, number, palette } from '@/lib/format';

interface Position {
  security_name: string;
  quantity: number;
  market_value: number;
  currency: string;
}

interface Account {
  id: number;
  name: string;
  account_type: string;
  currency: string;
  balance: number;
  positions: Position[];
}

interface Bank {
  id: number;
  name: string;
  accounts: Account[];
}

interface ClientDashboard {
  id: number;
  first_name: string;
  last_name: string;
  total_assets: number;
  banks: Bank[];
}

export default function ClientDetails({ clientId }: { clientId?: number }) {
  const [dashboard, setDashboard] = useState<ClientDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();
  const [credentialsMessage, setCredentialsMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const [selectedCurrency, setSelectedCurrency] = useState('');
  const [activeTab, setActiveTab] = useState<'accounts' | 'holdings'>('accounts');

  const saveCredentials = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setSaving(true);
    setCredentialsMessage('');
    try {
      const response = await fetch(`http://localhost:8000/clients/${clientId}/credentials`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
        body: JSON.stringify({ email: data.get('email'), password: data.get('password') }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Unable to save credentials');
      }
      form.reset();
      setCredentialsMessage('Client login saved. The client can now sign in using these credentials.');
    } catch (error) {
      setCredentialsMessage(error instanceof Error ? error.message : 'Unable to save credentials');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    const fetchDashboard = async () => {
      const token = localStorage.getItem('token');
      
      if (clientId !== undefined && localStorage.getItem('role') === 'client') {
        router.replace('/client');
        return;
      }
      if (!token) {
        router.push('/login');
        return;
      }

      try {
        const response = await fetch(`http://localhost:8000/clients/${clientId === undefined ? 'me' : clientId}/dashboard`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          if (response.status === 401 || response.status === 403) {
            localStorage.removeItem('token');
            localStorage.removeItem('advisor_id');
            localStorage.removeItem('client_id');
            localStorage.removeItem('role');
            router.push('/login');
            return;
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setDashboard(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load client details');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [clientId, router]);

  if (loading) return <StateView />;
  if (error) return <StateView error={error} />;
  if (!dashboard) return null;

  const accounts = dashboard.banks.flatMap(bank => bank.accounts.map(account => ({ ...account, bankName: bank.name })));
  const holdings = accounts.flatMap(account => account.positions.map(position => ({ ...position, accountName: account.name, accountId: account.id, bankName: account.bankName })));
  const currencies = [...new Set([...accounts.map(a => a.currency), ...holdings.map(p => p.currency)])].sort();
  const currency = currencies.includes(selectedCurrency) ? selectedCurrency : currencies[0] || 'USD';
  const cash = accounts.filter(a => a.currency === currency).reduce((sum, a) => sum + Number(a.balance), 0);
  const invested = holdings.filter(p => p.currency === currency).reduce((sum, p) => sum + Number(p.market_value), 0);
  const total = cash + invested;
  const bankValues = dashboard.banks.map(bank => ({ name: bank.name, value: bank.accounts.reduce((sum, a) => sum + (a.currency === currency ? Number(a.balance) : 0) + a.positions.filter(p => p.currency === currency).reduce((n, p) => n + Number(p.market_value), 0), 0) }));
  const positiveTotal = bankValues.reduce((sum, bank) => sum + Math.max(0, bank.value), 0);
  let stop = 0;
  const gradient = bankValues.map((bank, i) => { const start = stop; stop += positiveTotal ? Math.max(0, bank.value) / positiveTotal * 100 : 0; return `${palette[i % palette.length]} ${start}% ${stop}%`; }).join(', ');
  const visibleAccounts = accounts.filter(a => a.currency === currency);
  const visibleHoldings = holdings.filter(p => p.currency === currency);

  return <WealthShell name={clientId !== undefined ? 'Advisor' : `${dashboard.first_name} ${dashboard.last_name}`} advisor={clientId !== undefined}>
    <section className="page-hero portfolio-hero"><div className="content-width">
      <p className="eyebrow">{clientId !== undefined ? <Link href="/advisor">CLIENT PORTFOLIOS /</Link> : 'YOUR WEALTH /'} PORTFOLIO OVERVIEW</p>
      <div className="hero-title-row"><div><h1>{dashboard.first_name} {dashboard.last_name}</h1><p>A connected view of your financial world.</p></div><span className="hero-badge">{clientId === undefined ? 'Read-only access' : 'Client portfolio'}</span></div>
    </div></section>
    <main className="content-width main-content portfolio-content">
      <div className="overview-toolbar"><div><span className="status-dot" /> Current portfolio snapshot</div><label>Currency <select value={currency} onChange={e => setSelectedCurrency(e.target.value)}>{(currencies.length ? currencies : ['USD']).map(c => <option key={c}>{c}</option>)}</select></label></div>
      <div className="metrics-grid"><section className="metric-card primary-metric"><p>Total assets <span>{currency}</span></p><strong>{money(total, currency)}</strong><small>Account balances + investment positions</small></section><section className="metric-card"><p>Account balances</p><strong>{money(cash, currency)}</strong><small>{visibleAccounts.length} accounts in {currency}</small></section><section className="metric-card"><p>Investment positions</p><strong>{money(invested, currency)}</strong><small>{visibleHoldings.length} holdings in {currency}</small></section><section className="metric-card"><p>Financial institutions</p><strong>{dashboard.banks.length.toString().padStart(2, '0')}</strong><small>{accounts.length} accounts across your portfolio</small></section></div>
      {currencies.length > 1 && <p className="currency-note">Values shown in their original currency. Select a currency to explore its balances; no FX conversion is applied.</p>}
      <div className="analytics-grid"><section className="panel"><div className="panel-heading"><div><h2>Institution allocation</h2><p>Distribution of positive balances · {currency}</p></div><span className="tiny-label">ALLOCATION</span></div><div className="allocation-content"><div className="donut" role="img" aria-label={`Institution allocation in ${currency}. ${bankValues.map(b => `${b.name}: ${money(b.value, currency)}`).join('. ')}`} style={{ background: positiveTotal ? `conic-gradient(${gradient})` : '#e5e9e8' }}><div><span>INSTITUTIONS</span><strong>{bankValues.filter(b => b.value > 0).length}</strong></div></div><div className="allocation-legend">{bankValues.map((bank, i) => <div key={bank.name}><span className="legend-label"><i style={{ background: palette[i % palette.length] }} />{bank.name}</span><strong>{positiveTotal ? (Math.max(0, bank.value) / positiveTotal * 100).toFixed(1) : '0.0'}%</strong></div>)}</div></div></section>
      <section className="panel"><div className="panel-heading"><div><h2>Assets by institution</h2><p>Account balances and holdings · {currency}</p></div></div><div className="bank-bars">{bankValues.map((bank, i) => <div className="bank-bar" key={bank.name}><div><span>{bank.name}</span><strong>{money(bank.value, currency)}</strong></div><div className="bar-track"><div style={{ width: `${positiveTotal ? Math.max(0, bank.value) / positiveTotal * 100 : 0}%`, background: palette[i % palette.length] }} /></div></div>)}{bankValues.length === 0 && <p className="empty-state">No institutions added yet.</p>}</div></section></div>
      <section className="panel holdings-panel"><div className="panel-heading"><div><h2>Portfolio detail</h2><p>The accounts and investments behind your wealth.</p></div><span className="tag">{currency}</span></div><div className="table-tabs" aria-label="Portfolio detail view">{(['accounts', 'holdings'] as const).map(tab => <button key={tab} aria-pressed={activeTab === tab} onClick={() => setActiveTab(tab)} className={activeTab === tab ? 'active' : ''}>{tab === 'accounts' ? 'Accounts' : 'Investment holdings'} <span>{tab === 'accounts' ? visibleAccounts.length : visibleHoldings.length}</span></button>)}</div>
      <div className="table-scroll">{activeTab === 'accounts' ? <table className="data-table"><thead><tr><th>Account name</th><th>Institution</th><th>Account type</th><th>Currency</th><th className="numeric">Balance</th></tr></thead><tbody>{visibleAccounts.map(a => <tr key={a.id}><td className="strong-cell">{a.name}</td><td>{a.bankName}</td><td><span className="type-tag">{a.account_type}</span></td><td>{a.currency}</td><td className="numeric">{money(a.balance, a.currency)}</td></tr>)}</tbody><tfoot><tr><td colSpan={4}>Total account balances</td><td className="numeric">{money(cash, currency)}</td></tr></tfoot></table> : <table className="data-table"><thead><tr><th>Security</th><th>Account</th><th className="numeric">Quantity</th><th>Currency</th><th className="numeric">Market value</th></tr></thead><tbody>{visibleHoldings.map((p, i) => <tr key={`${p.accountId}-${i}`}><td className="strong-cell">{p.security_name}</td><td>{p.accountName}</td><td className="numeric">{number(p.quantity)}</td><td>{p.currency}</td><td className="numeric">{money(p.market_value, p.currency)}</td></tr>)}</tbody><tfoot><tr><td colSpan={4}>Total investment positions</td><td className="numeric">{money(invested, currency)}</td></tr></tfoot></table>}</div>
      {(activeTab === 'accounts' ? visibleAccounts : visibleHoldings).length === 0 && <p className="empty-state">No {activeTab} in {currency}.</p>}
      <div className="panel-footnote">Values reflect the data currently held in your portfolio.</div></section>
      {clientId !== undefined && <details className="panel credentials-panel"><summary>Client login access <span>Manage credentials</span></summary><form onSubmit={saveCredentials} className="credentials-form"><p>Set or reset this client’s credentials for read-only access to their portfolio.</p><div><label>Email<input name="email" type="email" required autoComplete="off" /></label><label>New password<input name="password" type="password" required minLength={8} maxLength={72} autoComplete="new-password" /></label><button disabled={saving} className="button">{saving ? 'Saving…' : 'Save client login'}</button></div><p role="status">{credentialsMessage}</p></form></details>}
    </main>
  </WealthShell>;
}
