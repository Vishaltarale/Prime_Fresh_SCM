import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { Grn } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { StatusBadge } from '../../components/StatusBadge';
import { Modal } from '../../components/Modal';
import { useToast } from '../../components/Toast';
import { useAuth } from '../../context/AuthContext';

export function GrnDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { show } = useToast();
  const { user } = useAuth();
  const canAct = user?.role === 'Admin' || user?.role === 'Inventory Officer' || user?.role === 'Warehouse Manager';
  const [grn, setGrn] = useState<Grn | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirmAction, setConfirmAction] = useState<'confirm' | 'reject' | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!id) return;
    apiClient.get<Grn>(API_ENDPOINTS.grnDetail(id))
      .then((res) => setGrn(res.data))
      .catch(() => show('GRN not found.', 'error'))
      .finally(() => setLoading(false));
  }, [id, show]);

  async function handleAction() {
    if (!id || !confirmAction) return;
    setSubmitting(true);
    try {
      const endpoint = confirmAction === 'confirm' ? API_ENDPOINTS.grnConfirm(id) : API_ENDPOINTS.grnReject(id);
      const res = await apiClient.post<Grn>(endpoint);
      setGrn(res.data);
      show(`GRN ${confirmAction === 'confirm' ? 'confirmed' : 'rejected'}.`, 'success');
    } catch {
      show('Action failed.', 'error');
    } finally {
      setSubmitting(false);
      setConfirmAction(null);
    }
  }

  if (loading) return <Card>Loading…</Card>;
  if (!grn) return <Card>GRN not found.</Card>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24 }}>{grn.grn_number}</h1>
          <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
            Received by {grn.received_by} on {new Date(grn.created_at).toLocaleString()}
          </span>
        </div>
        <StatusBadge status={grn.status} />
      </div>

      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
          <Field label="Source" value={grn.source_type === 'Supplier' ? grn.supplier?.name : grn.farmer?.name} />
          {grn.purchase_order && <Field label="Purchase Order" value={grn.purchase_order.po_number} />}
          <Field label="Warehouse" value={grn.warehouse.name} />
          <Field label="Total Amount" value={`₹${grn.total_amount.toFixed(2)}`} />
          <Field label="Notes" value={grn.notes || '—'} />
        </div>
      </Card>

      <Card>
        <h3 style={{ marginTop: 0, fontSize: 16 }}>Line items</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)', fontSize: 12 }}>
              <th style={{ padding: 8 }}>Product</th>
              <th style={{ padding: 8 }}>Ordered</th>
              <th style={{ padding: 8 }}>Received</th>
              <th style={{ padding: 8 }}>Loss</th>
              <th style={{ padding: 8 }}>Loss Reason</th>
              <th style={{ padding: 8 }}>Unit Price</th>
              <th style={{ padding: 8 }}>UOM</th>
              <th style={{ padding: 8 }}>Line Total</th>
            </tr>
          </thead>
          <tbody>
            {grn.items.map((item, i) => (
              <tr key={i} style={{ borderTop: '1px solid var(--color-border)' }}>
                <td style={{ padding: 8 }}>{item.product_name}</td>
                <td style={{ padding: 8 }}>{item.ordered_qty}</td>
                <td style={{ padding: 8 }}>{item.received_qty}</td>
                <td style={{ padding: 8 }}>{item.loss_qty ?? 0}</td>
                <td style={{ padding: 8 }}>{item.loss_reason || '—'}</td>
                <td style={{ padding: 8 }}>₹{item.unit_price.toFixed(2)}</td>
                <td style={{ padding: 8 }}>{item.uom}</td>
                <td style={{ padding: 8 }}>₹{(item.line_total ?? item.received_qty * item.unit_price).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
        <Button variant="secondary" onClick={() => navigate('/grn')}>Back to list</Button>
        {canAct && grn.status === 'Draft' && (
          <div style={{ display: 'flex', gap: 12 }}>
            <Button variant="danger" onClick={() => setConfirmAction('reject')}>Reject</Button>
            <Button onClick={() => setConfirmAction('confirm')}>Confirm</Button>
          </div>
        )}
      </div>

      <Modal
        open={confirmAction !== null}
        title={confirmAction === 'confirm' ? 'Confirm GRN?' : 'Reject GRN?'}
        onClose={() => setConfirmAction(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirmAction(null)}>Cancel</Button>
            <Button variant={confirmAction === 'reject' ? 'danger' : 'primary'} loading={submitting} onClick={handleAction}>
              Yes, {confirmAction}
            </Button>
          </>
        }
      >
        {confirmAction === 'confirm'
          ? 'This will add the received quantities to warehouse stock. This cannot be undone from here.'
          : 'This will mark the GRN as rejected. This cannot be undone from here.'}
      </Modal>
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: 15, marginTop: 2 }}>{value ?? '—'}</div>
    </div>
  );
}
