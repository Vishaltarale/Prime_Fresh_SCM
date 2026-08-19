import type { InputHTMLAttributes, SelectHTMLAttributes, ReactNode } from 'react';

interface FieldWrapperProps {
  label?: string;
  error?: string;
  children: ReactNode;
}

function FieldWrapper({ label, error, children }: FieldWrapperProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {label && <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-secondary)' }}>{label}</label>}
      {children}
      {error && <span style={{ fontSize: 12, color: 'var(--color-danger)' }}>{error}</span>}
    </div>
  );
}

const controlStyle: React.CSSProperties = {
  padding: '10px 12px',
  borderRadius: 'var(--radius-md)',
  border: '1px solid var(--color-border)',
  fontSize: 14,
  background: 'var(--color-surface)',
  color: 'var(--color-text)',
  outline: 'none',
};

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, style, className, ...rest }: InputProps) {
  return (
    <FieldWrapper label={label} error={error}>
      <input
        className={`input-app ${className ?? ''}`}
        style={{ ...controlStyle, ...style, borderColor: error ? 'var(--color-danger)' : 'var(--color-border)' }}
        {...rest}
      />
    </FieldWrapper>
  );
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
}

export function Select({ label, error, style, className, children, ...rest }: SelectProps) {
  return (
    <FieldWrapper label={label} error={error}>
      <select
        className={`input-app ${className ?? ''}`}
        style={{ ...controlStyle, ...style, borderColor: error ? 'var(--color-danger)' : 'var(--color-border)' }}
        {...rest}
      >
        {children}
      </select>
    </FieldWrapper>
  );
}
