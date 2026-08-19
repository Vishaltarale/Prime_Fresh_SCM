import type { ReactNode, CSSProperties } from 'react';
import { Tilt } from './Tilt';
import { useCountUp } from '../hooks/useCountUp';

export function Card({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      className="card-hover"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-sm)',
        padding: 'var(--space-lg)',
        ...style,
      }}
    >
      {children}
    </div>
  );
}

// Splits a display value like "₹1234.50" into its animatable number and
// surrounding text, so currency/units count up too, not just plain integers.
function parseNumeric(value: string | number): { prefix: string; number: number; decimals: number; suffix: string } | null {
  if (typeof value === 'number') return { prefix: '', number: value, decimals: 0, suffix: '' };
  const match = value.match(/^(\D*)([\d,]+(?:\.\d+)?)(.*)$/);
  if (!match) return null;
  const [, prefix, numStr, suffix] = match;
  const decimals = numStr.includes('.') ? numStr.split('.')[1].length : 0;
  return { prefix, number: parseFloat(numStr.replace(/,/g, '')), decimals, suffix };
}

export function StatCard({ label, value, accent, style }: { label: string; value: string | number; accent?: string; style?: CSSProperties }) {
  const parsed = parseNumeric(value);
  const animated = useCountUp(parsed?.number ?? 0);
  const display = parsed
    ? `${parsed.prefix}${animated.toLocaleString(undefined, { minimumFractionDigits: parsed.decimals, maximumFractionDigits: parsed.decimals })}${parsed.suffix}`
    : value;

  return (
    <Tilt style={style}>
      <Card style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 160 }}>
        <span style={{ fontSize: 13, color: 'var(--color-text-secondary)', fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: 28, fontWeight: 700, color: accent ?? 'var(--color-text)' }}>{display}</span>
      </Card>
    </Tilt>
  );
}
