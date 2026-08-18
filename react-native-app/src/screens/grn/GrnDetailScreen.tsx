import { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { Grn } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { StatusBadge } from '../../components/StatusBadge';
import { useAuth } from '../../context/AuthContext';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'GrnDetail'>;

export function GrnDetailScreen({ route, navigation }: Props) {
  const { id } = route.params;
  const { user } = useAuth();
  const canAct = user?.role === 'Admin' || user?.role === 'Inventory Officer' || user?.role === 'Warehouse Manager';
  const [grn, setGrn] = useState<Grn | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiClient.get<Grn>(API_ENDPOINTS.grnDetail(id))
      .then((res) => setGrn(res.data))
      .finally(() => setLoading(false));
  }, [id]);

  function confirmAction(action: 'confirm' | 'reject') {
    Alert.alert(
      action === 'confirm' ? 'Confirm GRN?' : 'Reject GRN?',
      action === 'confirm'
        ? 'This will add the received quantities to warehouse stock.'
        : 'This will mark the GRN as rejected.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: `Yes, ${action}`, style: action === 'reject' ? 'destructive' : 'default', onPress: () => runAction(action) },
      ]
    );
  }

  async function runAction(action: 'confirm' | 'reject') {
    setSubmitting(true);
    try {
      const endpoint = action === 'confirm' ? API_ENDPOINTS.grnConfirm(id) : API_ENDPOINTS.grnReject(id);
      const res = await apiClient.post<Grn>(endpoint);
      setGrn(res.data);
    } catch {
      Alert.alert('Action failed', 'Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <View style={styles.center}><Text style={styles.muted}>Loading…</Text></View>;
  }
  if (!grn) {
    return <View style={styles.center}><Text style={styles.muted}>GRN not found.</Text></View>;
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: spacing.md, paddingTop: 60, gap: spacing.md }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <View>
          <Text style={styles.title}>{grn.grn_number}</Text>
          <Text style={styles.muted}>{new Date(grn.created_at).toLocaleString()}</Text>
        </View>
        <StatusBadge status={grn.status} />
      </View>

      <Card style={{ gap: spacing.sm }}>
        <Row label="Source" value={(grn.source_type === 'Supplier' ? grn.supplier?.name : grn.farmer?.name) ?? '—'} />
        <Row label="Warehouse" value={grn.warehouse.name} />
        <Row label="Total" value={`₹${grn.total_amount.toFixed(2)}`} />
        <Row label="Notes" value={grn.notes || '—'} />
      </Card>

      <Card style={{ gap: spacing.sm }}>
        <Text style={styles.sectionTitle}>Line items</Text>
        {grn.items.map((item, i) => (
          <View key={i} style={styles.itemRow}>
            <Text style={{ fontWeight: '600', color: colors.textPrimary }}>{item.product_name}</Text>
            <Text style={styles.muted}>{item.received_qty} / {item.ordered_qty} {item.uom} @ ₹{item.unit_price.toFixed(2)}</Text>
            <Text style={{ fontWeight: '700', color: colors.textPrimary }}>₹{(item.line_total ?? item.received_qty * item.unit_price).toFixed(2)}</Text>
          </View>
        ))}
      </Card>

      {canAct && grn.status === 'Draft' && (
        <View style={{ flexDirection: 'row', gap: spacing.md }}>
          <Button title="Reject" variant="danger" onPress={() => confirmAction('reject')} loading={submitting} style={{ flex: 1 }} />
          <Button title="Confirm" onPress={() => confirmAction('confirm')} loading={submitting} style={{ flex: 1 }} />
        </View>
      )}
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
