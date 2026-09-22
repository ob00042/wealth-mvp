'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [role, setRole] = useState<'advisor' | 'client'>('advisor');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/${role}s/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Login failed');
      }

      const data = await response.json();
      
      // Store the token in localStorage
      localStorage.setItem('token', data.access_token);
      localStorage.removeItem('advisor_id');
      localStorage.removeItem('client_id');
      localStorage.setItem('role', data.role);
      localStorage.setItem(`${role}_id`, String(data[`${role}_id`]));
      
      // Redirect to advisor dashboard
      router.push(role === 'client' ? '/client' : '/advisor');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {role === 'advisor' ? 'Advisor Login' : 'Client Login'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {role === 'advisor' ? 'Sign in to view your clients' : 'Sign in to view your wealth details'}
          </p>
        </div>
        <div className="flex gap-2" aria-label="Login type">
          {(['advisor', 'client'] as const).map((option) => (
            <button key={option} type="button" disabled={loading} aria-pressed={role === option}
              onClick={() => { setRole(option); setError(''); }}
              className={`flex-1 rounded-md border p-2 capitalize ${role === option ? 'bg-indigo-600 text-white' : 'text-gray-900'}`}>
              {option}
            </button>
          ))}
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none rounded-t-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none rounded-b-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="text-center text-sm text-gray-600 space-y-3">
            <p className="font-semibold">Demo Credentials</p>
            {role === 'advisor' ? (
              <div>
                <p className="font-mono">Email: john.smith@example.com</p>
                <p className="font-mono">Password: password</p>
              </div>
            ) : (
              <>
                <div>
                  <p className="font-medium">Jane Doe</p>
                  <p className="font-mono">Email: jane.doe@example.com</p>
                  <p className="font-mono">Password: JaneDemo123!</p>
                </div>
                <div>
                  <p className="font-medium">Mister Agapitos</p>
                  <p className="font-mono">Email: mister.agapitos@example.com</p>
                  <p className="font-mono">Password: AgapitosDemo123!</p>
                </div>
              </>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
