import { useEffect, useState } from 'react';
import type { Category, Subcategory, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { DataView, type Column } from '../../components/DataView';
import { SearchBar } from '../../components/SearchBar';
import { FilterBar } from '../../components/FilterBar';
import { Pagination } from '../../components/Pagination';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { Input, Select } from '../../components/Input';
import { Modal } from '../../components/Modal';
import { useToast } from '../../components/Toast';

const PAGE_SIZE = 10;

export function SubcategoryPage() {
  const { show } = useToast();
  const [categories, setCategories] = useState<Category[]>([]);
  const [data, setData] = useState<Paginated<Subcategory> | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [formOpen, setFormOpen] = useState(false);
  const [name, setName] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiClient.get<Paginated<Category>>(API_ENDPOINTS.categories, { params: { page_size: 100 } })
      .then((res) => setCategories(res.data.results));
  }, []);

  function reload() {
    setLoading(true);
    apiClient.get<Paginated<Subcategory>>(API_ENDPOINTS.subcategories, { params: { search, page } })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }

  useEffect(reload, [search, page]);

  async function handleCreate() {
    setErrors({});
    setSubmitting(true);
    try {
      await apiClient.post(API_ENDPOINTS.subcategories, { name, category: categoryId });
      show('Subcategory created.', 'success');
      setFormOpen(false);
      setName('');
      setCategoryId('');
      setPage(1);
      reload();
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      setErrors(respData ?? { name: 'Failed to create subcategory.' });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(sub: Subcategory) {
    try {
      await apiClient.delete(API_ENDPOINTS.subcategoryDetail(sub.id));
      show('Subcategory deleted.', 'success');
      reload();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      show(msg ?? 'Delete failed — it may still have products.', 'error');
    }
  }

  const columns: Column<Subcategory>[] = [
    { key: 'name', header: 'Name', render: (s) => s.name },
    { key: 'category', header: 'Category', render: (s) => s.category.name },
    { key: 'actions', header: 'Actions', render: (s) => (
      <Button variant="danger" onClick={(e) => { e.stopPropagation(); handleDelete(s); }}>Delete</Button>
    ) },
  ];

  const pageCount = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24 }}>Subcategories</h1>
        <Button onClick={() => setFormOpen(true)}>+ Add Subcategory</Button>
      </div>

      <FilterBar>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search subcategories…" />
      </FilterBar>

      {loading && !data ? <Card>Loading…</Card> : (
        <>
          <DataView
            viewKey="catalog-subcategories"
            columns={columns}
            rows={data?.results ?? []}
            getRowId={(s) => s.id}
            renderCard={(s) => (
              <Card style={{ gap: 6 }}>
                <strong>{s.name}</strong>
                <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{s.category.name}</div>
                <Button variant="danger" onClick={() => handleDelete(s)} style={{ marginTop: 8 }}>Delete</Button>
              </Card>
            )}
            emptyMessage="No subcategories found."
          />
          {data && <Pagination page={page} pageCount={pageCount} onPageChange={setPage} totalCount={data.count} pageSize={PAGE_SIZE} />}
        </>
      )}

      <Modal
        open={formOpen}
        title="Add Subcategory"
        onClose={() => setFormOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button><Button loading={submitting} onClick={handleCreate}>Save</Button></>}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} error={errors.name} required />
          <Select label="Category" value={categoryId} onChange={(e) => setCategoryId(e.target.value)} error={errors.category} required>
            <option value="">Select category…</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
        </div>
      </Modal>
    </div>
  );
}
