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

export default function ClientDetails({ params }: { params: Promise<{ id: string }> }) {
  const [dashboard, setDashboard] = useState<ClientDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();
  const [clientId, setClientId] = useState<number | null>(null);

  useEffect(() => {
    const loadParams = async () => {
      const { id } = await params;
      setClientId(parseInt(id));
    };
    loadParams();
  }, [params]);

  useEffect(() => {
    if (!clientId) return;

    const fetchDashboard = async () => {
      const token = localStorage.getItem('token');
      
      if (!token) {
        router.push('/login');
        return;
      }

      try {
        const response = await fetch(`http://localhost:8000/clients/${clientId}/dashboard`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          if (response.status === 401 || response.status === 403) {
            localStorage.removeItem('token');
            localStorage.removeItem('advisor_id');
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
      <a 
        href="/advisor" 
        className="text-blue-600 hover:underline mb-6 inline-block"
      >
        ← Back to Advisor Dashboard
      </a>

      <h1 className="text-3xl font-bold">
        {dashboard.first_name} {dashboard.last_name}
      </h1>

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
