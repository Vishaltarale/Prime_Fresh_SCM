import { useCallback, useEffect, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { EntityMeta, EntityRecord } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { InfiniteCardList } from '../../components/InfiniteCardList';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'EntityList'>;

export function EntityListScreen({ route, navigation }: Props) {
  const { entity, label } = route.params;
  const [meta, setMeta] = useState<EntityMeta | null>(null);
  const [search, setSearch] = useState('');
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    apiClient.get<EntityMeta>(API_ENDPOINTS.entityMeta(entity)).then((res) => setMeta(res.data));
  }, [entity]);

  const fetchPage = useCallback(async (page: number) => {
    const res = await apiClient.get(API_ENDPOINTS.entityList(entity), { params: { search, page } });
    return res.data;
  }, [entity, search]);

  function confirmDelete(record: EntityRecord) {
    Alert.alert('Delete?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await apiClient.delete(API_ENDPOINTS.entityDetail(entity, record.id));
            setRefreshToken((t) => t + 1);
          } catch {
            Alert.alert('Delete failed', 'Please try again.');
          }
        },
      },
    ]);
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{label}</Text>
        <Button title="+ Add" onPress={() => navigation.navigate('EntityForm', { entity, label })} />
      </View>

      <View style={{ paddingHorizontal: spacing.md }}>
        <Input placeholder={`Search ${label.toLowerCase()}…`} value={search} onChangeText={setSearch} />
      </View>

      {meta && (
        <InfiniteCardList<EntityRecord>
          fetchPage={fetchPage}
          resetKey={[search, refreshToken]}
          keyExtractor={(r) => r.id}
          emptyMessage={`No ${label.toLowerCase()} found.`}
          renderItem={(record) => (
            <Card style={{ marginBottom: spacing.sm, gap: 4 }}>
              {meta.fields.slice(0, 3).map((f) => (
                <Text key={f.name} style={styles.fieldLine}>
                  <Text style={styles.fieldLabel}>{f.label}: </Text>
                  {String(record[f.name] ?? '—')}
                </Text>
              ))}
              <View style={{ flexDirection: 'row', gap: spacing.sm, marginTop: spacing.xs }}>
                <Pressable onPress={() => navigation.navigate('EntityForm', { entity, label, id: record.id })} style={styles.actionBtn}>
                  <Text style={styles.actionText}>Edit</Text>
                </Pressable>
                <Pressable onPress={() => confirmDelete(record)} style={[styles.actionBtn, { borderColor: colors.danger }]}>
                  <Text style={[styles.actionText, { color: colors.danger }]}>Delete</Text>
                </Pressable>
              </View>
            </Card>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, paddingTop: 60 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.md, marginBottom: spacing.sm },
  title: { fontSize: 22, fontWeight: '800', color: colors.textPrimary },
  fieldLine: { fontSize: 13, color: colors.textPrimary },
  fieldLabel: { fontWeight: '700', color: colors.textSecondary },
  actionBtn: { borderWidth: 1, borderColor: colors.border, borderRadius: 8, paddingVertical: 6, paddingHorizontal: 12 },
  actionText: { fontSize: 12, fontWeight: '700', color: colors.textPrimary },
});
