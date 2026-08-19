import { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { NamedRef, CatalogProduct, OrderItemInput, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { SelectField } from '../../components/SelectField';
import { Button } from '../../components/Button';
import { useAuth } from '../../context/AuthContext';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'OrderCreate'>;

const emptyItem: OrderItemInput = { product: '', quantity: 1, price: 0, uom: '' };

export function OrderCreateScreen({ navigation }: Props) {
  const { user } = useAuth();
  const isCustomer = user?.role === 'Customer';
  const [warehouses, setWarehouses] = useState<NamedRef[]>([]);
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [customerName, setCustomerName] = useState(isCustomer ? user!.full_name : '');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [warehouse, setWarehouse] = useState('');
  const [items, setItems] = useState<OrderItemInput[]>([{ ...emptyItem }]);

  useEffect(() => {
    Promise.all([
      apiClient.get<NamedRef[]>(API_ENDPOINTS.warehouses),
      apiClient.get<Paginated<CatalogProduct>>(API_ENDPOINTS.catalogProducts, { params: { page_size: 200 } }),
    ]).then(([wh, prod]) => {
      setWarehouses(wh.data);
      setProducts(prod.data.results);
    }).finally(() => setLoadingLookups(false));
  }, []);

  const productsInWarehouse = products
    .map((p) => ({ product: p, stockLine: p.stock.find((s) => s.warehouse.id === warehouse) }))
    .filter((row): row is { product: CatalogProduct; stockLine: NonNullable<typeof row.stockLine> } => !!row.stockLine);
  const total = items.reduce((sum, it) => sum + (Number(it.quantity) || 0) * (Number(it.price) || 0), 0);

  function updateItem(index: number, patch: Partial<OrderItemInput>) {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  }

  function pickProduct(index: number, productId: string) {
    const product = products.find((p) => p.id === productId);
    const stockLine = product?.stock.find((s) => s.warehouse.id === warehouse);
    updateItem(index, { product: productId, price: stockLine?.price_per_unit ?? product?.price_per_unit ?? 0, uom: product?.uom?.name ?? '' });
  }

  function addItem() { setItems((prev) => [...prev, { ...emptyItem }]); }
  function removeItem(index: number) { setItems((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== index) : prev)); }

  async function handleSubmit() {
    if (!customerName || !warehouse || !deliveryAddress) {
      Alert.alert('Missing fields', 'Please fill in customer, address, and warehouse.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await apiClient.post(API_ENDPOINTS.orders, {
        customer_name: customerName, delivery_address: deliveryAddress, warehouse, items,
      });
      navigation.replace('OrderDetail', { id: res.data.id });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { items?: string } } })?.response?.data?.items;
      Alert.alert('Failed to place order', msg ?? 'Check the form and try again.');
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
        <Text style={styles.title}>New Order</Text>

        <Card style={{ gap: spacing.md }}>
          <Input label="Customer Name" value={customerName} onChangeText={setCustomerName} editable={!isCustomer} />
          <SelectField label="Warehouse" value={warehouse} onChange={setWarehouse} options={warehouses.map((w) => ({ label: w.name, value: w.id }))} />
          <Input label="Delivery Address" value={deliveryAddress} onChangeText={setDeliveryAddress} multiline />
        </Card>

        <Card style={{ gap: spacing.md }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={styles.sectionTitle}>Line items</Text>
            <Button title="+ Add" variant="secondary" onPress={addItem} />
          </View>

          {!warehouse && <Text style={styles.muted}>Select a warehouse to choose products.</Text>}

          {items.map((item, index) => (
            <Card key={index} style={{ gap: spacing.sm, backgroundColor: colors.background }}>
              <SelectField
                label={`Product #${index + 1}`}
                value={item.product}
                onChange={(v) => pickProduct(index, v)}
                options={productsInWarehouse.map(({ product: p, stockLine }) => ({ label: `${p.name} (${p.sku}) — ${stockLine.quantity_available} in stock`, value: p.id }))}
              />
              <View style={{ flexDirection: 'row', gap: spacing.sm }}>
                <Input label="Quantity" keyboardType="numeric" style={{ flex: 1 }} value={String(item.quantity)} onChangeText={(v) => updateItem(index, { quantity: Number(v) || 0 })} />
                <Input label="Price" keyboardType="numeric" style={{ flex: 1 }} value={String(item.price)} onChangeText={(v) => updateItem(index, { price: Number(v) || 0 })} />
                <Input label="UOM" style={{ flex: 1 }} value={item.uom} onChangeText={(v) => updateItem(index, { uom: v })} />
              </View>
              {items.length > 1 && <Button title="Remove row" variant="danger" onPress={() => removeItem(index)} />}
            </Card>
          ))}

          <Text style={styles.total}>Total: ₹{total.toFixed(2)}</Text>
        </Card>

        <Button title="Place Order" onPress={handleSubmit} loading={submitting} />
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
