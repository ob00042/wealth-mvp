'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (!dashboard) {
    return null;
  }

  return (
    <main className="p-10">
      {clientId !== undefined ? <a 
        href="/advisor" 
        className="text-blue-600 hover:underline mb-6 inline-block"
      >
        ← Back to Advisor Dashboard
      </a> : <button className="mb-6 text-blue-600" onClick={() => {
        ['token', 'role', 'advisor_id', 'client_id'].forEach(key => localStorage.removeItem(key));
        router.replace('/login');
      }}>Logout</button>}

      <h1 className="text-3xl font-bold">
        {dashboard.first_name} {dashboard.last_name}
      </h1>

      {clientId !== undefined && <form onSubmit={saveCredentials} className="mt-6 rounded-xl border p-6 space-y-3">
        <h2 className="text-lg font-semibold">Client login access</h2>
        <p>Set or reset this client’s email and password for read-only access to their details.</p>
        <label className="block">Email
          <input name="email" type="email" required className="block border rounded p-2" autoComplete="off" />
        </label>
        <label className="block">New password
          <input name="password" type="password" required minLength={8} maxLength={72} className="block border rounded p-2" autoComplete="new-password" />
        </label>
        <button disabled={saving} className="rounded bg-indigo-600 text-white px-4 py-2 disabled:opacity-50">{saving ? 'Saving...' : 'Save client login'}</button>
        <p role="status">{credentialsMessage}</p>
      </form>}

      <div className="mt-6 rounded-xl border p-6">
        <h2 className="text-lg">
          Total Assets
        </h2>

        <p className="text-4xl font-bold">
          {dashboard.total_assets}
        </p>
      </div>

      <h2 className="mt-10 text-2xl font-bold">
        Banks
      </h2>

      {dashboard.banks.map((bank) => (
        <div
          key={bank.id}
          className="mt-5 rounded-xl border p-5"
        >
          <h3 className="text-xl font-semibold">
            {bank.name}
          </h3>

          {bank.accounts.map((account) => (
            <div
              key={account.id}
              className="mt-4"
            >
              <p className="font-medium">
                {account.name}
              </p>

              <p>
                Balance:
                {" "}
                {account.balance}
                {" "}
                {account.currency}
              </p>

              <ul className="ml-5 mt-2 list-disc">
                {account.positions.map((position) => (
                  <li key={position.security_name}>
                    {position.security_name}
                    :
                    {" "}
                    {position.market_value}
                    {" "}
                    {position.currency}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ))}
    </main>
  );
}
