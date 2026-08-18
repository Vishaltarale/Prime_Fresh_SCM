import type { ReactNode } from 'react';
import logoFull from '../../assets/logo-full.png';

export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, var(--color-primary-dark), var(--color-accent))',
        padding: 16,
      }}
    >
      <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-lg)', padding: 32, width: '100%', maxWidth: 400 }}>
        <img src={logoFull} alt="Prime Fresh" style={{ height: 36, width: 'auto', marginBottom: 20 }} />
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>{title}</h1>
        <p style={{ marginTop: 4, marginBottom: 24, color: 'var(--color-text-secondary)', fontSize: 14 }}>{subtitle}</p>
        {children}
      </div>
    </div>
  );
}
