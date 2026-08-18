import { useEffect, useState } from 'react';
import type { CatalogProduct, Category, Subcategory, UomRecord, NamedRef, Paginated, ProductSourceType } from '@shared/types';
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

const emptyForm = {
  name: '', sku: '', category: '', subcategory: '', uom: '', warehouse: '',
  price_per_unit: '', quantity_available: '', description: '',
  source_type: 'supplier' as ProductSourceType, supplier: '', farmer: '',
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
  const [warehouses, setWarehouses] = useState<NamedRef[]>([]);
  const [suppliers, setSuppliers] = useState<NamedRef[]>([]);
  const [farmers, setFarmers] = useState<NamedRef[]>([]);

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
      apiClient.get<NamedRef[]>(API_ENDPOINTS.warehouses),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.suppliers),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.farmers),
    ]).then(([cat, sub, uom, wh, sup, farm]) => {
      setCategories(cat.data.results);
      setSubcategories(sub.data.results);
      setUoms(uom.data.results);
      setWarehouses(wh.data);
      setSuppliers(sup.data);
      setFarmers(farm.data);
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
      const payload: Record<string, string> = { ...form };
      if (form.source_type === 'supplier') delete payload.farmer;
      else delete payload.supplier;

      await apiClient.post(API_ENDPOINTS.catalogProducts, payload);
      show('Product created.', 'success');
      setFormOpen(false);
      setPage(1);
      reload();
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      setErrors(respData ?? { name: 'Failed to create product.' });
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

  const columns: Column<CatalogProduct>[] = [
    { key: 'name', header: 'Name', render: (p) => p.name },
    { key: 'sku', header: 'SKU', render: (p) => p.sku },
    { key: 'category', header: 'Category', render: (p) => p.category?.name ?? '—' },
    { key: 'uom', header: 'UOM', render: (p) => p.uom?.name ?? '—' },
    { key: 'warehouse', header: 'Warehouse', render: (p) => p.warehouse?.name ?? '—' },
    { key: 'price', header: 'Price/Unit', render: (p) => `₹${p.price_per_unit.toFixed(2)}` },
    { key: 'qty', header: 'Qty Available', render: (p) => p.quantity_available },
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
                <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{p.category?.name} · {p.warehouse?.name}</span>
                <span style={{ fontSize: 18, fontWeight: 700 }}>₹{p.price_per_unit.toFixed(2)} / {p.uom?.name}</span>
                <span style={{ fontSize: 13 }}>Qty: {p.quantity_available}</span>
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input label="Name" value={form.name} onChange={(e) => update('name', e.target.value)} error={errors.name} required />
          <Input label="SKU" value={form.sku} onChange={(e) => update('sku', e.target.value)} error={errors.sku} required />
          <Select label="Category" value={form.category} onChange={(e) => { update('category', e.target.value); update('subcategory', ''); }} error={errors.category} required>
            <option value="">Select category…</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Select label="Subcategory" value={form.subcategory} onChange={(e) => update('subcategory', e.target.value)} error={errors.subcategory} required>
            <option value="">Select subcategory…</option>
            {filteredSubcategories.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </Select>
          <Select label="UOM" value={form.uom} onChange={(e) => update('uom', e.target.value)} error={errors.uom} required>
            <option value="">Select unit…</option>
            {uoms.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
          </Select>
          <Select label="Warehouse" value={form.warehouse} onChange={(e) => update('warehouse', e.target.value)} error={errors.warehouse} required>
            <option value="">Select warehouse…</option>
            {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </Select>
          <div style={{ display: 'flex', gap: 12 }}>
            <Input label="Price per unit" type="number" value={form.price_per_unit} onChange={(e) => update('price_per_unit', e.target.value)} error={errors.price_per_unit} required style={{ flex: 1 }} />
            <Input label="Quantity available" type="number" value={form.quantity_available} onChange={(e) => update('quantity_available', e.target.value)} error={errors.quantity_available} style={{ flex: 1 }} />
          </div>
          <Input label="Description" value={form.description} onChange={(e) => update('description', e.target.value)} />
          <Select label="Source type" value={form.source_type} onChange={(e) => update('source_type', e.target.value)}>
            <option value="supplier">Supplier</option>
            <option value="farmer">Farmer</option>
          </Select>
          {form.source_type === 'supplier' ? (
            <Select label="Supplier" value={form.supplier} onChange={(e) => update('supplier', e.target.value)} error={errors.supplier}>
              <option value="">Select supplier…</option>
              {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </Select>
          ) : (
            <Select label="Farmer" value={form.farmer} onChange={(e) => update('farmer', e.target.value)} error={errors.farmer}>
              <option value="">Select farmer…</option>
              {farmers.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
            </Select>
          )}
        </div>
      </Modal>
    </div>
  );
}
