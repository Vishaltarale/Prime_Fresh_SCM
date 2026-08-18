import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import type { NamedRef, ProductRef, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Input, Select } from '../../components/Input';
import { Button } from '../../components/Button';
import { useToast } from '../../components/Toast';

interface ItemForm {
  product: string;
  ordered_qty: number;
  proposed_price: number;
}

interface FormValues {
  supplier: string;
  warehouse: string;
  notes: string;
  items: ItemForm[];
}

export function PoCreatePage() {
  const navigate = useNavigate();
  const { show } = useToast();
  const [suppliers, setSuppliers] = useState<NamedRef[]>([]);
  const [warehouses, setWarehouses] = useState<NamedRef[]>([]);
  const [products, setProducts] = useState<ProductRef[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const { register, control, handleSubmit, watch, setValue, formState: { errors } } = useForm<FormValues>({
    defaultValues: { supplier: '', warehouse: '', notes: '', items: [{ product: '', ordered_qty: 1, proposed_price: 0 }] },
  });
  const { fields, append, remove } = useFieldArray({ control, name: 'items' });
  const items = watch('items');

  useEffect(() => {
    Promise.all([
      apiClient.get<NamedRef[]>(API_ENDPOINTS.suppliers),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.warehouses),
      apiClient.get<Paginated<ProductRef>>(API_ENDPOINTS.catalogProducts, { params: { page_size: 200 } }),
    ]).then(([sup, wh, prod]) => {
      setSuppliers(sup.data);
      setWarehouses(wh.data);
      setProducts(prod.data.results);
    }).finally(() => setLoadingLookups(false));
  }, []);

  const total = (items ?? []).reduce((sum, item) => sum + (Number(item.ordered_qty) || 0) * (Number(item.proposed_price) || 0), 0);

  function pickProduct(index: number, productId: string) {
    const product = products.find((p) => p.id === productId);
    if (!product) return;
    setValue(`items.${index}.proposed_price`, product.price_per_unit);
  }

  async function onSubmit(values: FormValues) {
    setFormError('');
    setSubmitting(true);
    try {
      const res = await apiClient.post(API_ENDPOINTS.purchaseOrders, values);
      show('Purchase Order created as Draft.', 'success');
      navigate(`/purchase-orders/${res.data.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      setFormError(msg ? Object.values(msg).join(' ') : 'Failed to create purchase order.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loadingLookups) return <Card>Loading form…</Card>;

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 20 }}>New Purchase Order</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
            <Select label="Supplier" {...register('supplier', { required: true })} error={errors.supplier ? 'Required' : undefined}>
              <option value="">Select supplier…</option>
              {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </Select>
            <Select label="Warehouse" {...register('warehouse', { required: true })} error={errors.warehouse ? 'Required' : undefined}>
              <option value="">Select warehouse…</option>
              {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </Select>
          </div>
          <div style={{ marginTop: 16 }}>
            <Input label="Notes" {...register('notes')} />
          </div>
        </Card>

        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: 16 }}>Line items — proposed pricing</h3>
            <Button type="button" variant="secondary" onClick={() => append({ product: '', ordered_qty: 1, proposed_price: 0 })}>+ Add row</Button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)' }}>
                  <th style={{ padding: 8 }}>Product</th>
                  <th style={{ padding: 8 }}>Ordered Qty</th>
                  <th style={{ padding: 8 }}>Proposed Price</th>
                  <th style={{ padding: 8 }} />
                </tr>
              </thead>
              <tbody>
                {fields.map((field, index) => (
                  <tr key={field.id} style={{ borderTop: '1px solid var(--color-border)' }}>
                    <td style={{ padding: 8 }}>
                      <select
                        {...register(`items.${index}.product` as const, { required: true, onChange: (e) => pickProduct(index, e.target.value) })}
                        style={{ padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }}
                      >
                        <option value="">Select…</option>
                        {products.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>)}
                      </select>
                    </td>
                    <td style={{ padding: 8 }}>
                      <input type="number" min={1} {...register(`items.${index}.ordered_qty` as const, { valueAsNumber: true, required: true })} style={{ width: 90, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
                    </td>
                    <td style={{ padding: 8 }}>
                      <input type="number" min={0} step="0.01" {...register(`items.${index}.proposed_price` as const, { valueAsNumber: true, required: true })} style={{ width: 110, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
                    </td>
                    <td style={{ padding: 8 }}>
                      {fields.length > 1 && (
                        <button type="button" onClick={() => remove(index)} style={{ background: 'none', border: 'none', color: 'var(--color-danger)', cursor: 'pointer' }}>✕</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16, fontSize: 18, fontWeight: 700 }}>
            Proposed Total: ₹{total.toFixed(2)}
          </div>
        </Card>

        {formError && <p style={{ color: 'var(--color-danger)', fontSize: 13, marginTop: 12 }}>{formError}</p>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 20 }}>
          <Button type="button" variant="secondary" onClick={() => navigate('/purchase-orders')}>Cancel</Button>
          <Button type="submit" loading={submitting}>Save as Draft</Button>
        </div>
      </form>
    </div>
  );
}
