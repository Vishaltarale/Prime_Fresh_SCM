import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import type { NamedRef, ProductRef, GrnCreateInput, PoConfirmedForGrn } from '@shared/types';
import { API_ENDPOINTS, LOSS_REASONS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Input, Select } from '../../components/Input';
import { Button } from '../../components/Button';
import { useToast } from '../../components/Toast';

interface FormValues extends GrnCreateInput {}

export function GrnCreatePage() {
  const navigate = useNavigate();
  const { show } = useToast();
  const [warehouses, setWarehouses] = useState<NamedRef[]>([]);
  const [farmers, setFarmers] = useState<NamedRef[]>([]);
  const [products, setProducts] = useState<ProductRef[]>([]);
  const [confirmedPOs, setConfirmedPOs] = useState<PoConfirmedForGrn[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const { register, control, handleSubmit, watch, setValue, formState: { errors } } = useForm<FormValues>({
    defaultValues: {
      source_type: 'Supplier',
      warehouse: '',
      purchase_order: '',
      notes: '',
      items: [],
    },
  });
  const { fields, append, remove, replace } = useFieldArray({ control, name: 'items' });
  const sourceType = watch('source_type');
  const selectedPoId = watch('purchase_order');
  const items = watch('items');

  useEffect(() => {
    Promise.all([
      apiClient.get<NamedRef[]>(API_ENDPOINTS.warehouses),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.farmers),
      apiClient.get<ProductRef[]>(API_ENDPOINTS.products),
      apiClient.get<PoConfirmedForGrn[]>(API_ENDPOINTS.poConfirmedForGrn),
    ]).then(([w, f, p, po]) => {
      setWarehouses(w.data);
      setFarmers(f.data);
      setProducts(p.data);
      setConfirmedPOs(po.data);
    }).finally(() => setLoadingLookups(false));
  }, []);

  // Switching source type resets the item rows — the two flows populate them very differently.
  useEffect(() => {
    replace([]);
    setValue('purchase_order', '');
    if (sourceType === 'Farmer') {
      replace([{ product: '', ordered_qty: 0, received_qty: 0, loss_qty: 0, loss_reason: '', unit_price: 0, uom: '', remarks: '' }]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceType]);

  function pickPurchaseOrder(poId: string) {
    const po = confirmedPOs.find((p) => p.id === poId);
    if (!po) {
      replace([]);
      return;
    }
    setValue('warehouse', po.warehouse.id);
    replace(po.items.map((item) => ({
      product: item.product,
      ordered_qty: item.remaining_qty,
      received_qty: item.remaining_qty,
      loss_qty: 0,
      loss_reason: '',
      unit_price: item.confirmed_price ?? 0,
      uom: '',
      remarks: '',
    })));
  }

  const total = (items ?? []).reduce((sum, item) => sum + (Number(item.received_qty) || 0) * (Number(item.unit_price) || 0), 0);

  async function onSubmit(values: FormValues) {
    setSubmitting(true);
    try {
      const payload = sourceType === 'Supplier' ? values : { ...values, purchase_order: undefined };
      const res = await apiClient.post(API_ENDPOINTS.grnList, payload);
      show('GRN created', 'success');
      navigate(`/grn/${res.data.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      show(msg ? Object.values(msg).join(' ') : 'Failed to create GRN — check the form for errors.', 'error');
    } finally {
      setSubmitting(false);
    }
  }

  function productAutofill(index: number, productId: string) {
    const product = products.find((p) => p.id === productId);
    if (!product) return;
    const el = document.querySelectorAll<HTMLInputElement>(`[data-item="${index}"][data-field="unit_price"]`)[0];
    if (el) el.value = String(product.price_per_unit);
  }

  function productName(productId: string) {
    return products.find((p) => p.id === productId)?.name ?? productId;
  }

  if (loadingLookups) return <Card>Loading form…</Card>;

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 20 }}>New Goods Receipt Note</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            <Select label="Source type" {...register('source_type')}>
              <option value="Supplier">Supplier</option>
              <option value="Farmer">Farmer</option>
            </Select>

            {sourceType === 'Supplier' ? (
              <Select
                label="Confirmed Purchase Order"
                value={selectedPoId}
                {...register('purchase_order', { required: sourceType === 'Supplier', onChange: (e) => pickPurchaseOrder(e.target.value) })}
                error={errors.purchase_order ? 'Required' : undefined}
              >
                <option value="">Select a confirmed PO…</option>
                {confirmedPOs.map((po) => <option key={po.id} value={po.id}>{po.po_number} — {po.supplier.name}</option>)}
              </Select>
            ) : (
              <Select label="Farmer" {...register('farmer', { required: sourceType === 'Farmer' })} error={errors.farmer ? 'Required' : undefined}>
                <option value="">Select farmer…</option>
                {farmers.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
              </Select>
            )}

            <Select label="Warehouse" disabled={sourceType === 'Supplier'} {...register('warehouse', { required: true })} error={errors.warehouse ? 'Required' : undefined}>
              <option value="">Select warehouse…</option>
              {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </Select>
          </div>
          {sourceType === 'Supplier' && confirmedPOs.length === 0 && (
            <p style={{ marginTop: 12, fontSize: 13, color: 'var(--color-warning)' }}>
              No Confirmed Purchase Orders with remaining quantity are available. Create and confirm a PO first.
            </p>
          )}
          <div style={{ marginTop: 16 }}>
            <Input label="Notes" {...register('notes')} />
          </div>
        </Card>

        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: 16 }}>Line items</h3>
            {sourceType === 'Farmer' && (
              <Button type="button" variant="secondary" onClick={() => append({ product: '', ordered_qty: 0, received_qty: 0, loss_qty: 0, loss_reason: '', unit_price: 0, uom: '', remarks: '' })}>
                + Add row
              </Button>
            )}
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)' }}>
                  <th style={{ padding: 8 }}>Product</th>
                  <th style={{ padding: 8 }}>Ordered/Shipped Qty</th>
                  <th style={{ padding: 8 }}>Received Qty</th>
                  <th style={{ padding: 8 }}>Loss Qty</th>
                  <th style={{ padding: 8 }}>Loss Reason</th>
                  <th style={{ padding: 8 }}>Unit Price</th>
                  <th style={{ padding: 8 }}>UOM</th>
                  <th style={{ padding: 8 }}>Remarks</th>
                  {sourceType === 'Farmer' && <th style={{ padding: 8 }} />}
                </tr>
              </thead>
              <tbody>
                {fields.map((field, index) => (
                  <tr key={field.id} style={{ borderTop: '1px solid var(--color-border)' }}>
                    <td style={{ padding: 8 }}>
                      {sourceType === 'Supplier' ? (
                        <span>{productName(items?.[index]?.product ?? '')}</span>
                      ) : (
                        <select
                          {...register(`items.${index}.product` as const, { required: true, onChange: (e) => productAutofill(index, e.target.value) })}
                          style={{ padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }}
                        >
                          <option value="">Select…</option>
                          {products.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>)}
                        </select>
                      )}
                    </td>
                    <td style={{ padding: 8 }}>
                      <input type="number" min={0} {...register(`items.${index}.ordered_qty` as const, { valueAsNumber: true, required: true })} style={{ width: 90, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
                    </td>
                    <td style={{ padding: 8 }}>
                      <input type="number" min={0} {...register(`items.${index}.received_qty` as const, { valueAsNumber: true, required: true })} style={{ width: 90, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
                    </td>
                    <td style={{ padding: 8 }}>
                      <input type="number" min={0} {...register(`items.${index}.loss_qty` as const, { valueAsNumber: true })} style={{ width: 80, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
                    </td>
                    <td style={{ padding: 8 }}>
                      <select {...register(`items.${index}.loss_reason` as const)} style={{ padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }}>
                        {LOSS_REASONS.map((r) => <option key={r} value={r}>{r || '—'}</option>)}
                      </select>
                    </td>
                    <td style={{ padding: 8 }}>
                      <input
                        type="number" min={0} step="0.01"
                        data-item={index} data-field="unit_price"
                        disabled={sourceType === 'Supplier'}
                        {...register(`items.${index}.unit_price` as const, { valueAsNumber: true, required: true })}
                        style={{ width: 100, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }}
                      />
                    </td>
                    <td style={{ padding: 8 }}>
                      <input {...register(`items.${index}.uom` as const)} style={{ width: 70, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
                    </td>
                    <td style={{ padding: 8 }}>
                      <input {...register(`items.${index}.remarks` as const)} style={{ width: 120, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }} />
                    </td>
                    {sourceType === 'Farmer' && (
                      <td style={{ padding: 8 }}>
                        {fields.length > 1 && (
                          <button type="button" onClick={() => remove(index)} style={{ background: 'none', border: 'none', color: 'var(--color-danger)', cursor: 'pointer' }}>✕</button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
                {fields.length === 0 && (
                  <tr><td colSpan={9} style={{ padding: 16, textAlign: 'center', color: 'var(--color-text-secondary)' }}>Select a Confirmed Purchase Order above to load its items.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16, fontSize: 18, fontWeight: 700 }}>
            Total: ₹{total.toFixed(2)}
          </div>
        </Card>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 20 }}>
          <Button type="button" variant="secondary" onClick={() => navigate('/grn')}>Cancel</Button>
          <Button type="submit" loading={submitting} disabled={fields.length === 0}>Save GRN</Button>
        </div>
      </form>
    </div>
  );
}
