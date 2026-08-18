import type { EntityField } from '@shared/types';
import { Input, Select } from './Input';

interface EntityFieldInputProps {
  field: EntityField;
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export function EntityFieldInput({ field, value, onChange, error }: EntityFieldInputProps) {
  if (field.type === 'select' && field.choices) {
    return (
      <Select label={field.label} value={value} onChange={(e) => onChange(e.target.value)} error={error} required={field.required}>
        <option value="">Select {field.label.toLowerCase()}…</option>
        {field.choices.map((c) => <option key={c} value={c}>{c}</option>)}
      </Select>
    );
  }

  if (field.type === 'bool') {
    return (
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600, color: 'var(--color-text-secondary)' }}>
        <input type="checkbox" checked={value === 'true'} onChange={(e) => onChange(String(e.target.checked))} />
        {field.label}
      </label>
    );
  }

  if (field.type === 'textarea') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-secondary)' }}>{field.label}</label>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={field.required}
          rows={3}
          style={{ padding: '10px 12px', borderRadius: 'var(--radius-md)', border: `1px solid ${error ? 'var(--color-danger)' : 'var(--color-border)'}`, fontSize: 14, fontFamily: 'inherit', resize: 'vertical' }}
        />
        {error && <span style={{ fontSize: 12, color: 'var(--color-danger)' }}>{error}</span>}
      </div>
    );
  }

  const htmlType = field.type === 'date' ? 'date' : field.type === 'email' ? 'email' : 'text';
  return (
    <Input
      label={field.label}
      type={htmlType}
      value={field.type === 'date' ? value.slice(0, 10) : value}
      onChange={(e) => onChange(e.target.value)}
      required={field.required}
      error={error}
    />
  );
}
