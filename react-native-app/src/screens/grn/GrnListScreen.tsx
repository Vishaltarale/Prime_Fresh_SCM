import { useCallback, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { Grn } from '@shared/types';
import { API_ENDPOINTS, GRN_STATUSES } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { InfiniteCardList } from '../../components/InfiniteCardList';
import { Card } from '../../components/Card';
import { StatusBadge } from '../../components/StatusBadge';
import { Input } from '../../components/Input';
import { Button } from '../../components/Button';
import { useAuth } from '../../context/AuthContext';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'GrnList'>;

export function GrnListScreen({ navigation }: Props) {
  const { user } = useAuth();
  const canCreate = user?.role === 'Admin' || user?.role === 'Inventory Officer' || user?.role === 'Warehouse Manager';
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');

  const fetchPage = useCallback(async (page: number) => {
    const res = await apiClient.get(API_ENDPOINTS.grnList, { params: { status, search, page } });
    return res.data;
  }, [status, search]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{canCreate ? 'Goods Receipt Notes' : 'My Deliveries'}</Text>
        {canCreate && <Button title="+ New" onPress={() => navigation.navigate('GrnCreate')} />}
      </View>

      <View style={{ paddingHorizontal: spacing.md }}>
        <Input placeholder="Search GRN number…" value={search} onChangeText={setSearch} />
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipsRow} contentContainerStyle={{ gap: 8, paddingHorizontal: spacing.md }}>
        {['', ...GRN_STATUSES].map((opt) => (
          <Pressable key={opt || 'all'} onPress={() => setStatus(opt)} style={[styles.chip, status === opt && styles.chipActive]}>
            <Text style={[styles.chipText, status === opt && styles.chipTextActive]}>{opt || 'All'}</Text>
          </Pressable>
        ))}
      </ScrollView>

      <InfiniteCardList<Grn>
        fetchPage={fetchPage}
        resetKey={[status, search]}
        keyExtractor={(g) => g.id}
        emptyMessage="No GRNs match your filters."
        renderItem={(g) => (
          <Pressable onPress={() => navigation.navigate('GrnDetail', { id: g.id })}>
            <Card style={{ marginBottom: spacing.sm, gap: 6 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={styles.cardTitle}>{g.grn_number}</Text>
                <StatusBadge status={g.status} />
              </View>
              <Text style={styles.cardSub}>{g.warehouse.name}</Text>
              <Text style={styles.cardTotal}>₹{g.total_amount.toFixed(2)}</Text>
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
  chipsRow: { marginTop: spacing.sm, marginBottom: spacing.sm, flexGrow: 0 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderRadius: 999, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  chipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { fontSize: 13, fontWeight: '600', color: colors.textSecondary },
  chipTextActive: { color: colors.textInverse },
  cardTitle: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  cardSub: { fontSize: 13, color: colors.textSecondary },
  cardTotal: { fontSize: 18, fontWeight: '700', color: colors.textPrimary },
});
