import { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { UomRecord, Conversion, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { SelectField } from '../../components/SelectField';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'UomList'>;

export function UomListScreen(_props: Props) {
  const [uoms, setUoms] = useState<UomRecord[]>([]);
  const [conversions, setConversions] = useState<Conversion[]>([]);

  const [uomName, setUomName] = useState('');
  const [uomDesc, setUomDesc] = useState('');
  const [uomSubmitting, setUomSubmitting] = useState(false);

  const [fromUom, setFromUom] = useState('');
  const [toUom, setToUom] = useState('');
  const [factor, setFactor] = useState('');
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
    if (!uomName.trim()) return;
    setUomSubmitting(true);
    try {
      await apiClient.post(API_ENDPOINTS.catalogUom, { name: uomName, description: uomDesc });
      setUomName('');
      setUomDesc('');
      reloadUoms();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { name?: string } } })?.response?.data?.name;
      Alert.alert('Failed to save', msg ?? 'Please try again.');
    } finally {
      setUomSubmitting(false);
    }
  }

  function confirmDeleteUom(uom: UomRecord) {
    Alert.alert('Delete?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive', onPress: async () => {
          try {
            await apiClient.delete(API_ENDPOINTS.catalogUomDetail(uom.id));
            reloadUoms();
            reloadConversions();
          } catch (err: unknown) {
            const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            Alert.alert('Delete failed', msg ?? 'Please try again.');
          }
        },
      },
    ]);
  }

  async function handleSaveConversion() {
    if (!fromUom || !toUom || !factor) return;
    setConvSubmitting(true);
    try {
      await apiClient.post(API_ENDPOINTS.conversions, { from_uom: fromUom, to_uom: toUom, factor: Number(factor) });
      setFromUom('');
      setToUom('');
      setFactor('');
      reloadConversions();
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      Alert.alert('Failed to save', Object.values(respData ?? {}).join(' ') || 'Please try again.');
    } finally {
      setConvSubmitting(false);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: spacing.md, paddingTop: 60, paddingBottom: spacing.xl, gap: spacing.lg }}>
      <View>
        <Text style={styles.title}>Units of Measurement</Text>
        <Card style={{ marginTop: spacing.sm, gap: spacing.sm }}>
          <Input label="Name" placeholder="e.g. KG" value={uomName} onChangeText={setUomName} autoCapitalize="characters" />
          <Input label="Description" value={uomDesc} onChangeText={setUomDesc} />
          <Button title="+ Add UOM" onPress={handleCreateUom} loading={uomSubmitting} />
        </Card>

        {uoms.map((u) => (
          <Card key={u.id} style={{ marginTop: spacing.sm, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <View>
              <Text style={styles.cardTitle}>{u.name}</Text>
              {u.description ? <Text style={styles.cardSub}>{u.description}</Text> : null}
            </View>
            <Button title="Delete" variant="danger" onPress={() => confirmDeleteUom(u)} />
          </Card>
        ))}
      </View>

      <View>
        <Text style={styles.title}>Conversion Matrix</Text>
        <Card style={{ marginTop: spacing.sm, gap: spacing.sm }}>
          <SelectField label="From" value={fromUom} onChange={setFromUom} options={uoms.map((u) => ({ label: u.name, value: u.id }))} />
          <SelectField label="To" value={toUom} onChange={setToUom} options={uoms.map((u) => ({ label: u.name, value: u.id }))} />
          <Input label="Factor" keyboardType="numeric" value={factor} onChangeText={setFactor} />
          <Button title="Save Conversion" onPress={handleSaveConversion} loading={convSubmitting} />
        </Card>

        {conversions.map((c) => (
          <Card key={c.id} style={{ marginTop: spacing.sm, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={styles.cardSub}>{c.from_uom.name} → {c.to_uom.name} (×{c.factor})</Text>
          </Card>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  title: { fontSize: 20, fontWeight: '800', color: colors.textPrimary },
  cardTitle: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  cardSub: { fontSize: 13, color: colors.textSecondary },
});
