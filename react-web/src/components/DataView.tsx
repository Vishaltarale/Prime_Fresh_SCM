import { useState, type ReactNode } from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

interface DataViewProps<T> {
  /** Unique key used to persist the table/grid toggle choice per page. */
  viewKey: string;
  columns: Column<T>[];
  rows: T[];
  getRowId: (row: T) => string;
  renderCard: (row: T) => ReactNode;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

type ViewMode = 'table' | 'grid';

function loadViewMode(viewKey: string): ViewMode {
  const stored = localStorage.getItem(`dataview_${viewKey}`);
  return stored === 'grid' ? 'grid' : 'table';
}

export function DataView<T>({ viewKey, columns, rows, getRowId, renderCard, onRowClick, emptyMessage }: DataViewProps<T>) {
  const [mode, setMode] = useState<ViewMode>(() => loadViewMode(viewKey));

  function setModeAndPersist(next: ViewMode) {
    setMode(next);
    localStorage.setItem(`dataview_${viewKey}`, next);
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
        <div style={toggleWrapStyle}>
          <button style={toggleBtnStyle(mode === 'table')} onClick={() => setModeAndPersist('table')}>
            ☰ Table
          </button>
          <button style={toggleBtnStyle(mode === 'grid')} onClick={() => setModeAndPersist('grid')}>
            ▦ Grid
          </button>
        </div>
      </div>

      <div style={containerStyle}>
        {rows.length === 0 ? (
          <div style={emptyStyle}>{emptyMessage ?? 'No records found.'}</div>
        ) : mode === 'table' ? (
          <table style={tableStyle}>
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col.key} style={thStyle}>{col.header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={getRowId(row)}
                  style={{ cursor: onRowClick ? 'pointer' : 'default' }}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((col) => (
                    <td key={col.key} style={tdStyle}>{col.render(row)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={gridStyle}>
            {rows.map((row) => (
              <div key={getRowId(row)} onClick={() => onRowClick?.(row)} style={{ cursor: onRowClick ? 'pointer' : 'default' }}>
                {renderCard(row)}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const containerStyle: React.CSSProperties = {
  maxHeight: 560,
  overflowY: 'auto',
  overflowX: 'auto',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-lg)',
  background: 'var(--color-surface)',
};

const tableStyle: React.CSSProperties = { width: '100%', borderCollapse: 'collapse', fontSize: 14 };
const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '12px 16px',
  background: 'var(--color-bg)',
  color: 'var(--color-text-secondary)',
  fontWeight: 600,
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: 0.4,
  position: 'sticky',
  top: 0,
};
const tdStyle: React.CSSProperties = { padding: '12px 16px', borderTop: '1px solid var(--color-border)' };

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
  gap: 16,
  padding: 16,
};

const emptyStyle: React.CSSProperties = {
  padding: 48,
  textAlign: 'center',
  color: 'var(--color-text-secondary)',
  fontSize: 14,
};

const toggleWrapStyle: React.CSSProperties = {
  display: 'inline-flex',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  overflow: 'hidden',
};

function toggleBtnStyle(active: boolean): React.CSSProperties {
  return {
    padding: '8px 14px',
    fontSize: 13,
    fontWeight: 600,
    border: 'none',
    cursor: 'pointer',
    background: active ? 'var(--color-primary)' : 'var(--color-surface)',
    color: active ? 'var(--color-text-inverse)' : 'var(--color-text-secondary)',
  };
}
