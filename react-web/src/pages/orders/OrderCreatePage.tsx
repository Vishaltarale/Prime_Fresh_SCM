import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import type { NamedRef, CatalogProduct, OrderCreateInput, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Input, Select } from '../../components/Input';
import { Button } from '../../components/Button';
import { useToast } from '../../components/Toast';
import { useAuth } from '../../context/AuthContext';

interface FormValues extends OrderCreateInput {}

export function OrderCreatePage() {
  const navigate = useNavigate();
  const { show } = useToast();
  const { user } = useAuth();
  const isCustomer = user?.role === 'Customer';
  const [warehouses, setWarehouses] = useState<NamedRef[]>([]);
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const { register, control, handleSubmit, watch, setValue, formState: { errors } } = useForm<FormValues>({
    defaultValues: {
      customer_name: isCustomer ? user!.full_name : '', delivery_address: '', warehouse: '',
      items: [{ product: '', quantity: 1, price: 0, uom: '' }],
    },
  });
  const { fields, append, remove } = useFieldArray({ control, name: 'items' });
  const warehouseId = watch('warehouse');
  const items = watch('items');

  useEffect(() => {
    Promise.all([
      apiClient.get<NamedRef[]>(API_ENDPOINTS.warehouses),
      apiClient.get<Paginated<CatalogProduct>>(API_ENDPOINTS.catalogProducts, { params: { page_size: 200 } }),
    ]).then(([wh, prod]) => {
      setWarehouses(wh.data);
      setProducts(prod.data.results);
    }).finally(() => setLoadingLookups(false));
  }, []);

  const productsInWarehouse = products.filter((p) => p.warehouse?.id === warehouseId);
  const total = (items ?? []).reduce((sum, item) => sum + (Number(item.quantity) || 0) * (Number(item.price) || 0), 0);

  function pickProduct(index: number, productId: string) {
    const product = products.find((p) => p.id === productId);
    if (!product) return;
    setValue(`items.${index}.price`, product.price_per_unit);
    setValue(`items.${index}.uom`, product.uom?.name ?? '');
  }

  async function onSubmit(values: FormValues) {
    setFormError('');
    setSubmitting(true);
    try {
      const res = await apiClient.post(API_ENDPOINTS.orders, values);
      show('Order placed successfully.', 'success');
      navigate(`/orders/${res.data.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { items?: string; customer_name?: string; warehouse?: string } } })?.response?.data;
      setFormError(msg?.items ?? msg?.customer_name ?? msg?.warehouse ?? 'Failed to place order.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loadingLookups) return <Card>Loading form…</Card>;

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 20 }}>New Order</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
            <Input
              label="Customer Name"
              disabled={isCustomer}
              {...register('customer_name', { required: true })}
              error={errors.customer_name ? 'Required' : undefined}
            />
            <Select label="Warehouse" {...register('warehouse', { required: true })} error={errors.warehouse ? 'Required' : undefined}>
              <option value="">Select warehouse…</option>
              {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </Select>
          </div>
          <div style={{ marginTop: 16 }}>
            <Input label="Delivery Address" {...register('delivery_address', { required: true })} error={errors.delivery_address ? 'Required' : undefined} />
          </div>
        </Card>

        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: 16 }}>Line items</h3>
            <Button type="button" variant="secondary" onClick={() => append({ product: '', quantity: 1, price: 0, uom: '' })}>
              + Add row
            </Button>
          </div>

          {!warehouseId && <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>Select a warehouse to choose products.</p>}

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)' }}>
                  <th style={{ padding: 8 }}>Product</th>
                  <th style={{ padding: 8 }}>Quantity</th>
                  <th style={{ padding: 8 }}>Price</th>
                  <th style={{ padding: 8 }}>UOM</th>
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
                        disabled={!warehouseId}
                      >
                        <option value="">Select…</option>
                        {productsInWarehouse.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.sku}) — {p.quantity_available} in stock</option>)}
                      </select>
                    </td>
                    <td style={{ padding: 8 }}>
                      <input type="number" min={1} {...register(`items.${index}.quantity` as const, { valueAsNumber: true, required: true })} style={{ width: 90, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
                    </td>
                    <td style={{ padding: 8 }}>
                      <input type="number" min={0} step="0.01" {...register(`items.${index}.price` as const, { valueAsNumber: true, required: true })} style={{ width: 100, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
                    </td>
                    <td style={{ padding: 8 }}>
                      <input {...register(`items.${index}.uom` as const)} style={{ width: 70, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
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
            Total: ₹{total.toFixed(2)}
          </div>
        </Card>

        {formError && <p style={{ color: 'var(--color-danger)', fontSize: 13, marginTop: 12 }}>{formError}</p>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 20 }}>
          <Button type="button" variant="secondary" onClick={() => navigate('/orders')}>Cancel</Button>
          <Button type="submit" loading={submitting}>Place Order</Button>
        </div>
      </form>
    </div>
  );
}
