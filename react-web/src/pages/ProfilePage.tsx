import { useEffect, useState } from 'react';
import type { MyProfile } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../lib/apiClient';
import { Card } from '../components/Card';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { useToast } from '../components/Toast';

const ENTITY_FIELD_LABELS: Record<string, string> = {
  phone: 'Phone',
  address: 'Address',
  city: 'City',
  state: 'State',
  district: 'District',
  village: 'Village',
  company_name: 'Company Name',
};

export function ProfilePage() {
  const { show } = useToast();
  const [profile, setProfile] = useState<MyProfile | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiClient.get<MyProfile>(API_ENDPOINTS.myProfile).then((res) => {
      setProfile(res.data);
      setValues({
        full_name: res.data.user.full_name,
        ...(res.data.entity ?? {}),
      });
    }).finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setSubmitting(true);
    try {
      const res = await apiClient.put<MyProfile>(API_ENDPOINTS.myProfile, values);
      setProfile(res.data);
      show('Profile updated.', 'success');
    } catch {
      show('Update failed.', 'error');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !profile) return <Card>Loading…</Card>;

  const entityFields = profile.entity ? Object.keys(profile.entity).filter((k) => k !== 'id') : [];

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 20 }}>My Profile</h1>
      <Card style={{ maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <Input label="Full Name" value={values.full_name ?? ''} onChange={(e) => setValues((v) => ({ ...v, full_name: e.target.value }))} />
        <Input label="Email" value={profile.user.email} disabled />
        <Input label="Role" value={profile.user.role} disabled />

        {entityFields.map((field) => (
          <Input
            key={field}
            label={ENTITY_FIELD_LABELS[field] ?? field}
            value={values[field] ?? ''}
            onChange={(e) => setValues((v) => ({ ...v, [field]: e.target.value }))}
          />
        ))}

        <Button onClick={handleSave} loading={submitting}>Save Changes</Button>
      </Card>
    </div>
  );
}
