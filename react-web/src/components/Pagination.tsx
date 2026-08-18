import { Button } from './Button';

interface PaginationProps {
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
  totalCount: number;
  pageSize: number;
}

export function Pagination({ page, pageCount, onPageChange, totalCount, pageSize }: PaginationProps) {
  if (totalCount === 0) return null;
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalCount);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'var(--space-md)' }}>
      <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
        Showing {start}–{end} of {totalCount}
      </span>
      <div style={{ display: 'flex', gap: 8 }}>
        <Button variant="secondary" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          Previous
        </Button>
        <span style={{ alignSelf: 'center', fontSize: 13, color: 'var(--color-text-secondary)' }}>
          Page {page} of {pageCount}
        </span>
        <Button variant="secondary" disabled={page >= pageCount} onClick={() => onPageChange(page + 1)}>
          Next
        </Button>
      </div>
    </div>
  );
}
