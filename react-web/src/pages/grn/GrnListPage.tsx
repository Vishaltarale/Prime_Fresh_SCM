import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { Grn, Paginated } from '@shared/types';
import { API_ENDPOINTS, GRN_STATUSES } from '@shared/constants';
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

export function GrnListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const canCreate = user?.role === 'Admin' || user?.role === 'Inventory Officer' || user?.role === 'Warehouse Manager';
  const [data, setData] = useState<Paginated<Grn> | null>(null);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiClient
      .get<Paginated<Grn>>(API_ENDPOINTS.grnList, { params: { status, search, page } })
      .then((res) => { if (!cancelled) setData(res.data); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [status, search, page]);

  const columns: Column<Grn>[] = [
    { key: 'grn_number', header: 'GRN Number', render: (g) => g.grn_number },
    { key: 'source', header: 'Source', render: (g) => (g.source_type === 'Supplier' ? g.supplier?.name : g.farmer?.name) ?? '—' },
    { key: 'warehouse', header: 'Warehouse', render: (g) => g.warehouse.name },
    { key: 'total', header: 'Total', render: (g) => `₹${g.total_amount.toFixed(2)}` },
    { key: 'status', header: 'Status', render: (g) => <StatusBadge status={g.status} /> },
    { key: 'date', header: 'Date', render: (g) => new Date(g.created_at).toLocaleDateString() },
  ];

  const pageCount = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24 }}>{canCreate ? 'Goods Receipt Notes' : 'My Deliveries'}</h1>
        {canCreate && <Link to="/grn/new"><Button>+ New GRN</Button></Link>}
      </div>

      <FilterBar>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search GRN number…" />
        <FilterChips options={[...GRN_STATUSES]} value={status} onChange={(v) => { setStatus(v); setPage(1); }} />
      </FilterBar>

      {loading && !data ? (
        <Card>Loading…</Card>
      ) : (
        <>
          <DataView
            viewKey="grn-list"
            columns={columns}
            rows={data?.results ?? []}
            getRowId={(g) => g.id}
            renderCard={(g) => (
              <Link to={`/grn/${g.id}`}>
                <Card style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong>{g.grn_number}</strong>
                    <StatusBadge status={g.status} />
                  </div>
                  <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{g.warehouse.name}</span>
                  <span style={{ fontSize: 18, fontWeight: 700 }}>₹{g.total_amount.toFixed(2)}</span>
                </Card>
              </Link>
            )}
            onRowClick={(g) => navigate(`/grn/${g.id}`)}
            emptyMessage="No GRNs match your filters."
          />
          {data && <Pagination page={page} pageCount={pageCount} onPageChange={setPage} totalCount={data.count} pageSize={PAGE_SIZE} />}
        </>
      )}
    </div>
  );
}
