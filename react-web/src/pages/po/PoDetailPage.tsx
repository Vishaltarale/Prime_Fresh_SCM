import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { PurchaseOrder, PoPaymentSummary } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { Input } from '../../components/Input';
import { Modal } from '../../components/Modal';
import { useToast } from '../../components/Toast';
import { PoStatusBadge } from './PoListPage';

export function PoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { show } = useToast();
  const [po, setPo] = useState<PurchaseOrder | null>(null);
  const [payment, setPayment] = useState<PoPaymentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const [rejectOpen, setRejectOpen] = useState(false);
  const [payOpen, setPayOpen] = useState(false);
  const [refundOpen, setRefundOpen] = useState(false);
  const [payAmount, setPayAmount] = useState('');
  const [payMethod, setPayMethod] = useState('');
  const [refundAmount, setRefundAmount] = useState('');
  const [refundReason, setRefundReason] = useState('');

  function load() {
    if (!id) return;
    setLoading(true);
    Promise.all([
      apiClient.get<PurchaseOrder>(API_ENDPOINTS.poDetail(id)),
      apiClient.get<PoPaymentSummary>(API_ENDPOINTS.poPayments(id)).catch(() => null),
    ]).then(([poRes, payRes]) => {
      setPo(poRes.data);
      if (payRes) setPayment(payRes.data);
    }).finally(() => setLoading(false));
  }

  useEffect(load, [id]);

  async function handleSend() {
    if (!id) return;
    setBusy(true);
    try {
      const res = await apiClient.post<PurchaseOrder>(API_ENDPOINTS.poSend(id));
      setPo(res.data);
      show(res.data.email_sent ? 'PO sent to supplier by email.' : `PO marked Sent, but email failed: ${res.data.email_error}`, res.data.email_sent ? 'success' : 'error');
    } catch {
      show('Failed to send PO.', 'error');
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirm() {
    if (!id) return;
    setBusy(true);
    try {
      const res = await apiClient.post<PurchaseOrder>(API_ENDPOINTS.poConfirm(id));
      setPo(res.data);
      show('PO confirmed — now available for GRN receipt.', 'success');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      show(msg ?? 'Failed to confirm PO.', 'error');
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    if (!id) return;
    setBusy(true);
    try {
      const res = await apiClient.post<PurchaseOrder>(API_ENDPOINTS.poReject(id));
      setPo(res.data);
      show('PO rejected.', 'success');
    } catch {
      show('Failed to reject PO.', 'error');
    } finally {
      setBusy(false);
      setRejectOpen(false);
    }
  }

  async function handleRecordPayment() {
    if (!id) return;
    setBusy(true);
    try {
      const res = await apiClient.post<PoPaymentSummary>(API_ENDPOINTS.poPayments(id), { amount: Number(payAmount), method: payMethod });
      setPayment(res.data);
      show('Payment recorded.', 'success');
      setPayOpen(false);
      setPayAmount('');
      setPayMethod('');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { amount?: string } } })?.response?.data?.amount;
      show(msg ?? 'Failed to record payment.', 'error');
    } finally {
      setBusy(false);
    }
  }

  async function handleRecordRefund() {
    if (!id) return;
    setBusy(true);
    try {
      const res = await apiClient.post<PoPaymentSummary>(API_ENDPOINTS.poRefund(id), { amount: Number(refundAmount), reason: refundReason });
      setPayment(res.data);
      show('Refund recorded.', 'success');
      setRefundOpen(false);
      setRefundAmount('');
      setRefundReason('');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { amount?: string; reason?: string } } })?.response?.data;
      show(msg?.amount ?? msg?.reason ?? 'Failed to record refund.', 'error');
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Card>Loading…</Card>;
  if (!po) return <Card>Purchase Order not found.</Card>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24 }}>{po.po_number}</h1>
          <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{po.supplier.name} · {po.warehouse.name}</span>
        </div>
        <PoStatusBadge status={po.status} />
      </div>

      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
          <Field label="Proposed Total" value={`₹${po.proposed_total.toFixed(2)}`} />
          <Field label="Confirmed Total" value={po.status === 'Confirmed' || po.status === 'Rejected' ? `₹${po.confirmed_total.toFixed(2)}` : '—'} />
          <Field label="Received Value (owed)" value={`₹${po.received_total.toFixed(2)}`} />
          <Field label="Created By" value={po.created_by} />
          {po.approved_by && <Field label="Approved/Rejected By" value={po.approved_by} />}
          <Field label="Notes" value={po.notes || '—'} />
        </div>
      </Card>

      <Card>
        <h3 style={{ marginTop: 0, fontSize: 16 }}>Line items</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)' }}>
                <th style={{ padding: 8 }}>Product</th>
                <th style={{ padding: 8 }}>Ordered</th>
                <th style={{ padding: 8 }}>Proposed</th>
                <th style={{ padding: 8 }}>Confirmed</th>
                <th style={{ padding: 8 }}>Received</th>
                <th style={{ padding: 8 }}>Loss</th>
                <th style={{ padding: 8 }}>Remaining</th>
              </tr>
            </thead>
            <tbody>
              {po.items.map((item, i) => (
                <tr key={i} style={{ borderTop: '1px solid var(--color-border)' }}>
                  <td style={{ padding: 8 }}>{item.product_name}</td>
                  <td style={{ padding: 8 }}>{item.ordered_qty}</td>
                  <td style={{ padding: 8 }}>₹{item.proposed_price.toFixed(2)}</td>
                  <td style={{ padding: 8 }}>{item.confirmed_price != null ? `₹${item.confirmed_price.toFixed(2)}` : '—'}</td>
                  <td style={{ padding: 8 }}>{item.received_qty}</td>
                  <td style={{ padding: 8 }}>{item.loss_qty}</td>
                  <td style={{ padding: 8 }}>{item.remaining_qty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
        <Button variant="secondary" onClick={() => navigate('/purchase-orders')}>Back to list</Button>
        <div style={{ display: 'flex', gap: 12 }}>
          {(po.status === 'Draft' || po.status === 'Rejected') && (
            <Button loading={busy} onClick={handleSend}>{po.status === 'Rejected' ? 'Resend to Supplier' : 'Send to Supplier'}</Button>
          )}
          {po.status === 'Awaiting Approval' && (
            <>
              <Button variant="danger" onClick={() => setRejectOpen(true)}>Reject</Button>
              <Button loading={busy} onClick={handleConfirm}>Confirm</Button>
            </>
          )}
        </div>
      </div>

      {po.status === 'Confirmed' && payment && (
        <Card style={{ marginTop: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: 16 }}>Payment Tracking</h3>
            <span style={{ fontSize: 12, fontWeight: 700, padding: '4px 10px', borderRadius: 'var(--radius-pill)', color: payment.status === 'Fully Paid' ? 'var(--color-success)' : payment.status === 'Partially Paid' ? 'var(--color-warning)' : 'var(--color-text-secondary)', background: 'var(--color-bg)' }}>
              {payment.status}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 16, marginBottom: 16 }}>
            <Field label="Total Owed" value={`₹${payment.total_amount.toFixed(2)}`} />
            <Field label="Amount Paid" value={`₹${payment.amount_paid.toFixed(2)}`} />
            <Field label="Balance" value={`₹${payment.balance.toFixed(2)}`} />
          </div>

          <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
            <Button onClick={() => setPayOpen(true)} disabled={payment.balance <= 0}>Record Payment</Button>
            <Button variant="secondary" onClick={() => setRefundOpen(true)} disabled={payment.amount_paid <= 0}>Record Refund</Button>
          </div>

          <h4 style={{ fontSize: 14, marginBottom: 8 }}>History</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)' }}>
                <th style={{ padding: 8 }}>Type</th>
                <th style={{ padding: 8 }}>Amount</th>
                <th style={{ padding: 8 }}>Method / Reason</th>
                <th style={{ padding: 8 }}>By</th>
                <th style={{ padding: 8 }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {payment.history.length === 0 ? (
                <tr><td colSpan={5} style={{ padding: 16, textAlign: 'center', color: 'var(--color-text-secondary)' }}>No payments recorded yet.</td></tr>
              ) : payment.history.map((h, i) => (
                <tr key={i} style={{ borderTop: '1px solid var(--color-border)' }}>
                  <td style={{ padding: 8, color: h.kind === 'Refund' ? 'var(--color-danger)' : 'var(--color-success)', fontWeight: 600 }}>{h.kind}</td>
                  <td style={{ padding: 8 }}>₹{h.amount.toFixed(2)}</td>
                  <td style={{ padding: 8 }}>{h.method || h.reason || '—'}</td>
                  <td style={{ padding: 8 }}>{h.recorded_by}</td>
                  <td style={{ padding: 8 }}>{new Date(h.date).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <Modal open={rejectOpen} title="Reject PO?" onClose={() => setRejectOpen(false)} footer={<><Button variant="secondary" onClick={() => setRejectOpen(false)}>Cancel</Button><Button variant="danger" loading={busy} onClick={handleReject}>Reject</Button></>}>
        This can be re-sent to the supplier later if needed.
      </Modal>

      <Modal
        open={payOpen}
        title="Record Payment"
        onClose={() => setPayOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setPayOpen(false)}>Cancel</Button><Button loading={busy} onClick={handleRecordPayment}>Save Payment</Button></>}
      >
        {payment && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, fontSize: 13 }}>
              <div><div style={{ color: 'var(--color-text-secondary)' }}>Total</div><strong>₹{payment.total_amount.toFixed(2)}</strong></div>
              <div><div style={{ color: 'var(--color-text-secondary)' }}>Already Paid</div><strong>₹{payment.amount_paid.toFixed(2)}</strong></div>
              <div><div style={{ color: 'var(--color-text-secondary)' }}>Balance</div><strong>₹{payment.balance.toFixed(2)}</strong></div>
            </div>
            <Input label="Current Payment" type="number" min={0} max={payment.balance} step="0.01" value={payAmount} onChange={(e) => setPayAmount(e.target.value)} />
            <Input label="Method / Reference (optional)" value={payMethod} onChange={(e) => setPayMethod(e.target.value)} />
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
              Balance after this payment: ₹{Math.max(payment.balance - (Number(payAmount) || 0), 0).toFixed(2)}
            </div>
          </div>
        )}
      </Modal>

      <Modal
        open={refundOpen}
        title="Record Refund"
        onClose={() => setRefundOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setRefundOpen(false)}>Cancel</Button><Button variant="danger" loading={busy} onClick={handleRecordRefund}>Save Refund</Button></>}
      >
        {payment && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>Amount paid so far: ₹{payment.amount_paid.toFixed(2)}</div>
            <Input label="Refund Amount" type="number" min={0} max={payment.amount_paid} step="0.01" value={refundAmount} onChange={(e) => setRefundAmount(e.target.value)} />
            <Input label="Reason" required value={refundReason} onChange={(e) => setRefundReason(e.target.value)} />
          </div>
        )}
      </Modal>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: 15, marginTop: 2 }}>{value}</div>
    </div>
  );
}
