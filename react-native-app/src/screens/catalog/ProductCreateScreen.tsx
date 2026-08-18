import { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { Category, Subcategory, UomRecord, NamedRef, Paginated, ProductSourceType } from '@shared/types';
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
  const [warehouses, setWarehouses] = useState<NamedRef[]>([]);
  const [suppliers, setSuppliers] = useState<NamedRef[]>([]);
  const [farmers, setFarmers] = useState<NamedRef[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState('');
  const [sku, setSku] = useState('');
  const [category, setCategory] = useState('');
  const [subcategory, setSubcategory] = useState('');
  const [uom, setUom] = useState('');
  const [warehouse, setWarehouse] = useState('');
  const [price, setPrice] = useState('');
  const [qty, setQty] = useState('');
  const [description, setDescription] = useState('');
  const [sourceType, setSourceType] = useState<ProductSourceType>('supplier');
  const [supplier, setSupplier] = useState('');
  const [farmer, setFarmer] = useState('');

  useEffect(() => {
    Promise.all([
      apiClient.get<Paginated<Category>>(API_ENDPOINTS.categories, { params: { page_size: 100 } }),
      apiClient.get<Paginated<Subcategory>>(API_ENDPOINTS.subcategories, { params: { page_size: 100 } }),
      apiClient.get<Paginated<UomRecord>>(API_ENDPOINTS.catalogUom, { params: { page_size: 100 } }),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.warehouses),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.suppliers),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.farmers),
    ]).then(([cat, sub, u, wh, sup, farm]) => {
      setCategories(cat.data.results);
      setSubcategories(sub.data.results);
      setUoms(u.data.results);
      setWarehouses(wh.data);
      setSuppliers(sup.data);
      setFarmers(farm.data);
    }).finally(() => setLoadingLookups(false));
  }, []);

  const filteredSubcategories = subcategories.filter((s) => s.category.id === category);

  async function handleSubmit() {
    setSubmitting(true);
    try {
      const payload: Record<string, string> = {
        name, sku, category, subcategory, uom, warehouse,
        price_per_unit: price, quantity_available: qty, description, source_type: sourceType,
      };
      if (sourceType === 'supplier') payload.supplier = supplier;
      else payload.farmer = farmer;

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

        <Card style={{ gap: spacing.md }}>
          <Input label="Name" value={name} onChangeText={setName} />
          <Input label="SKU" value={sku} onChangeText={setSku} autoCapitalize="characters" />
          <SelectField label="Category" value={category} onChange={(v) => { setCategory(v); setSubcategory(''); }} options={categories.map((c) => ({ label: c.name, value: c.id }))} />
          <SelectField label="Subcategory" value={subcategory} onChange={setSubcategory} options={filteredSubcategories.map((s) => ({ label: s.name, value: s.id }))} />
          <SelectField label="UOM" value={uom} onChange={setUom} options={uoms.map((u) => ({ label: u.name, value: u.id }))} />
          <SelectField label="Warehouse" value={warehouse} onChange={setWarehouse} options={warehouses.map((w) => ({ label: w.name, value: w.id }))} />
          <Input label="Price per unit" keyboardType="numeric" value={price} onChangeText={setPrice} />
          <Input label="Quantity available" keyboardType="numeric" value={qty} onChangeText={setQty} />
          <Input label="Description" value={description} onChangeText={setDescription} />
          <SelectField label="Source type" value={sourceType} onChange={(v) => setSourceType(v as ProductSourceType)} options={[{ label: 'Supplier', value: 'supplier' }, { label: 'Farmer', value: 'farmer' }]} />
          {sourceType === 'supplier' ? (
            <SelectField label="Supplier" value={supplier} onChange={setSupplier} options={suppliers.map((s) => ({ label: s.name, value: s.id }))} />
          ) : (
            <SelectField label="Farmer" value={farmer} onChange={setFarmer} options={farmers.map((f) => ({ label: f.name, value: f.id }))} />
          )}
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
});
