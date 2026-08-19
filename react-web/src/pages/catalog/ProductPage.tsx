import { useEffect, useState } from 'react';
import type { CatalogProduct, Category, Subcategory, UomRecord, Paginated } from '@shared/types';
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

// Reference-only fields: a product created here is a catalog entry for PO
// dropdowns, not stock. Warehouse/quantity/source only get set once a PO
// raised against it has its GRN confirmed (see mysite/grn_views.py / GRNConfirmView).
const emptyForm = {
  name: '', sku: '', category: '', subcategory: '', uom: '',
  price_per_unit: '', description: '',
};

export function ProductPage() {
  const { show } = useToast();
  const [data, setData] = useState<Paginated<CatalogProduct> | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [categories, setCategories] = useState<Category[]>([]);
  const [subcategories, setSubcategories] = useState<Subcategory[]>([]);
  const [uoms, setUoms] = useState<UomRecord[]>([]);

  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  function reload() {
    setLoading(true);
    apiClient.get<Paginated<CatalogProduct>>(API_ENDPOINTS.catalogProducts, { params: { search, page } })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }

  useEffect(reload, [search, page]);

  useEffect(() => {
    Promise.all([
      apiClient.get<Paginated<Category>>(API_ENDPOINTS.categories, { params: { page_size: 100 } }),
      apiClient.get<Paginated<Subcategory>>(API_ENDPOINTS.subcategories, { params: { page_size: 100 } }),
      apiClient.get<Paginated<UomRecord>>(API_ENDPOINTS.catalogUom, { params: { page_size: 100 } }),
    ]).then(([cat, sub, uom]) => {
      setCategories(cat.data.results);
      setSubcategories(sub.data.results);
      setUoms(uom.data.results);
    });
  }, []);

  const filteredSubcategories = subcategories.filter((s) => s.category.id === form.category);

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function openCreate() {
    setForm(emptyForm);
    setErrors({});
    setFormOpen(true);
  }

  async function handleSave() {
    setErrors({});
    setSubmitting(true);
    try {
      await apiClient.post(API_ENDPOINTS.catalogProducts, form);
      show('Product created.', 'success');
      setFormOpen(false);
      setPage(1);
      reload();
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      setErrors(respData ?? { name: 'Failed to create product.' });
      const message = respData ? Object.values(respData).join(' ') : 'Failed to create product.';
      show(message, 'error');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(product: CatalogProduct) {
    try {
      await apiClient.delete(API_ENDPOINTS.catalogProductDetail(product.id));
      show('Product deleted.', 'success');
      reload();
    } catch {
      show('Delete failed.', 'error');
    }
  }

  function renderStock(p: CatalogProduct) {
    if (p.stock.length === 0) {
      return <span style={{ color: 'var(--color-text-secondary)' }}>Not received yet</span>;
    }
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {p.stock.map((line) => (
          <span key={line.warehouse.id} style={{ fontSize: 13 }}>
            {line.warehouse.name}: <strong>{line.quantity_available}</strong>
            {line.price_per_unit != null && (
              <span style={{ color: 'var(--color-text-secondary)' }}> @ ₹{line.price_per_unit.toFixed(2)}</span>
            )}
          </span>
        ))}
      </div>
    );
  }

  const columns: Column<CatalogProduct>[] = [
    { key: 'name', header: 'Name', render: (p) => p.name },
    { key: 'sku', header: 'SKU', render: (p) => p.sku },
    { key: 'category', header: 'Category', render: (p) => p.category?.name ?? '—' },
    { key: 'uom', header: 'UOM', render: (p) => p.uom?.name ?? '—' },
    { key: 'refPrice', header: 'Reference Price', render: (p) => `₹${p.price_per_unit.toFixed(2)}` },
    { key: 'stock', header: 'Stock by Warehouse', render: renderStock },
    { key: 'totalQty', header: 'Total Qty', render: (p) => p.quantity_available },
    { key: 'source', header: 'Source', render: (p) => p.supplier?.name ?? p.farmer?.name ?? '—' },
    { key: 'actions', header: 'Actions', render: (p) => (
      <Button variant="danger" onClick={(e) => { e.stopPropagation(); handleDelete(p); }}>Delete</Button>
    ) },
  ];

  const pageCount = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24 }}>Products</h1>
        <Button onClick={openCreate}>+ Add Product</Button>
      </div>

      <FilterBar>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search name or SKU…" />
      </FilterBar>

      {loading && !data ? <Card>Loading…</Card> : (
        <>
          <DataView
            viewKey="catalog-products"
            columns={columns}
            rows={data?.results ?? []}
            getRowId={(p) => p.id}
            renderCard={(p) => (
              <Card style={{ gap: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>{p.name}</strong>
                  <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{p.sku}</span>
                </div>
                <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{p.category?.name}</span>
                <span style={{ fontSize: 18, fontWeight: 700 }}>₹{p.price_per_unit.toFixed(2)} / {p.uom?.name}</span>
                {renderStock(p)}
                <Button variant="danger" onClick={() => handleDelete(p)} style={{ marginTop: 8 }}>Delete</Button>
              </Card>
            )}
            emptyMessage="No products found."
          />
          {data && <Pagination page={page} pageCount={pageCount} onPageChange={setPage} totalCount={data.count} pageSize={PAGE_SIZE} />}
        </>
      )}

      <Modal
        open={formOpen}
        title="Add Product"
        onClose={() => setFormOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button><Button loading={submitting} onClick={handleSave}>Save</Button></>}
      >
        <p style={{ marginTop: 0, marginBottom: 14, fontSize: 13, color: 'var(--color-text-secondary)' }}>
          This adds a catalog reference only — it won't sit in any warehouse or count as stock until it's
          ordered on a Purchase Order and that order's GRN is confirmed.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input label="Name" value={form.name} onChange={(e) => update('name', e.target.value)} error={errors.name} required />
          <Input label="SKU" value={form.sku} onChange={(e) => update('sku', e.target.value)} error={errors.sku} required />
          <Select label="Category" value={form.category} onChange={(e) => { update('category', e.target.value); update('subcategory', ''); }} error={errors.category} required>
            <option value="">Select category…</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Select
            label="Subcategory"
            value={form.subcategory}
            onChange={(e) => update('subcategory', e.target.value)}
            error={errors.subcategory}
            required
            disabled={!form.category}
          >
            <option value="">{form.category ? 'Select subcategory…' : 'Select a category first'}</option>
            {filteredSubcategories.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </Select>
          {form.category && filteredSubcategories.length === 0 && (
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: -8 }}>
              No subcategories yet for this category — add one under Subcategories first.
            </span>
          )}
          <Select label="UOM" value={form.uom} onChange={(e) => update('uom', e.target.value)} error={errors.uom} required>
            <option value="">Select unit…</option>
            {uoms.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
          </Select>
          <Input label="Reference price per unit" type="number" value={form.price_per_unit} onChange={(e) => update('price_per_unit', e.target.value)} error={errors.price_per_unit} required />
          <Input label="Description" value={form.description} onChange={(e) => update('description', e.target.value)} />
        </div>
      </Modal>
    </div>
  );
}
