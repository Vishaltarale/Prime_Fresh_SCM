import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import type { PurchaseOrder } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const publicClient = axios.create({ baseURL });

export function PoPublicResponsePage() {
  const { token } = useParams<{ token: string }>();
  const [po, setPo] = useState<PurchaseOrder | null>(null);
  const [prices, setPrices] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!token) return;
    publicClient.get<PurchaseOrder>(API_ENDPOINTS.poPublic(token))
      .then((res) => {
        setPo(res.data);
        setPrices(Object.fromEntries(res.data.items.map((i) => [i.product, i.confirmed_price != null ? String(i.confirmed_price) : String(i.proposed_price)])));
      })
      .catch(() => setError('This purchase order link is invalid or no longer active.'))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleSubmit() {
    if (!token || !po) return;
    setSubmitting(true);
    setError('');
    try {
      const items = po.items.map((i) => ({ product: i.product, confirmed_price: Number(prices[i.product]) }));
      await publicClient.post(API_ENDPOINTS.poPublic(token), { items });
      setSubmitted(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { items?: string } } })?.response?.data?.items;
      setError(msg ?? 'Failed to submit pricing. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-bg)', padding: 24, display: 'flex', justifyContent: 'center' }}>
      <div style={{ width: '100%', maxWidth: 720 }}>
        <h1 style={{ fontSize: 22, marginBottom: 4 }}>Purchase Order Review</h1>
        <p style={{ color: 'var(--color-text-secondary)', marginTop: 0, marginBottom: 20, fontSize: 14 }}>
          Prime Fresh SCM — please review the items below and confirm your pricing.
        </p>

        {loading ? (
          <Card>Loading…</Card>
        ) : error && !po ? (
          <Card>{error}</Card>
        ) : submitted ? (
          <Card>
            <h3 style={{ marginTop: 0 }}>Thank you!</h3>
            <p style={{ color: 'var(--color-text-secondary)' }}>Your pricing has been submitted and is now awaiting internal approval. You'll be notified once it's confirmed.</p>
          </Card>
        ) : po ? (
          <>
            <Card style={{ marginBottom: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, fontSize: 14 }}>
                <div><div style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>PO Number</div><strong>{po.po_number}</strong></div>
                <div><div style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>Warehouse</div><strong>{po.warehouse.name}</strong></div>
                <div><div style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>Proposed Total</div><strong>₹{po.proposed_total.toFixed(2)}</strong></div>
              </div>
            </Card>

            <Card>
              <h3 style={{ marginTop: 0, fontSize: 16 }}>Confirm your pricing per item</h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)' }}>
                      <th style={{ padding: 8 }}>Product</th>
                      <th style={{ padding: 8 }}>Ordered Qty</th>
                      <th style={{ padding: 8 }}>Proposed Price</th>
                      <th style={{ padding: 8 }}>Your Fixed Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {po.items.map((item) => (
                      <tr key={item.product} style={{ borderTop: '1px solid var(--color-border)' }}>
                        <td style={{ padding: 8 }}>{item.product_name}</td>
                        <td style={{ padding: 8 }}>{item.ordered_qty}</td>
                        <td style={{ padding: 8 }}>₹{item.proposed_price.toFixed(2)}</td>
                        <td style={{ padding: 8 }}>
                          <input
                            type="number" min={0} step="0.01"
                            value={prices[item.product] ?? ''}
                            onChange={(e) => setPrices((p) => ({ ...p, [item.product]: e.target.value }))}
                            style={{ width: 120, padding: 8, borderRadius: 6, border: '1px solid var(--color-border)' }}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {error && <p style={{ color: 'var(--color-danger)', fontSize: 13, marginTop: 12 }}>{error}</p>}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
                <Button loading={submitting} onClick={handleSubmit}>Submit Fixed Pricing</Button>
              </div>
            </Card>
          </>
        ) : null}
      </div>
    </div>
  );
}
