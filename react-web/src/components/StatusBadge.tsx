const statusColors: Record<string, string> = {
  // GRN statuses
  Draft: 'var(--color-warning)',
  Confirmed: 'var(--color-success)',
  Rejected: 'var(--color-danger)',
  // Order statuses
  Pending: 'var(--color-warning)',
  Processing: 'var(--color-primary)',
  Completed: 'var(--color-success)',
  Cancelled: 'var(--color-danger)',
};

export function StatusBadge({ status }: { status: string }) {
  const color = statusColors[status] ?? 'var(--color-text-secondary)';
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '4px 10px',
        borderRadius: 'var(--radius-pill)',
        fontSize: 12,
        fontWeight: 600,
        color,
        background: `${color}1a`,
        border: `1px solid ${color}40`,
      }}
    >
      {status}
    </span>
  );
}
