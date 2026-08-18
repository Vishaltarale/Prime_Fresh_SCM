import { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { EntityMeta, EntityRecord } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { EntityFieldInput } from '../../components/EntityFieldInput';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'EntityForm'>;

export function EntityFormScreen({ route, navigation }: Props) {
  const { entity, label, id } = route.params;
  const [meta, setMeta] = useState<EntityMeta | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    (async () => {
      const metaRes = await apiClient.get<EntityMeta>(API_ENDPOINTS.entityMeta(entity));
      setMeta(metaRes.data);

      if (id) {
        const recordRes = await apiClient.get<EntityRecord>(API_ENDPOINTS.entityDetail(entity, id));
        setValues(Object.fromEntries(metaRes.data.fields.map((f) => [f.name, String(recordRes.data[f.name] ?? '')])));
      } else {
        setValues(Object.fromEntries(metaRes.data.fields.map((f) => [f.name, ''])));
      }
      setLoading(false);
    })();
  }, [entity, id]);

  async function handleSave() {
    if (!meta) return;
    setSubmitting(true);
    setErrors({});
    try {
      const payload: Record<string, string | boolean> = { ...values };
      meta.fields.forEach((f) => {
        if (f.type === 'bool') payload[f.name] = values[f.name] === 'true';
      });

      if (id) {
        await apiClient.put(API_ENDPOINTS.entityDetail(entity, id), payload);
      } else {
        await apiClient.post(API_ENDPOINTS.entityList(entity), payload);
      }
      navigation.goBack();
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      if (respData && typeof respData === 'object') {
        setErrors(respData);
      } else {
        Alert.alert('Save failed', 'Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !meta) {
    return <ScrollView style={styles.container}><Text style={styles.muted}>Loading…</Text></ScrollView>;
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: colors.background }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={{ padding: spacing.md, paddingTop: 60, gap: spacing.md }}>
        <Text style={styles.title}>{id ? `Edit ${label.slice(0, -1)}` : `Add ${label.slice(0, -1)}`}</Text>

        {meta.fields.map((f) => (
          <EntityFieldInput
            key={f.name}
            field={f}
            value={values[f.name] ?? ''}
            onChange={(v) => setValues((prev) => ({ ...prev, [f.name]: v }))}
            error={errors[f.name]}
          />
        ))}

        <Button title="Save" onPress={handleSave} loading={submitting} />
        <Button title="Cancel" variant="secondary" onPress={() => navigation.goBack()} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.md },
  title: { fontSize: 22, fontWeight: '800', color: colors.textPrimary },
  muted: { fontSize: 13, color: colors.textSecondary, marginTop: 60 },
});
