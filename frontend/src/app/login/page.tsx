'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Brand } from '@/components/WealthShell';

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
      
      // Open the dashboard for the selected role
      router.push(role === 'client' ? '/client' : '/advisor');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const demos = role === 'advisor'
    ? [{ name: 'John Smith', email: 'john.smith@example.com', password: 'password' }]
    : [{ name: 'Jane Doe', email: 'jane.doe@example.com', password: 'JaneDemo123!' }, { name: 'Mister Agapitos', email: 'mister.agapitos@example.com', password: 'AgapitosDemo123!' }];

  return (
    <main className="login-layout">
      <section className="login-story">
        <Brand />
        <div className="story-copy"><p className="eyebrow">A CONNECTED VIEW OF YOUR WEALTH</p><h1>Every detail.<br />A clearer <em>perspective.</em></h1><p>Your accounts, investments and institutions.<br />Together in one considered view.</p></div>
        <div className="orbital-art" aria-hidden="true"><div /><div /><div /><span /></div>
        <div className="story-footer"><span>CLARITY THROUGH CONNECTION</span><span>01 / WEALTH</span></div>
      </section>
      <section className="login-panel">
        <div className="login-form-wrap">
          <p className="eyebrow">YOUR WEALTH, IN VIEW</p><h2>Welcome back.</h2><p className="muted">Sign in to your {role === 'advisor' ? 'advisor workspace' : 'personal portfolio'}.</p>
          <div className="role-switch" aria-label="Login type">{(['advisor', 'client'] as const).map(option => <button key={option} type="button" disabled={loading} aria-pressed={role === option} className={role === option ? 'selected' : ''} onClick={() => { setRole(option); setError(''); }}>{option === 'advisor' ? 'Advisor' : 'Client'}</button>)}</div>
          <form onSubmit={handleLogin} className="login-form">
            {error && <p className="error-message" role="alert">{error}</p>}
            <label htmlFor="email">Email address<input id="email" type="email" autoComplete="email" required placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} /></label>
            <label htmlFor="password">Password<input id="password" type="password" autoComplete="current-password" required placeholder="Enter your password" value={password} onChange={e => setPassword(e.target.value)} /></label>
            <button type="submit" className="button login-submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}<span aria-hidden="true">→</span></button>
          </form>
          <div className="demo-section"><div className="demo-heading"><span>Demo Credentials</span><span className="tag">EXPLORE WEALTH</span></div>
            {demos.map(demo => <button type="button" className="demo-account" key={demo.email} disabled={loading} onClick={() => { setEmail(demo.email); setPassword(demo.password); setError(''); }} aria-label={`Use demo credentials for ${demo.name}`}><span><strong>{demo.name}</strong><span>{demo.email}</span><small>Password: {demo.password}</small></span><span className="demo-arrow" aria-hidden="true">↗</span></button>)}
            <p className="demo-hint">Select an account to fill in its demo credentials.</p>
          </div>
        </div>
        <p className="login-footnote">One place. Your complete perspective.</p>
      </section>
    </main>
  );
}
