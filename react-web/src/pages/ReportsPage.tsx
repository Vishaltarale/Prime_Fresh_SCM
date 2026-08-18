import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { ReportData } from '@shared/types';
import { API_ENDPOINTS, REPORT_NAV } from '@shared/constants';
import { apiClient } from '../lib/apiClient';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
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

export function ReportsPage() {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const { show } = useToast();
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [threshold, setThreshold] = useState('10');
  const [exporting, setExporting] = useState<'pdf' | 'excel' | null>(null);

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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <h2 style={{ margin: 0, fontSize: 18 }}>{data.title}</h2>
              {data.summary && <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: 14 }}>{data.summary}</p>}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
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
                ) : data.rows.map((row, i) => (
                  <tr key={i} style={{ borderTop: '1px solid var(--color-border)' }}>
                    {row.map((cell, j) => <td key={j} style={{ padding: 12 }}>{String(cell)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      ) : null}
    </div>
  );
}
