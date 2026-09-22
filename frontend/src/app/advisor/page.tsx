'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import WealthShell, { StateView } from '@/components/WealthShell';
import { number } from '@/lib/format';

interface Client {
  id: number;
  first_name: string;
  last_name: string;
  total_assets: number;
}

interface AdvisorDashboard {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  clients: Client[];
}

export default function AdvisorDashboard() {
  const [dashboard, setDashboard] = useState<AdvisorDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      const token = localStorage.getItem('token');
      
      if (localStorage.getItem('role') === 'client') {
        router.replace('/client');
        return;
      }
      if (!token) {
        router.push('/login');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/advisors/dashboard', {
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
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [router]);

  if (loading) return <StateView />;
  if (error) return <StateView error={error} />;
  if (!dashboard) return null;
  const clients = dashboard.clients.filter(client => `${client.first_name} ${client.last_name}`.toLowerCase().includes(search.toLowerCase()));

  return <WealthShell name={`${dashboard.first_name} ${dashboard.last_name}`} advisor>
    <section className="page-hero"><div className="content-width"><p className="eyebrow">ADVISOR WORKSPACE / OVERVIEW</p><h1>A perspective on every portfolio.</h1><p>Your client relationships, connected to the details that matter.</p><div className="hero-meta"><span className="status-dot" /> {dashboard.first_name} {dashboard.last_name}<span className="meta-divider" />{dashboard.email}</div></div></section>
    <main className="content-width main-content">
      <div className="advisor-intro"><div><p className="eyebrow">YOUR BOOK OF BUSINESS</p><h2>Client portfolios</h2></div><div className="client-count"><strong>{dashboard.clients.length.toString().padStart(2, '0')}</strong><span>Managed clients</span></div></div>
      <section className="panel"><div className="panel-heading"><div><h3>All clients</h3><p>Open a portfolio to explore accounts and holdings.</p></div><label className="search-field"><span aria-hidden="true">⌕</span><input aria-label="Search clients" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search clients" /></label></div>
        <div className="table-scroll"><table className="data-table client-table"><thead><tr><th>Client name</th><th>Access</th><th className="numeric">Reported total assets*</th><th><span className="sr-only">View portfolio</span></th></tr></thead><tbody>{clients.map((client, i) => <tr key={client.id}><td><Link className="client-identity" href={`/advisor/client/${client.id}`}><span className={`client-avatar tone-${i % 2}`}>{client.first_name[0]}{client.last_name[0]}</span><span><strong>{client.first_name} {client.last_name}</strong><small>Private client · #{String(client.id).padStart(4, '0')}</small></span></Link></td><td><span className="access-tag">Client portfolio</span></td><td className="numeric client-value">{number(client.total_assets)}</td><td><Link className="text-link" href={`/advisor/client/${client.id}`}>View portfolio <span aria-hidden="true">↗</span></Link></td></tr>)}</tbody></table></div>
        {clients.length === 0 && <p className="empty-state">{search ? 'No clients match your search.' : 'No client portfolios yet.'}</p>}
        <div className="panel-footnote">* Reported totals are not currency converted. Open a portfolio for values by currency.</div>
      </section>
      <aside className="insight-strip"><span className="insight-icon" aria-hidden="true">↗</span><div><h3>The full picture starts with the details.</h3><p>Explore each client’s institutions, account balances and investment positions in one view.</p></div></aside>
    </main>
  </WealthShell>;
}
