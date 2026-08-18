import { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { Order } from '@shared/types';
import { API_ENDPOINTS, ORDER_STATUSES, PAYMENT_STATUSES } from '@shared/constants';
import { apiClient, nativeTokenStorage } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { SelectField } from '../../components/SelectField';
import { StatusBadge } from '../../components/StatusBadge';
import { useAuth } from '../../context/AuthContext';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'OrderDetail'>;

export function OrderDetailScreen({ route, navigation }: Props) {
  const { id } = route.params;
  const { user } = useAuth();
  const isCustomer = user?.role === 'Customer';
  const [order, setOrder] = useState<Order | null>(null);
  const [status, setStatus] = useState('');
  const [paymentStatus, setPaymentStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    apiClient.get<Order>(API_ENDPOINTS.orderDetail(id)).then((res) => {
      setOrder(res.data);
      setStatus(res.data.status);
      setPaymentStatus(res.data.payment_status);
    }).finally(() => setLoading(false));
  }, [id]);

  async function handleSave() {
    if (!order) return;
    setSubmitting(true);
    try {
      // Deliberately omit `items` — this screen only updates status/payment (mobile-simplified
      // vs. the web edit form's full item re-editing), and the API treats a missing `items` key
      // as "leave line items unchanged" rather than "clear them".
      const res = await apiClient.put<Order>(API_ENDPOINTS.orderDetail(id), {
        customer_name: order.customer_name,
        delivery_address: order.delivery_address,
        warehouse: order.warehouse?.id,
        status,
        payment_status: paymentStatus,
      });
      setOrder(res.data);
      Alert.alert('Saved', 'Order updated.');
    } catch {
      Alert.alert('Update failed', 'Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  function confirmDelete() {
    Alert.alert('Delete order?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive', onPress: async () => {
          await apiClient.delete(API_ENDPOINTS.orderDetail(id));
          navigation.goBack();
        },
      },
    ]);
  }

  async function handleDownloadInvoice() {
    setDownloading(true);
    try {
      const fileUri = `${FileSystem.cacheDirectory}Invoice_${id}.pdf`;
      const tokensRaw = await nativeTokenStorage.getTokens();
      const download = await FileSystem.downloadAsync(
        `${apiClient.defaults.baseURL}${API_ENDPOINTS.orderInvoice(id)}`,
        fileUri,
        { headers: tokensRaw?.access ? { Authorization: `Bearer ${tokensRaw.access}` } : {} }
      );
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(download.uri, { mimeType: 'application/pdf' });
      } else {
        Alert.alert('Downloaded', `Saved to ${download.uri}`);
      }
    } catch {
      Alert.alert('Failed', 'Could not download the invoice.');
    } finally {
      setDownloading(false);
    }
  }

  if (loading) return <View style={styles.center}><Text style={styles.muted}>Loading…</Text></View>;
  if (!order) return <View style={styles.center}><Text style={styles.muted}>Order not found.</Text></View>;

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: spacing.md, paddingTop: 60, gap: spacing.md }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <View>
          <Text style={styles.title}>{order.customer_name}</Text>
          <Text style={styles.muted}>{order.order_date}</Text>
        </View>
        <StatusBadge status={order.status} />
      </View>

      <Card style={{ gap: spacing.sm }}>
        <Row label="Warehouse" value={order.warehouse?.name ?? '—'} />
        <Row label="Delivery Address" value={order.delivery_address} />
        <Row label="Total" value={`₹${order.total_amount.toFixed(2)}`} />
      </Card>

      <Card style={{ gap: spacing.sm }}>
        <Text style={styles.sectionTitle}>Line items</Text>
        {order.items.map((item, i) => (
          <View key={i} style={styles.itemRow}>
            <Text style={{ fontWeight: '600', color: colors.textPrimary }}>{item.product_name}</Text>
            <Text style={styles.muted}>{item.quantity} {item.uom} @ ₹{item.price.toFixed(2)}</Text>
            <Text style={{ fontWeight: '700', color: colors.textPrimary }}>₹{item.line_total.toFixed(2)}</Text>
          </View>
        ))}
      </Card>

      {!isCustomer && (
        <Card style={{ gap: spacing.md }}>
          <Text style={styles.sectionTitle}>Update status</Text>
          <SelectField label="Status" value={status} onChange={setStatus} options={ORDER_STATUSES.map((s) => ({ label: s, value: s }))} />
          <SelectField label="Payment Status" value={paymentStatus} onChange={setPaymentStatus} options={PAYMENT_STATUSES.map((s) => ({ label: s, value: s }))} />
          <Button title="Save Changes" onPress={handleSave} loading={submitting} />
        </Card>
      )}

      <Button title="Download Invoice" variant="secondary" onPress={handleDownloadInvoice} loading={downloading} />
      {!isCustomer && <Button title="Delete Order" variant="danger" onPress={confirmDelete} />}
      <Button title="Back to list" variant="secondary" onPress={() => navigation.goBack()} />
    </ScrollView>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  title: { fontSize: 22, fontWeight: '800', color: colors.textPrimary },
  muted: { fontSize: 13, color: colors.textSecondary },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: colors.textPrimary },
  itemRow: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.sm, gap: 2 },
  label: { fontSize: 12, fontWeight: '600', color: colors.textSecondary, textTransform: 'uppercase' },
  value: { fontSize: 15, color: colors.textPrimary, marginTop: 2 },
});
