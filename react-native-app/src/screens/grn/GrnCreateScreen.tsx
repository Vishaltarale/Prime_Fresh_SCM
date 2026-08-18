import { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { NamedRef, ProductRef, GrnItem, GrnSourceType } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { SelectField } from '../../components/SelectField';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'GrnCreate'>;

type DraftItem = Pick<GrnItem, 'product' | 'ordered_qty' | 'received_qty' | 'unit_price' | 'uom' | 'remarks'>;

const emptyItem: DraftItem = { product: '', ordered_qty: 0, received_qty: 0, unit_price: 0, uom: '', remarks: '' };

export function GrnCreateScreen({ navigation }: Props) {
  const [warehouses, setWarehouses] = useState<NamedRef[]>([]);
  const [suppliers, setSuppliers] = useState<NamedRef[]>([]);
  const [farmers, setFarmers] = useState<NamedRef[]>([]);
  const [products, setProducts] = useState<ProductRef[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [sourceType, setSourceType] = useState<GrnSourceType>('Supplier');
  const [supplier, setSupplier] = useState('');
  const [farmer, setFarmer] = useState('');
  const [warehouse, setWarehouse] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<DraftItem[]>([{ ...emptyItem }]);

  useEffect(() => {
    Promise.all([
      apiClient.get<NamedRef[]>(API_ENDPOINTS.warehouses),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.suppliers),
      apiClient.get<NamedRef[]>(API_ENDPOINTS.farmers),
      apiClient.get<ProductRef[]>(API_ENDPOINTS.products),
    ]).then(([w, s, f, p]) => {
      setWarehouses(w.data);
      setSuppliers(s.data);
      setFarmers(f.data);
      setProducts(p.data);
    }).finally(() => setLoadingLookups(false));
  }, []);

  function updateItem(index: number, patch: Partial<DraftItem>) {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  }

  function addItem() {
    setItems((prev) => [...prev, { ...emptyItem }]);
  }

  function removeItem(index: number) {
    setItems((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== index) : prev));
  }

  function pickProduct(index: number, productId: string) {
    const product = products.find((p) => p.id === productId);
    updateItem(index, { product: productId, uom: product?.uom ?? '', unit_price: product?.price_per_unit ?? 0 });
  }

  const total = items.reduce((sum, it) => sum + (Number(it.received_qty) || 0) * (Number(it.unit_price) || 0), 0);

  async function handleSubmit() {
    if (!warehouse || (sourceType === 'Supplier' && !supplier) || (sourceType === 'Farmer' && !farmer)) {
      Alert.alert('Missing fields', 'Please select the source and warehouse.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await apiClient.post(API_ENDPOINTS.grnList, {
        source_type: sourceType,
        supplier: sourceType === 'Supplier' ? supplier : undefined,
        farmer: sourceType === 'Farmer' ? farmer : undefined,
        warehouse,
        notes,
        items,
      });
      navigation.replace('GrnDetail', { id: res.data.id });
    } catch {
      Alert.alert('Failed to create GRN', 'Check the form and try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loadingLookups) {
    return <View style={styles.center}><Text style={styles.muted}>Loading form…</Text></View>;
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: colors.background }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={{ padding: spacing.md, paddingTop: 60, gap: spacing.md }}>
        <Text style={styles.title}>New Goods Receipt Note</Text>

        <Card style={{ gap: spacing.md }}>
          <SelectField
            label="Source type"
            value={sourceType}
            onChange={(v) => setSourceType(v as GrnSourceType)}
            options={[{ label: 'Supplier', value: 'Supplier' }, { label: 'Farmer', value: 'Farmer' }]}
          />
          {sourceType === 'Supplier' ? (
            <SelectField label="Supplier" value={supplier} onChange={setSupplier} options={suppliers.map((s) => ({ label: s.name, value: s.id }))} />
          ) : (
            <SelectField label="Farmer" value={farmer} onChange={setFarmer} options={farmers.map((f) => ({ label: f.name, value: f.id }))} />
          )}
          <SelectField label="Warehouse" value={warehouse} onChange={setWarehouse} options={warehouses.map((w) => ({ label: w.name, value: w.id }))} />
          <Input label="Notes" value={notes} onChangeText={setNotes} />
        </Card>

        <Card style={{ gap: spacing.md }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={styles.sectionTitle}>Line items</Text>
            <Button title="+ Add" variant="secondary" onPress={addItem} />
          </View>

          {items.map((item, index) => (
            <Card key={index} style={{ gap: spacing.sm, backgroundColor: colors.background }}>
              <SelectField
                label={`Product #${index + 1}`}
                value={item.product}
                onChange={(v) => pickProduct(index, v)}
                options={products.map((p) => ({ label: `${p.name} (${p.sku})`, value: p.id }))}
              />
              <View style={{ flexDirection: 'row', gap: spacing.sm }}>
                <Input label="Ordered" keyboardType="numeric" style={{ flex: 1 }} value={String(item.ordered_qty)} onChangeText={(v) => updateItem(index, { ordered_qty: Number(v) || 0 })} />
                <Input label="Received" keyboardType="numeric" style={{ flex: 1 }} value={String(item.received_qty)} onChangeText={(v) => updateItem(index, { received_qty: Number(v) || 0 })} />
              </View>
              <View style={{ flexDirection: 'row', gap: spacing.sm }}>
                <Input label="Unit price" keyboardType="numeric" style={{ flex: 1 }} value={String(item.unit_price)} onChangeText={(v) => updateItem(index, { unit_price: Number(v) || 0 })} />
                <Input label="UOM" style={{ flex: 1 }} value={item.uom} onChangeText={(v) => updateItem(index, { uom: v })} />
              </View>
              <Input label="Remarks" value={item.remarks} onChangeText={(v) => updateItem(index, { remarks: v })} />
              {items.length > 1 && <Button title="Remove row" variant="danger" onPress={() => removeItem(index)} />}
            </Card>
          ))}

          <Text style={styles.total}>Total: ₹{total.toFixed(2)}</Text>
        </Card>

        <Button title="Save GRN" onPress={handleSubmit} loading={submitting} />
        <Button title="Cancel" variant="secondary" onPress={() => navigation.goBack()} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  title: { fontSize: 22, fontWeight: '800', color: colors.textPrimary },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: colors.textPrimary },
  muted: { fontSize: 13, color: colors.textSecondary },
  total: { fontSize: 18, fontWeight: '700', color: colors.textPrimary, textAlign: 'right' },
});
