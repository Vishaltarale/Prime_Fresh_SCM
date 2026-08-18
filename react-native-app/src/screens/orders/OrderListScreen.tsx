import { useCallback, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { Order } from '@shared/types';
import { API_ENDPOINTS, ORDER_STATUSES } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { InfiniteCardList } from '../../components/InfiniteCardList';
import { Card } from '../../components/Card';
import { StatusBadge } from '../../components/StatusBadge';
import { Input } from '../../components/Input';
import { Button } from '../../components/Button';
import { useAuth } from '../../context/AuthContext';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'OrderList'>;

export function OrderListScreen({ navigation }: Props) {
  const { user } = useAuth();
  const isCustomer = user?.role === 'Customer';
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [mineOnly, setMineOnly] = useState(true);

  const fetchPage = useCallback(async (page: number) => {
    const res = await apiClient.get(API_ENDPOINTS.orders, {
      params: { status, search, page, mine: mineOnly ? 'true' : undefined },
    });
    return res.data;
  }, [status, search, mineOnly]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{isCustomer ? 'My Orders' : 'Orders'}</Text>
        <Button title="+ New" onPress={() => navigation.navigate('OrderCreate')} />
      </View>

      <View style={{ paddingHorizontal: spacing.md, marginBottom: spacing.sm }}>
        <Input placeholder="Search customer…" value={search} onChangeText={setSearch} />
      </View>

      {!isCustomer && (
        <View style={{ flexDirection: 'row', gap: 8, paddingHorizontal: spacing.md, marginBottom: spacing.sm }}>
          <Pressable onPress={() => setMineOnly(true)} style={[styles.chip, mineOnly && styles.chipActive]}>
            <Text style={[styles.chipText, mineOnly && styles.chipTextActive]}>My Orders</Text>
          </Pressable>
          <Pressable onPress={() => setMineOnly(false)} style={[styles.chip, !mineOnly && styles.chipActive]}>
            <Text style={[styles.chipText, !mineOnly && styles.chipTextActive]}>All Orders</Text>
          </Pressable>
        </View>
      )}

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipsRow} contentContainerStyle={{ gap: 8, paddingHorizontal: spacing.md }}>
        {['', ...ORDER_STATUSES].map((opt) => (
          <Pressable key={opt || 'all'} onPress={() => setStatus(opt)} style={[styles.chip, status === opt && styles.chipActive]}>
            <Text style={[styles.chipText, status === opt && styles.chipTextActive]}>{opt || 'All'}</Text>
          </Pressable>
        ))}
      </ScrollView>

      <InfiniteCardList<Order>
        fetchPage={fetchPage}
        resetKey={[status, search, mineOnly]}
        keyExtractor={(o) => o.id}
        emptyMessage="No orders match your filters."
        renderItem={(o) => (
          <Pressable onPress={() => navigation.navigate('OrderDetail', { id: o.id })}>
            <Card style={{ marginBottom: spacing.sm, gap: 6 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={styles.cardTitle}>{o.customer_name}</Text>
                <StatusBadge status={o.status} />
              </View>
              <Text style={styles.cardSub}>{o.warehouse?.name ?? '—'}</Text>
              <Text style={styles.cardTotal}>₹{o.total_amount.toFixed(2)}</Text>
            </Card>
          </Pressable>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, paddingTop: 60 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.md, marginBottom: spacing.md },
  title: { fontSize: 22, fontWeight: '800', color: colors.textPrimary },
  chipsRow: { marginBottom: spacing.sm, flexGrow: 0 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderRadius: 999, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  chipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { fontSize: 13, fontWeight: '600', color: colors.textSecondary },
  chipTextActive: { color: colors.textInverse },
  cardTitle: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  cardSub: { fontSize: 13, color: colors.textSecondary },
  cardTotal: { fontSize: 18, fontWeight: '700', color: colors.textPrimary },
});
