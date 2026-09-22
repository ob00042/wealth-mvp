'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { ReactNode } from 'react';

export function Brand() {
  return <span className="brand"><span className="brand-mark" aria-hidden="true">w</span>wealth<span className="brand-caption">PRIVATE WEALTH</span></span>;
}

export default function WealthShell({ children, name, advisor = false }: { children: ReactNode; name: string; advisor?: boolean }) {
  const router = useRouter();
  return <div className="workspace">
    <header className="topbar">
      <Link href={advisor ? '/advisor' : '/client'} aria-label="Wealth home"><Brand /></Link>
      <nav aria-label="Main navigation"><Link className="nav-active" href={advisor ? '/advisor' : '/client'}>{advisor ? 'Client portfolios' : 'Portfolio overview'}</Link></nav>
      <div className="user-menu"><span className="avatar">{name.split(' ').map(n => n[0]).slice(0, 2).join('')}</span><span className="user-name">{name}<small>{advisor ? 'Advisor workspace' : 'Client portal'}</small></span><button className="logout" onClick={() => {
        ['token', 'role', 'advisor_id', 'client_id'].forEach(key => localStorage.removeItem(key));
        router.replace('/login');
      }}>Log out <span aria-hidden="true">↗</span></button></div>
    </header>
    {children}
    <footer className="app-footer"><span>WEALTH / A clearer financial perspective.</span><span>Private wealth overview</span></footer>
  </div>;
}

export function StateView({ error }: { error?: string }) {
  return <main className="state-view"><Brand /><h1>{error ? 'Unable to load your portfolio' : 'Gathering your portfolio'}</h1><p>{error || 'Your financial overview will be ready in a moment.'}</p>{error && <a className="button" href="/login">Return to login</a>}</main>;
}
