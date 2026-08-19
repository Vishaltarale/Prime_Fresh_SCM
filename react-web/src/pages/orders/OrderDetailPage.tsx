import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import type { Order, NamedRef, CatalogProduct, Paginated } from '@shared/types';
import { API_ENDPOINTS, ORDER_STATUSES, PAYMENT_STATUSES } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Input, Select } from '../../components/Input';
import { Button } from '../../components/Button';
import { StatusBadge } from '../../components/StatusBadge';
import { Modal } from '../../components/Modal';
import { useToast } from '../../components/Toast';
import { useAuth } from '../../context/AuthContext';

interface FormValues {
  customer_name: string;
  delivery_address: string;
  status: string;
  payment_status: string;
  warehouse: string;
  items: Array<{ product: string; quantity: number; price: number; uom: string }>;
}

export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { show } = useToast();
  const { user } = useAuth();
  const isCustomer = user?.role === 'Customer';

  const [order, setOrder] = useState<Order | null>(null);
  const [warehouses, setWarehouses] = useState<NamedRef[]>([]);
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [downloadingInvoice, setDownloadingInvoice] = useState(false);

  const { register, control, handleSubmit, watch, reset, setValue } = useForm<FormValues>({
    defaultValues: { customer_name: '', delivery_address: '', status: '', payment_status: '', warehouse: '', items: [] },
  });
  const { fields, append, remove } = useFieldArray({ control, name: 'items' });
  const warehouseId = watch('warehouse');
  const items = watch('items');

  useEffect(() => {
    if (!id) return;
    Promise.all([
      apiClient.get<Order>(API_ENDPOINTS.orderDetail(id)),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.warehouses),
      apiClient.get<Paginated<CatalogProduct>>(API_ENDPOINTS.catalogProducts, { params: { page_size: 200 } }),
    ]).then(([orderRes, whRes, prodRes]) => {
      setOrder(orderRes.data);
      setWarehouses(whRes.data);
      setProducts(prodRes.data.results);

      const matchedItems = orderRes.data.items.map((item) => {
        const match = prodRes.data.results.find(
          (p) => p.name === item.product_name && p.stock.some((s) => s.warehouse.id === orderRes.data.warehouse?.id),
        );
        return { product: match?.id ?? '', quantity: item.quantity, price: item.price, uom: item.uom };
      });
      reset({
        customer_name: orderRes.data.customer_name,
        delivery_address: orderRes.data.delivery_address,
        status: orderRes.data.status,
        payment_status: orderRes.data.payment_status,
        warehouse: orderRes.data.warehouse?.id ?? '',
        items: matchedItems,
      });
    }).finally(() => setLoading(false));
  }, [id, reset]);

  const productsInWarehouse = products
    .map((p) => ({ product: p, stockLine: p.stock.find((s) => s.warehouse.id === warehouseId) }))
    .filter((row): row is { product: CatalogProduct; stockLine: NonNullable<typeof row.stockLine> } => !!row.stockLine);
  const total = (items ?? []).reduce((sum, item) => sum + (Number(item.quantity) || 0) * (Number(item.price) || 0), 0);

  function pickProduct(index: number, productId: string) {
    const product = products.find((p) => p.id === productId);
    if (!product) return;
    const stockLine = product.stock.find((s) => s.warehouse.id === warehouseId);
    setValue(`items.${index}.price`, stockLine?.price_per_unit ?? product.price_per_unit);
    setValue(`items.${index}.uom`, product.uom?.name ?? '');
  }

  async function onSubmit(values: FormValues) {
    if (!id) return;
    setSubmitting(true);
    try {
      const res = await apiClient.put<Order>(API_ENDPOINTS.orderDetail(id), values);
      setOrder(res.data);
      show('Order updated.', 'success');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { items?: string } } })?.response?.data?.items;
      show(msg ?? 'Update failed.', 'error');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!id) return;
    setDeleting(true);
    try {
      await apiClient.delete(API_ENDPOINTS.orderDetail(id));
      show('Order deleted.', 'success');
      navigate('/orders');
    } catch {
      show('Delete failed.', 'error');
      setDeleting(false);
    }
  }

  async function handleDownloadInvoice() {
    if (!id) return;
    setDownloadingInvoice(true);
    try {
      const res = await apiClient.get(API_ENDPOINTS.orderInvoice(id), { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `Invoice_${id}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      show('Failed to generate invoice.', 'error');
    } finally {
      setDownloadingInvoice(false);
    }
  }

  if (loading) return <Card>Loading…</Card>;
  if (!order) return <Card>Order not found.</Card>;

  if (isCustomer) {
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24 }}>{order.customer_name}</h1>
            <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>Placed on {order.order_date}</span>
          </div>
          <StatusBadge status={order.status} />
        </div>

        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
            <div><div style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Warehouse</div><div style={{ fontSize: 15, marginTop: 2 }}>{order.warehouse?.name ?? '—'}</div></div>
            <div><div style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Payment Status</div><div style={{ fontSize: 15, marginTop: 2 }}>{order.payment_status}</div></div>
            <div><div style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Total</div><div style={{ fontSize: 15, marginTop: 2 }}>₹{order.total_amount.toFixed(2)}</div></div>
            <div><div style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Delivery Address</div><div style={{ fontSize: 15, marginTop: 2 }}>{order.delivery_address}</div></div>
          </div>
        </Card>

        <Card>
          <h3 style={{ marginTop: 0, fontSize: 16 }}>Line items</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)', fontSize: 12 }}>
                <th style={{ padding: 8 }}>Product</th>
                <th style={{ padding: 8 }}>Quantity</th>
                <th style={{ padding: 8 }}>UOM</th>
                <th style={{ padding: 8 }}>Price</th>
                <th style={{ padding: 8 }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item, i) => (
                <tr key={i} style={{ borderTop: '1px solid var(--color-border)' }}>
                  <td style={{ padding: 8 }}>{item.product_name}</td>
                  <td style={{ padding: 8 }}>{item.quantity}</td>
                  <td style={{ padding: 8 }}>{item.uom}</td>
                  <td style={{ padding: 8 }}>₹{item.price.toFixed(2)}</td>
                  <td style={{ padding: 8 }}>₹{item.line_total.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
          <Button variant="secondary" onClick={() => navigate('/orders')}>Back to my orders</Button>
          <Button variant="secondary" loading={downloadingInvoice} onClick={handleDownloadInvoice}>Download Invoice</Button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24 }}>{order.customer_name}</h1>
          <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>Placed by {order.created_by} on {order.order_date}</span>
        </div>
        <StatusBadge status={order.status} />
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            <Input label="Customer Name" {...register('customer_name', { required: true })} />
            <Select label="Warehouse" {...register('warehouse', { required: true })}>
              {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </Select>
            <Select label="Status" {...register('status')}>
              {ORDER_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </Select>
            <Select label="Payment Status" {...register('payment_status')}>
              {PAYMENT_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <div style={{ marginTop: 16 }}>
            <Input label="Delivery Address" {...register('delivery_address', { required: true })} />
          </div>
        </Card>

        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: 16 }}>Line items</h3>
            <Button type="button" variant="secondary" onClick={() => append({ product: '', quantity: 1, price: 0, uom: '' })}>+ Add row</Button>
          </div>
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
                      >
                        <option value="">Select…</option>
                        {productsInWarehouse.map(({ product: p }) => <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>)}
                      </select>
                    </td>
                    <td style={{ padding: 8 }}><input type="number" min={1} {...register(`items.${index}.quantity` as const, { valueAsNumber: true })} style={{ width: 90, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} /></td>
                    <td style={{ padding: 8 }}><input type="number" min={0} step="0.01" {...register(`items.${index}.price` as const, { valueAsNumber: true })} style={{ width: 100, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} /></td>
                    <td style={{ padding: 8 }}><input {...register(`items.${index}.uom` as const)} style={{ width: 70, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} /></td>
                    <td style={{ padding: 8 }}>{fields.length > 1 && <button type="button" onClick={() => remove(index)} style={{ background: 'none', border: 'none', color: 'var(--color-danger)', cursor: 'pointer' }}>✕</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16, fontSize: 18, fontWeight: 700 }}>Total: ₹{total.toFixed(2)}</div>
        </Card>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
          <div style={{ display: 'flex', gap: 12 }}>
            <Button type="button" variant="secondary" onClick={() => navigate('/orders')}>Back</Button>
            <Button type="button" variant="secondary" loading={downloadingInvoice} onClick={handleDownloadInvoice}>Download Invoice</Button>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <Button type="button" variant="danger" onClick={() => setDeleteOpen(true)}>Delete</Button>
            <Button type="submit" loading={submitting}>Save Changes</Button>
          </div>
        </div>
      </form>

      <Modal
        open={deleteOpen}
        title="Delete order?"
        onClose={() => setDeleteOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setDeleteOpen(false)}>Cancel</Button><Button variant="danger" loading={deleting} onClick={handleDelete}>Delete</Button></>}
      >
        This cannot be undone.
      </Modal>
    </div>
  );
}
