import { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text } from 'react-native';
import type { MyProfile } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../lib/apiClient';
import { Card } from '../components/Card';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { useAuth } from '../context/AuthContext';
import { colors, spacing } from '../theme';

const ENTITY_FIELD_LABELS: Record<string, string> = {
  phone: 'Phone',
  address: 'Address',
  city: 'City',
  state: 'State',
  district: 'District',
  village: 'Village',
  company_name: 'Company Name',
};

export function ProfileScreen() {
  const { logout } = useAuth();
  const [profile, setProfile] = useState<MyProfile | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiClient.get<MyProfile>(API_ENDPOINTS.myProfile).then((res) => {
      setProfile(res.data);
      setValues({ full_name: res.data.user.full_name, ...(res.data.entity ?? {}) });
    }).finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setSubmitting(true);
    try {
      const res = await apiClient.put<MyProfile>(API_ENDPOINTS.myProfile, values);
      setProfile(res.data);
      Alert.alert('Saved', 'Profile updated.');
    } catch {
      Alert.alert('Update failed', 'Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !profile) {
    return <ScrollView style={styles.container}><Text style={styles.muted}>Loading…</Text></ScrollView>;
  }

  const entityFields = profile.entity ? Object.keys(profile.entity).filter((k) => k !== 'id') : [];

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: spacing.md, paddingTop: 60, gap: spacing.md }}>
      <Text style={styles.title}>My Profile</Text>
      <Card style={{ gap: spacing.md }}>
        <Input label="Full Name" value={values.full_name ?? ''} onChangeText={(v) => setValues((s) => ({ ...s, full_name: v }))} />
        <Input label="Email" value={profile.user.email} editable={false} />
        <Input label="Role" value={profile.user.role} editable={false} />

        {entityFields.map((field) => (
          <Input
            key={field}
            label={ENTITY_FIELD_LABELS[field] ?? field}
            value={values[field] ?? ''}
            onChangeText={(v) => setValues((s) => ({ ...s, [field]: v }))}
          />
        ))}

        <Button title="Save Changes" onPress={handleSave} loading={submitting} />
      </Card>

      <Button title="Sign out" variant="secondary" onPress={logout} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  title: { fontSize: 22, fontWeight: '800', color: colors.textPrimary, marginBottom: spacing.sm },
  muted: { fontSize: 13, color: colors.textSecondary, padding: spacing.md, paddingTop: 60 },
});
