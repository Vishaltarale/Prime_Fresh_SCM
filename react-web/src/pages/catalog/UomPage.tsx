import { useEffect, useState } from 'react';
import type { UomRecord, Conversion, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { Input, Select } from '../../components/Input';
import { useToast } from '../../components/Toast';

export function UomPage() {
  const { show } = useToast();
  const [uoms, setUoms] = useState<UomRecord[]>([]);
  const [conversions, setConversions] = useState<Conversion[]>([]);

  const [uomName, setUomName] = useState('');
  const [uomDesc, setUomDesc] = useState('');
  const [uomError, setUomError] = useState('');
  const [uomSubmitting, setUomSubmitting] = useState(false);

  const [fromUom, setFromUom] = useState('');
  const [toUom, setToUom] = useState('');
  const [factor, setFactor] = useState('');
  const [convErrors, setConvErrors] = useState<Record<string, string>>({});
  const [convSubmitting, setConvSubmitting] = useState(false);

  function reloadUoms() {
    apiClient.get<Paginated<UomRecord>>(API_ENDPOINTS.catalogUom, { params: { page_size: 100 } })
      .then((res) => setUoms(res.data.results));
  }
  function reloadConversions() {
    apiClient.get<Paginated<Conversion>>(API_ENDPOINTS.conversions, { params: { page_size: 100 } })
      .then((res) => setConversions(res.data.results));
  }

  useEffect(() => { reloadUoms(); reloadConversions(); }, []);

  async function handleCreateUom() {
    setUomError('');
    setUomSubmitting(true);
    try {
      await apiClient.post(API_ENDPOINTS.catalogUom, { name: uomName, description: uomDesc });
      show('UOM created.', 'success');
      setUomName('');
      setUomDesc('');
      reloadUoms();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { name?: string } } })?.response?.data?.name;
      setUomError(msg ?? 'Failed to create UOM.');
    } finally {
      setUomSubmitting(false);
    }
  }

  async function handleDeleteUom(uom: UomRecord) {
    try {
      await apiClient.delete(API_ENDPOINTS.catalogUomDetail(uom.id));
      show('UOM deleted.', 'success');
      reloadUoms();
      reloadConversions();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      show(msg ?? 'Delete failed — it may still be used by products.', 'error');
    }
  }

  async function handleSaveConversion() {
    setConvErrors({});
    setConvSubmitting(true);
    try {
      await apiClient.post(API_ENDPOINTS.conversions, { from_uom: fromUom, to_uom: toUom, factor: Number(factor) });
      show('Conversion saved.', 'success');
      setFromUom('');
      setToUom('');
      setFactor('');
      reloadConversions();
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      setConvErrors(respData ?? { factor: 'Failed to save conversion.' });
    } finally {
      setConvSubmitting(false);
    }
  }

  async function handleDeleteConversion(conversion: Conversion) {
    await apiClient.delete(API_ENDPOINTS.conversionDetail(conversion.id));
    show('Conversion removed.', 'success');
    reloadConversions();
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 24, marginBottom: 16 }}>Units of Measurement</h1>
        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <Input label="Name" placeholder="e.g. KG" value={uomName} onChange={(e) => setUomName(e.target.value)} />
            <Input label="Description" value={uomDesc} onChange={(e) => setUomDesc(e.target.value)} />
            <Button loading={uomSubmitting} onClick={handleCreateUom}>+ Add UOM</Button>
          </div>
          {uomError && <p style={{ color: 'var(--color-danger)', fontSize: 13, marginTop: 8 }}>{uomError}</p>}
        </Card>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
          {uoms.map((u) => (
            <Card key={u.id} style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: 10, padding: '10px 14px' }}>
              <strong>{u.name}</strong>
              <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{u.description}</span>
              <Button variant="danger" onClick={() => handleDeleteUom(u)}>✕</Button>
            </Card>
          ))}
          {uoms.length === 0 && <span style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>No units yet.</span>}
        </div>
      </div>

      <div>
        <h2 style={{ fontSize: 20, marginBottom: 16 }}>Conversion Matrix</h2>
        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <Select label="From" value={fromUom} onChange={(e) => setFromUom(e.target.value)} error={convErrors.from_uom}>
              <option value="">Select…</option>
              {uoms.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
            </Select>
            <Select label="To" value={toUom} onChange={(e) => setToUom(e.target.value)} error={convErrors.to_uom}>
              <option value="">Select…</option>
              {uoms.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
            </Select>
            <Input label="Factor" type="number" value={factor} onChange={(e) => setFactor(e.target.value)} error={convErrors.factor} style={{ width: 120 }} />
            <Button loading={convSubmitting} onClick={handleSaveConversion}>Save</Button>
          </div>
        </Card>

        <Card>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)', fontSize: 12 }}>
                <th style={{ padding: 8 }}>From</th>
                <th style={{ padding: 8 }}>To</th>
                <th style={{ padding: 8 }}>Factor</th>
                <th style={{ padding: 8 }} />
              </tr>
            </thead>
            <tbody>
              {conversions.map((c) => (
                <tr key={c.id} style={{ borderTop: '1px solid var(--color-border)' }}>
                  <td style={{ padding: 8 }}>{c.from_uom.name}</td>
                  <td style={{ padding: 8 }}>{c.to_uom.name}</td>
                  <td style={{ padding: 8 }}>{c.factor}</td>
                  <td style={{ padding: 8 }}><Button variant="danger" onClick={() => handleDeleteConversion(c)}>Delete</Button></td>
                </tr>
              ))}
              {conversions.length === 0 && (
                <tr><td colSpan={4} style={{ padding: 16, textAlign: 'center', color: 'var(--color-text-secondary)' }}>No conversions yet.</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
}
