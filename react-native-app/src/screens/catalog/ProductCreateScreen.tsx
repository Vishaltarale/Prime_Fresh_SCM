import { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { Category, Subcategory, UomRecord, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { SelectField } from '../../components/SelectField';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'ProductCreate'>;

export function ProductCreateScreen({ navigation }: Props) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [subcategories, setSubcategories] = useState<Subcategory[]>([]);
  const [uoms, setUoms] = useState<UomRecord[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState('');
  const [sku, setSku] = useState('');
  const [category, setCategory] = useState('');
  const [subcategory, setSubcategory] = useState('');
  const [uom, setUom] = useState('');
  const [price, setPrice] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    Promise.all([
      apiClient.get<Paginated<Category>>(API_ENDPOINTS.categories, { params: { page_size: 100 } }),
      apiClient.get<Paginated<Subcategory>>(API_ENDPOINTS.subcategories, { params: { page_size: 100 } }),
      apiClient.get<Paginated<UomRecord>>(API_ENDPOINTS.catalogUom, { params: { page_size: 100 } }),
    ]).then(([cat, sub, u]) => {
      setCategories(cat.data.results);
      setSubcategories(sub.data.results);
      setUoms(u.data.results);
    }).finally(() => setLoadingLookups(false));
  }, []);

  const filteredSubcategories = subcategories.filter((s) => s.category.id === category);

  async function handleSubmit() {
    setSubmitting(true);
    try {
      const payload: Record<string, string> = {
        name, sku, category, subcategory, uom, price_per_unit: price, description,
      };

      await apiClient.post(API_ENDPOINTS.catalogProducts, payload);
      navigation.goBack();
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      Alert.alert('Failed to save', Object.values(respData ?? {}).join(' ') || 'Check the form and try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loadingLookups) {
    return <ScrollView style={{ backgroundColor: colors.background }}><Text style={styles.muted}>Loading form…</Text></ScrollView>;
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: colors.background }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={{ padding: spacing.md, paddingTop: 60, gap: spacing.md }}>
        <Text style={styles.title}>New Product</Text>
        <Text style={styles.hint}>
          This adds a catalog reference only — it won't sit in any warehouse or count as stock until it's
          ordered on a Purchase Order and that order's GRN is confirmed.
        </Text>

        <Card style={{ gap: spacing.md }}>
          <Input label="Name" value={name} onChangeText={setName} />
          <Input label="SKU" value={sku} onChangeText={setSku} autoCapitalize="characters" />
          <SelectField label="Category" value={category} onChange={(v) => { setCategory(v); setSubcategory(''); }} options={categories.map((c) => ({ label: c.name, value: c.id }))} />
          <SelectField label="Subcategory" value={subcategory} onChange={setSubcategory} options={filteredSubcategories.map((s) => ({ label: s.name, value: s.id }))} />
          <SelectField label="UOM" value={uom} onChange={setUom} options={uoms.map((u) => ({ label: u.name, value: u.id }))} />
          <Input label="Reference price per unit" keyboardType="numeric" value={price} onChangeText={setPrice} />
          <Input label="Description" value={description} onChangeText={setDescription} />
        </Card>

        <Button title="Save Product" onPress={handleSubmit} loading={submitting} />
        <Button title="Cancel" variant="secondary" onPress={() => navigation.goBack()} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 22, fontWeight: '800', color: colors.textPrimary },
  muted: { fontSize: 13, color: colors.textSecondary, marginTop: 60, paddingHorizontal: spacing.md },
  hint: { fontSize: 13, color: colors.textSecondary },
});
