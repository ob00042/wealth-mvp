'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

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

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('advisor_id');
            localStorage.removeItem('client_id');
            localStorage.removeItem('role');
    router.push('/login');
  };

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
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">
            Advisor: {dashboard.first_name} {dashboard.last_name}
          </h1>
          <p className="text-gray-600">{dashboard.email}</p>
        </div>
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Logout
        </button>
      </div>

      <h2 className="text-2xl font-bold">
        Clients ({dashboard.clients.length})
      </h2>

      <div className="mt-6 space-y-4">
        {dashboard.clients.map((client) => (
          <a
            key={client.id}
            href={`/advisor/client/${client.id}`}
            className="block rounded-xl border p-6 hover:bg-gray-50 transition-colors"
          >
            <h3 className="text-xl font-semibold">
              {client.first_name} {client.last_name}
            </h3>
            <p className="mt-2 text-lg">
              Total Assets: {client.total_assets}
            </p>
          </a>
        ))}
      </div>
    </main>
  );
}
