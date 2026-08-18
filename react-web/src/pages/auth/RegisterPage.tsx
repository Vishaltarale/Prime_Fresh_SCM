import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthLayout } from './AuthLayout';
import { Input, Select } from '../../components/Input';
import { Button } from '../../components/Button';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../components/Toast';
import { STAFF_ROLES, EXTERNAL_ROLES, REGISTER_PROFILE_FIELDS } from '@shared/constants';
import type { RegisterInput, Role } from '@shared/types';

const FIELD_LABELS: Record<string, string> = {
  address: 'Address',
  city: 'City',
  state: 'State',
  district: 'District',
  village: 'Village',
  company_name: 'Company Name',
};

const emptyForm: RegisterInput = {
  full_name: '', email: '', phone: '', password: '', role: 'Customer',
  address: '', city: '', state: '', district: '', village: '', company_name: '',
};

export function RegisterPage() {
  const { register } = useAuth();
  const { show } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState<RegisterInput>(emptyForm);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function update<K extends keyof RegisterInput>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  const profileFields = REGISTER_PROFILE_FIELDS[form.role] ?? [];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form);
      show('Account created', 'success');
      navigate('/');
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      const message = respData ? Object.values(respData).join(' ') : 'Registration failed.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Create account" subtitle="Register a new Prime Fresh SCM account">
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <Input label="Full name" required value={form.full_name} onChange={(e) => update('full_name', e.target.value)} />
        <Input label="Email" type="email" required value={form.email} onChange={(e) => update('email', e.target.value)} />
        <Input label="Phone" required value={form.phone} onChange={(e) => update('phone', e.target.value)} />
        <Select label="I am a…" value={form.role} onChange={(e) => update('role', e.target.value as Role)}>
          <optgroup label="Customer / Partner">
            {EXTERNAL_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </optgroup>
          <optgroup label="Staff">
            {STAFF_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </optgroup>
        </Select>

        {profileFields.map((field) => (
          <Input
            key={field}
            label={FIELD_LABELS[field]}
            required
            value={(form[field as keyof RegisterInput] as string) ?? ''}
            onChange={(e) => update(field as keyof RegisterInput, e.target.value)}
          />
        ))}

        <Input label="Password" type="password" required minLength={8} value={form.password} onChange={(e) => update('password', e.target.value)} />
        {error && <span style={{ fontSize: 13, color: 'var(--color-danger)' }}>{error}</span>}
        <Button type="submit" loading={loading}>Create account</Button>
      </form>
      <p style={{ marginTop: 16, fontSize: 13, textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        Already registered? <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>Sign in</Link>
      </p>
    </AuthLayout>
  );
}
