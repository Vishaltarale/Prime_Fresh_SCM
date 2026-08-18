interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function SearchBar({ value, onChange, placeholder = 'Search…' }: SearchBarProps) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        padding: '10px 14px',
        borderRadius: 'var(--radius-pill)',
        border: '1px solid var(--color-border)',
        fontSize: 14,
        minWidth: 240,
        background: 'var(--color-surface)',
        outline: 'none',
      }}
    />
  );
}
