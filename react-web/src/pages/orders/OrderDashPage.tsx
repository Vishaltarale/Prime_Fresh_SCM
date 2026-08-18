import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { Order, Paginated } from '@shared/types';
import { API_ENDPOINTS, ORDER_STATUSES } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { DataView, type Column } from '../../components/DataView';
import { FilterBar, FilterChips } from '../../components/FilterBar';
import { SearchBar } from '../../components/SearchBar';
import { Pagination } from '../../components/Pagination';
import { StatusBadge } from '../../components/StatusBadge';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { useAuth } from '../../context/AuthContext';

const PAGE_SIZE = 10;

export function OrderDashPage({ allOrders = false }: { allOrders?: boolean }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<Paginated<Order> | null>(null);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiClient
      .get<Paginated<Order>>(API_ENDPOINTS.orders, { params: { status, search, page, mine: allOrders ? undefined : 'true' } })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [status, search, page, allOrders]);

  const columns: Column<Order>[] = [
    { key: 'customer_name', header: 'Customer', render: (o) => o.customer_name },
    { key: 'warehouse', header: 'Warehouse', render: (o) => o.warehouse?.name ?? '—' },
    { key: 'total', header: 'Total', render: (o) => `₹${o.total_amount.toFixed(2)}` },
    { key: 'payment', header: 'Payment', render: (o) => o.payment_status },
    { key: 'status', header: 'Status', render: (o) => <StatusBadge status={o.status} /> },
    { key: 'date', header: 'Date', render: (o) => o.order_date },
  ];

  const pageCount = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24 }}>{allOrders ? 'All Orders' : `${user?.full_name}'s Orders`}</h1>
        <Link to="/orders/new"><Button>+ New Order</Button></Link>
      </div>

      <FilterBar>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search customer…" />
        <FilterChips options={[...ORDER_STATUSES]} value={status} onChange={(v) => { setStatus(v); setPage(1); }} />
      </FilterBar>

      {loading && !data ? <Card>Loading…</Card> : (
        <>
          <DataView
            viewKey={allOrders ? 'orders-all' : 'orders-mine'}
            columns={columns}
            rows={data?.results ?? []}
            getRowId={(o) => o.id}
            renderCard={(o) => (
              <Card style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>{o.customer_name}</strong>
                  <StatusBadge status={o.status} />
                </div>
                <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{o.warehouse?.name}</span>
                <span style={{ fontSize: 18, fontWeight: 700 }}>₹{o.total_amount.toFixed(2)}</span>
              </Card>
            )}
            onRowClick={(o) => navigate(`/orders/${o.id}`)}
            emptyMessage="No orders match your filters."
          />
          {data && <Pagination page={page} pageCount={pageCount} onPageChange={setPage} totalCount={data.count} pageSize={PAGE_SIZE} />}
        </>
      )}
    </div>
  );
}
