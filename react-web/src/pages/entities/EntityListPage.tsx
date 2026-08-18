import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import type { EntityMeta, EntityRecord, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { DataView, type Column } from '../../components/DataView';
import { SearchBar } from '../../components/SearchBar';
import { FilterBar } from '../../components/FilterBar';
import { Pagination } from '../../components/Pagination';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { Modal } from '../../components/Modal';
import { EntityFieldInput } from '../../components/EntityFieldInput';
import { useToast } from '../../components/Toast';

const PAGE_SIZE = 10;

export function EntityListPage() {
  const { entity } = useParams<{ entity: string }>();
  const { show } = useToast();

  const [meta, setMeta] = useState<EntityMeta | null>(null);
  const [data, setData] = useState<Paginated<EntityRecord> | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<EntityRecord | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<EntityRecord | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Reset local state when navigating between entity types (e.g. Employees -> Farmers).
  useEffect(() => {
    setSearch('');
    setPage(1);
    setMeta(null);
  }, [entity]);

  useEffect(() => {
    if (!entity) return;
    apiClient.get<EntityMeta>(API_ENDPOINTS.entityMeta(entity)).then((res) => setMeta(res.data));
  }, [entity]);

  useEffect(() => {
    if (!entity) return;
    let cancelled = false;
    setLoading(true);
    apiClient
      .get<Paginated<EntityRecord>>(API_ENDPOINTS.entityList(entity), { params: { search, page } })
      .then((res) => { if (!cancelled) setData(res.data); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [entity, search, page]);

  const columns: Column<EntityRecord>[] = useMemo(() => {
    if (!meta) return [];
    const fieldCols: Column<EntityRecord>[] = meta.fields.map((f) => ({
      key: f.name,
      header: f.label,
      render: (row) => {
        const v = row[f.name];
        if (f.type === 'bool') return v ? 'Yes' : 'No';
        return String(v ?? '—');
      },
    }));
    return [
      ...fieldCols,
      {
        key: 'actions',
        header: 'Actions',
        render: (row) => (
          <div style={{ display: 'flex', gap: 8 }}>
            <Button variant="secondary" onClick={(e) => { e.stopPropagation(); openEdit(row); }}>Edit</Button>
            <Button variant="danger" onClick={(e) => { e.stopPropagation(); setDeleteTarget(row); }}>Delete</Button>
          </div>
        ),
      },
    ];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meta]);

  function openCreate() {
    if (!meta) return;
    setEditing(null);
    setFormValues(Object.fromEntries(meta.fields.map((f) => [f.name, ''])));
    setFormErrors({});
    setFormOpen(true);
  }

  function openEdit(row: EntityRecord) {
    if (!meta) return;
    setEditing(row);
    setFormValues(Object.fromEntries(meta.fields.map((f) => [f.name, String(row[f.name] ?? '')])));
    setFormErrors({});
    setFormOpen(true);
  }

  async function handleSave() {
    if (!entity || !meta) return;
    setSubmitting(true);
    setFormErrors({});
    try {
      const payload = { ...formValues } as Record<string, string | boolean>;
      meta.fields.forEach((f) => {
        if (f.type === 'bool') payload[f.name] = formValues[f.name] === 'true';
      });

      if (editing) {
        await apiClient.put(API_ENDPOINTS.entityDetail(entity, editing.id), payload);
        show(`${meta.label.slice(0, -1)} updated.`, 'success');
      } else {
        await apiClient.post(API_ENDPOINTS.entityList(entity), payload);
        show(`${meta.label.slice(0, -1)} created.`, 'success');
      }
      setFormOpen(false);
      setPage(1);
      const res = await apiClient.get<Paginated<EntityRecord>>(API_ENDPOINTS.entityList(entity), { params: { search, page: 1 } });
      setData(res.data);
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      if (respData && typeof respData === 'object') {
        setFormErrors(respData);
      } else {
        show('Save failed.', 'error');
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!entity || !deleteTarget) return;
    setDeleting(true);
    try {
      await apiClient.delete(API_ENDPOINTS.entityDetail(entity, deleteTarget.id));
      show('Deleted.', 'success');
      const res = await apiClient.get<Paginated<EntityRecord>>(API_ENDPOINTS.entityList(entity), { params: { search, page } });
      setData(res.data);
    } catch {
      show('Delete failed.', 'error');
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  }

  if (!entity) return null;
  const pageCount = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24 }}>{meta?.label ?? '…'}</h1>
        {meta && <Button onClick={openCreate}>+ Add {meta.label.slice(0, -1)}</Button>}
      </div>

      <FilterBar>
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder={`Search ${meta?.label.toLowerCase() ?? ''}…`} />
      </FilterBar>

      {loading && !data ? (
        <Card>Loading…</Card>
      ) : meta ? (
        <>
          <DataView
            viewKey={`entity-${entity}`}
            columns={columns}
            rows={data?.results ?? []}
            getRowId={(r) => r.id}
            renderCard={(row) => (
              <Card style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {meta.fields.slice(0, 3).map((f) => (
                  <div key={f.name} style={{ fontSize: 13 }}>
                    <strong>{f.label}:</strong> {String(row[f.name] ?? '—')}
                  </div>
                ))}
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <Button variant="secondary" onClick={() => openEdit(row)}>Edit</Button>
                  <Button variant="danger" onClick={() => setDeleteTarget(row)}>Delete</Button>
                </div>
              </Card>
            )}
            emptyMessage={`No ${meta.label.toLowerCase()} found.`}
          />
          {data && <Pagination page={page} pageCount={pageCount} onPageChange={setPage} totalCount={data.count} pageSize={PAGE_SIZE} />}
        </>
      ) : null}

      <Modal
        open={formOpen}
        title={editing ? `Edit ${meta?.label.slice(0, -1)}` : `Add ${meta?.label.slice(0, -1)}`}
        onClose={() => setFormOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button loading={submitting} onClick={handleSave}>Save</Button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {meta?.fields.map((f) => (
            <EntityFieldInput
              key={f.name}
              field={f}
              value={formValues[f.name] ?? ''}
              onChange={(v) => setFormValues((prev) => ({ ...prev, [f.name]: v }))}
              error={formErrors[f.name]}
            />
          ))}
        </div>
      </Modal>

      <Modal
        open={deleteTarget !== null}
        title={`Delete ${meta?.label.slice(0, -1)}?`}
        onClose={() => setDeleteTarget(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button variant="danger" loading={deleting} onClick={handleDelete}>Delete</Button>
          </>
        }
      >
        This cannot be undone.
      </Modal>
    </div>
  );
}
