import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { PurchaseOrder, Paginated } from '@shared/types';
import { API_ENDPOINTS, PO_STATUSES } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { DataView, type Column } from '../../components/DataView';
import { FilterBar, FilterChips } from '../../components/FilterBar';
import { SearchBar } from '../../components/SearchBar';
import { Pagination } from '../../components/Pagination';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';

const PAGE_SIZE = 10;

const STATUS_COLORS: Record<string, string> = {
  Draft: 'var(--color-text-secondary)',
  Sent: 'var(--color-primary)',
  'Awaiting Approval': 'var(--color-warning)',
  Confirmed: 'var(--color-success)',
  Rejected: 'var(--color-danger)',
};

function PoStatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? 'var(--color-text-secondary)';
  return (
    <span style={{ display: 'inline-block', padding: '4px 10px', borderRadius: 'var(--radius-pill)', fontSize: 12, fontWeight: 600, color, background: `${color}1a`, border: `1px solid ${color}40` }}>
      {status}
    </span>
  );
}

export function PoListPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<Paginated<PurchaseOrder> | null>(null);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiClient
      .get<Paginated<PurchaseOrder>>(API_ENDPOINTS.purchaseOrders, { params: { status, search, page } })
      .then((res) => { if (!cancelled) setData(res.data); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [status, search, page]);

  const columns: Column<PurchaseOrder>[] = [
    { key: 'po_number', header: 'PO Number', render: (po) => po.po_number },
    { key: 'supplier', header: 'Supplier', render: (po) => po.supplier.name },
    { key: 'warehouse', header: 'Warehouse', render: (po) => po.warehouse.name },
    { key: 'total', header: 'Total', render: (po) => `₹${(po.confirmed_total || po.proposed_total).toFixed(2)}` },
    { key: 'status', header: 'Status', render: (po) => <PoStatusBadge status={po.status} /> },
    { key: 'date', header: 'Date', render: (po) => new Date(po.created_at).toLocaleDateString() },
  ];

  const pageCount = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24 }}>Purchase Orders</h1>
        <Link to="/purchase-orders/new"><Button>+ New Purchase Order</Button></Link>
      </div>

      <FilterBar>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search PO number…" />
        <FilterChips options={[...PO_STATUSES]} value={status} onChange={(v) => { setStatus(v); setPage(1); }} />
      </FilterBar>

      {loading && !data ? (
        <Card>Loading…</Card>
      ) : (
        <>
          <DataView
            viewKey="po-list"
            columns={columns}
            rows={data?.results ?? []}
            getRowId={(po) => po.id}
            renderCard={(po) => (
              <Link to={`/purchase-orders/${po.id}`}>
                <Card style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong>{po.po_number}</strong>
                    <PoStatusBadge status={po.status} />
                  </div>
                  <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{po.supplier.name} · {po.warehouse.name}</span>
                  <span style={{ fontSize: 18, fontWeight: 700 }}>₹{(po.confirmed_total || po.proposed_total).toFixed(2)}</span>
                </Card>
              </Link>
            )}
            onRowClick={(po) => navigate(`/purchase-orders/${po.id}`)}
            emptyMessage="No purchase orders match your filters."
          />
          {data && <Pagination page={page} pageCount={pageCount} onPageChange={setPage} totalCount={data.count} pageSize={PAGE_SIZE} />}
        </>
      )}
    </div>
  );
}

export { PoStatusBadge };
