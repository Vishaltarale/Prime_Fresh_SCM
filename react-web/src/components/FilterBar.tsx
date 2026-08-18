import type { ReactNode } from 'react';

export function FilterBar({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: 12,
        marginBottom: 'var(--space-md)',
      }}
    >
      {children}
    </div>
  );
}

interface FilterChipsProps {
  options: string[];
  value: string;
  onChange: (value: string) => void;
  allLabel?: string;
}

export function FilterChips({ options, value, onChange, allLabel = 'All' }: FilterChipsProps) {
  const all = ['', ...options];
  return (
    <div style={{ display: 'flex', gap: 8 }}>
      {all.map((opt) => {
        const active = opt === value;
        return (
          <button
            key={opt || 'all'}
            onClick={() => onChange(opt)}
            style={{
              padding: '8px 14px',
              borderRadius: 'var(--radius-pill)',
              border: '1px solid var(--color-border)',
              background: active ? 'var(--color-primary)' : 'var(--color-surface)',
              color: active ? 'var(--color-text-inverse)' : 'var(--color-text)',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {opt || allLabel}
          </button>
        );
      })}
    </div>
  );
}
