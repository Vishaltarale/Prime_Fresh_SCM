import type { ButtonHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

const variantStyles: Record<Variant, React.CSSProperties> = {
  primary: { background: 'var(--color-primary)', color: 'var(--color-text-inverse)', border: '1px solid transparent' },
  secondary: { background: 'var(--color-surface)', color: 'var(--color-text)', border: '1px solid var(--color-border)' },
  danger: { background: 'var(--color-danger)', color: 'var(--color-text-inverse)', border: '1px solid transparent' },
  ghost: { background: 'transparent', color: 'var(--color-primary)', border: '1px solid transparent' },
};

export function Button({ variant = 'primary', loading, disabled, children, style, className, ...rest }: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={`btn-app ${className ?? ''}`}
      style={{
        ...base,
        ...variantStyles[variant],
        opacity: disabled || loading ? 0.6 : 1,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        ...style,
      }}
      {...rest}
    >
      {loading ? 'Please wait…' : children}
    </button>
  );
}

const base: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 600,
  padding: '10px 18px',
  borderRadius: 'var(--radius-md)',
  transition: 'filter 0.15s, transform 0.05s',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 8,
};
