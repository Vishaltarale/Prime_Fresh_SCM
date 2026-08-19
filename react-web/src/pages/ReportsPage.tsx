import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { PurchaseOrder, ReportData, WarehouseStockDetail } from '@shared/types';
import { API_ENDPOINTS, REPORT_NAV } from '@shared/constants';
import { apiClient } from '../lib/apiClient';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Modal } from '../components/Modal';
import { StatusBadge } from '../components/StatusBadge';
import { useToast } from '../components/Toast';

function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function PoDetailModal({ poId, onClose }: { poId: string; onClose: () => void }) {
  const [po, setPo] = useState<PurchaseOrder | null>(null);

  useEffect(() => {
    apiClient.get<PurchaseOrder>(API_ENDPOINTS.poDetail(poId)).then((res) => setPo(res.data));
  }, [poId]);

  return (
    <Modal open title={po ? po.po_number : 'Loading…'} onClose={onClose}>
      {!po ? (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>Loading order details…</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Supplier</div>
              <div style={{ fontWeight: 600 }}>{po.supplier.name}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Warehouse</div>
              <div style={{ fontWeight: 600 }}>{po.warehouse.name}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Status</div>
              <StatusBadge status={po.status} />
            </div>
          </div>

          <div>
            <h4 style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Products</h4>
            <div style={{ overflowX: 'auto', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--color-bg)' }}>
                    <th style={{ textAlign: 'left', padding: 10 }}>Product</th>
                    <th style={{ textAlign: 'right', padding: 10 }}>Ordered</th>
                    <th style={{ textAlign: 'right', padding: 10 }}>Received</th>
                    <th style={{ textAlign: 'right', padding: 10 }}>Price</th>
                    <th style={{ textAlign: 'right', padding: 10 }}>Line Total</th>
                  </tr>
                </thead>
                <tbody>
                  {po.items.map((item, i) => (
                    <tr key={i} className="row-hover" style={{ borderTop: '1px solid var(--color-border)' }}>
                      <td style={{ padding: 10 }}>{item.product_name}</td>
                      <td style={{ padding: 10, textAlign: 'right' }}>{item.ordered_qty}</td>
                      <td style={{ padding: 10, textAlign: 'right' }}>{item.received_qty}</td>
                      <td style={{ padding: 10, textAlign: 'right' }}>₹{(item.confirmed_price ?? item.proposed_price).toFixed(2)}</td>
                      <td style={{ padding: 10, textAlign: 'right', fontWeight: 600 }}>₹{item.line_total_received.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 24, fontSize: 14, paddingTop: 4, borderTop: '1px solid var(--color-border)' }}>
            <span>Proposed: <strong>₹{po.proposed_total.toFixed(2)}</strong></span>
            <span>Confirmed: <strong>₹{po.confirmed_total.toFixed(2)}</strong></span>
            <span>Received: <strong style={{ color: 'var(--color-success)' }}>₹{po.received_total.toFixed(2)}</strong></span>
          </div>
        </div>
      )}
    </Modal>
  );
}

function WarehouseStockModal({ warehouseId, onClose }: { warehouseId: string; onClose: () => void }) {
  const [detail, setDetail] = useState<WarehouseStockDetail | null>(null);

  useEffect(() => {
    apiClient.get<WarehouseStockDetail>(API_ENDPOINTS.warehouseStockDetail(warehouseId)).then((res) => setDetail(res.data));
  }, [warehouseId]);

  const lowCount = detail?.items.filter((i) => i.is_low).length ?? 0;

  return (
    <Modal open title={detail ? `${detail.warehouse.name} — Stock` : 'Loading…'} onClose={onClose}>
      {!detail ? (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>Loading warehouse stock…</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>City</div>
              <div style={{ fontWeight: 600 }}>{detail.warehouse.city}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Low-stock threshold</div>
              <div style={{ fontWeight: 600 }}>≤ {detail.threshold} units</div>
            </div>
            {lowCount > 0 && (
              <div>
                <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Alerts</div>
                <div style={{ fontWeight: 700, color: 'var(--color-danger)' }}>{lowCount} product{lowCount === 1 ? '' : 's'} low</div>
              </div>
            )}
          </div>

          <div style={{ overflowX: 'auto', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', maxHeight: 360, overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: 'var(--color-bg)' }}>
                  <th style={{ textAlign: 'left', padding: 10 }}>Product</th>
                  <th style={{ textAlign: 'left', padding: 10 }}>SKU</th>
                  <th style={{ textAlign: 'right', padding: 10 }}>Qty Available</th>
                  <th style={{ textAlign: 'right', padding: 10 }}>Unit Price</th>
                  <th style={{ textAlign: 'left', padding: 10 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {detail.items.length === 0 ? (
                  <tr><td colSpan={5} style={{ padding: 24, textAlign: 'center', color: 'var(--color-text-secondary)' }}>No stock in this warehouse yet.</td></tr>
                ) : detail.items.map((item) => (
                  <tr key={item.sku} className="row-hover" style={{ borderTop: '1px solid var(--color-border)' }}>
                    <td style={{ padding: 10 }}>{item.product}</td>
                    <td style={{ padding: 10, color: 'var(--color-text-secondary)' }}>{item.sku}</td>
                    <td style={{ padding: 10, textAlign: 'right', fontWeight: item.is_low ? 700 : 400 }}>{item.quantity_available}</td>
                    <td style={{ padding: 10, textAlign: 'right' }}>₹{item.price_per_unit.toFixed(2)}</td>
                    <td style={{ padding: 10 }}>
                      {item.is_low ? (
                        <span style={{ color: 'var(--color-danger)', fontWeight: 700, fontSize: 12 }}>⚠ Low stock</span>
                      ) : (
                        <span style={{ color: 'var(--color-success)', fontSize: 12 }}>OK</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Modal>
  );
}

export function ReportsPage() {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const { show } = useToast();
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [threshold, setThreshold] = useState('10');
  const [exporting, setExporting] = useState<'pdf' | 'excel' | 'preview' | null>(null);
  const [activePoId, setActivePoId] = useState<string | null>(null);
  const [activeWarehouseId, setActiveWarehouseId] = useState<string | null>(null);

  const reportType = type ?? 'inventory';

  useEffect(() => {
    setLoading(true);
    const params = reportType === 'low-stock' ? { threshold } : undefined;
    apiClient.get<ReportData>(API_ENDPOINTS.report(reportType), { params })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [reportType, threshold]);

  async function handleExport(format: 'pdf' | 'excel') {
    setExporting(format);
    try {
      const endpoint = format === 'pdf' ? API_ENDPOINTS.reportExportPdf(reportType) : API_ENDPOINTS.reportExportExcel(reportType);
      const params = reportType === 'low-stock' ? { threshold } : undefined;
      const res = await apiClient.get(endpoint, { params, responseType: 'blob' });
      const ext = format === 'pdf' ? 'pdf' : 'xlsx';
      downloadBlob(res.data, `${reportType}_report.${ext}`);
    } catch {
      show('Export failed.', 'error');
    } finally {
      setExporting(null);
    }
  }

  async function handlePreview() {
    setExporting('preview');
    try {
      const params = { ...(reportType === 'low-stock' ? { threshold } : {}), preview: 1 };
      const res = await apiClient.get(API_ENDPOINTS.reportExportPdf(reportType), { params, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      window.open(url, '_blank');
    } catch {
      show('Preview failed.', 'error');
    } finally {
      setExporting(null);
    }
  }

  const clickable = Boolean(data?.row_meta);

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Reports</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {REPORT_NAV.map((r) => (
          <Button
            key={r.type}
            variant={r.type === reportType ? 'primary' : 'secondary'}
            onClick={() => navigate(`/reports/${r.type}`)}
          >
            {r.icon} {r.label}
          </Button>
        ))}
      </div>

      {reportType === 'low-stock' && (
        <div style={{ marginBottom: 16, maxWidth: 200 }}>
          <Input label="Threshold" type="number" value={threshold} onChange={(e) => setThreshold(e.target.value)} />
        </div>
      )}

      {loading ? (
        <Card>Loading…</Card>
      ) : data ? (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h2 style={{ margin: 0, fontSize: 18 }}>{data.title}</h2>
              {data.summary && <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: 14 }}>{data.summary}</p>}
              {clickable && <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: 12 }}>Click a row for details.</p>}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button variant="secondary" loading={exporting === 'preview'} onClick={handlePreview}>👁 Preview PDF</Button>
              <Button variant="secondary" loading={exporting === 'pdf'} onClick={() => handleExport('pdf')}>Export PDF</Button>
              <Button variant="secondary" loading={exporting === 'excel'} onClick={() => handleExport('excel')}>Export Excel</Button>
            </div>
          </div>

          <Card style={{ padding: 0, overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr>
                  {data.headers.map((h) => (
                    <th key={h} style={{ textAlign: 'left', padding: 12, background: 'var(--color-bg)', color: 'var(--color-text-secondary)', fontSize: 12, textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.length === 0 ? (
                  <tr><td colSpan={data.headers.length} style={{ padding: 32, textAlign: 'center', color: 'var(--color-text-secondary)' }}>No data for this report.</td></tr>
                ) : data.rows.map((row, i) => {
                  const meta = data.row_meta?.[i];
                  const poId = meta && 'po_id' in meta ? meta.po_id : undefined;
                  const warehouseId = meta && 'warehouse_id' in meta ? meta.warehouse_id : undefined;
                  const onClick = poId ? () => setActivePoId(poId) : warehouseId ? () => setActiveWarehouseId(warehouseId) : undefined;
                  return (
                    <tr
                      key={i}
                      className="row-hover"
                      onClick={onClick}
                      style={{ borderTop: '1px solid var(--color-border)', cursor: onClick ? 'pointer' : 'default' }}
                    >
                      {row.map((cell, j) => <td key={j} style={{ padding: 12 }}>{String(cell)}</td>)}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </>
      ) : null}

      {activePoId && <PoDetailModal poId={activePoId} onClose={() => setActivePoId(null)} />}
      {activeWarehouseId && <WarehouseStockModal warehouseId={activeWarehouseId} onClose={() => setActiveWarehouseId(null)} />}
    </div>
  );
}
