import { lazy, Suspense, type ReactNode } from 'react';
import logoFull from '../../assets/logo-full.png';

// Lazy-loaded: three.js/@react-three add ~900kB, and only the auth screens
// need it — code-splitting keeps it out of the main app bundle entirely.
const ParticleRing = lazy(() => import('../../components/ParticleRing').then((m) => ({ default: m.ParticleRing })));

export function AuthLayout({
  title,
  subtitle,
  children,
  wide = false,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  /** Wider card for forms with side-by-side fields (e.g. registration). */
  wide?: boolean;
}) {
  return (
    <div
      className="auth-bg"
      style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
      }}
    >
      <Suspense fallback={null}>
        <ParticleRing />
      </Suspense>
      <div
        className="auth-card-enter"
        style={{
          position: 'relative',
          zIndex: 1,
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          width: '100%',
          maxWidth: wide ? 640 : 400,
          maxHeight: '100%',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Fixed header — logo/title never scroll with the form */}
        <div style={{ flexShrink: 0, padding: wide ? '24px 28px 0' : '32px 32px 0' }}>
          <img src={logoFull} alt="Prime Fresh" className="logo-badge" style={{ height: wide ? 30 : 36, width: 'auto', marginBottom: wide ? 12 : 20 }} />
          <h1 style={{ margin: 0, fontSize: wide ? 20 : 24, fontWeight: 800 }}>{title}</h1>
          <p style={{ marginTop: 4, marginBottom: wide ? 16 : 24, color: 'var(--color-text-secondary)', fontSize: 14 }}>{subtitle}</p>
        </div>

        {/* Scrollable body — only the form fields scroll */}
        <div className="auth-card-scroll" style={{ flex: 1, overflowY: 'auto', padding: wide ? '0 28px 24px' : '0 32px 32px' }}>
          {children}
        </div>
      </div>
    </div>
  );
}
