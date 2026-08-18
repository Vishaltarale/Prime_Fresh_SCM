import { useEffect, useState } from 'react';
import type { Category, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { DataView, type Column } from '../../components/DataView';
import { SearchBar } from '../../components/SearchBar';
import { FilterBar } from '../../components/FilterBar';
import { Pagination } from '../../components/Pagination';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { Input } from '../../components/Input';
import { Modal } from '../../components/Modal';
import { useToast } from '../../components/Toast';

const PAGE_SIZE = 10;

export function CategoryPage() {
  const { show } = useToast();
  const [data, setData] = useState<Paginated<Category> | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [formOpen, setFormOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  function reload() {
    setLoading(true);
    apiClient.get<Paginated<Category>>(API_ENDPOINTS.categories, { params: { search, page } })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }

  useEffect(reload, [search, page]);

  async function handleCreate() {
    setError('');
    setSubmitting(true);
    try {
      await apiClient.post(API_ENDPOINTS.categories, { name, description });
      show('Category created.', 'success');
      setFormOpen(false);
      setName('');
      setDescription('');
      setPage(1);
      reload();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { name?: string } } })?.response?.data?.name;
      setError(msg ?? 'Failed to create category.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(category: Category) {
    setDeleteError('');
    try {
      await apiClient.delete(API_ENDPOINTS.categoryDetail(category.id));
      show('Category deleted.', 'success');
      reload();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setDeleteError(msg ?? 'Delete failed.');
      show(msg ?? 'Delete failed — it may still have subcategories.', 'error');
    }
  }

  const columns: Column<Category>[] = [
    { key: 'name', header: 'Name', render: (c) => c.name },
    { key: 'description', header: 'Description', render: (c) => c.description || '—' },
    { key: 'actions', header: 'Actions', render: (c) => (
      <Button variant="danger" onClick={(e) => { e.stopPropagation(); handleDelete(c); }}>Delete</Button>
    ) },
  ];

  const pageCount = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24 }}>Categories</h1>
        <Button onClick={() => setFormOpen(true)}>+ Add Category</Button>
      </div>

      <FilterBar>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search categories…" />
      </FilterBar>

      {loading && !data ? <Card>Loading…</Card> : (
        <>
          <DataView
            viewKey="catalog-categories"
            columns={columns}
            rows={data?.results ?? []}
            getRowId={(c) => c.id}
            renderCard={(c) => (
              <Card style={{ gap: 6 }}>
                <strong>{c.name}</strong>
                <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{c.description || '—'}</div>
                <Button variant="danger" onClick={() => handleDelete(c)} style={{ marginTop: 8 }}>Delete</Button>
              </Card>
            )}
            emptyMessage="No categories found."
          />
          {data && <Pagination page={page} pageCount={pageCount} onPageChange={setPage} totalCount={data.count} pageSize={PAGE_SIZE} />}
        </>
      )}
      {deleteError && <p style={{ color: 'var(--color-danger)', fontSize: 13 }}>{deleteError}</p>}

      <Modal
        open={formOpen}
        title="Add Category"
        onClose={() => setFormOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button><Button loading={submitting} onClick={handleCreate}>Save</Button></>}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
          {error && <span style={{ fontSize: 13, color: 'var(--color-danger)' }}>{error}</span>}
        </div>
      </Modal>
    </div>
  );
}
