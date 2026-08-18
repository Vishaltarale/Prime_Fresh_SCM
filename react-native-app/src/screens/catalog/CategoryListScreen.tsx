import { useCallback, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { Category } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { InfiniteCardList } from '../../components/InfiniteCardList';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'CategoryList'>;

export function CategoryListScreen(_props: Props) {
  const [search, setSearch] = useState('');
  const [refreshToken, setRefreshToken] = useState(0);
  const [formOpen, setFormOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchPage = useCallback(async (page: number) => {
    const res = await apiClient.get(API_ENDPOINTS.categories, { params: { search, page } });
    return res.data;
  }, [search]);

  async function handleCreate() {
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      await apiClient.post(API_ENDPOINTS.categories, { name, description });
      setName('');
      setDescription('');
      setFormOpen(false);
      setRefreshToken((t) => t + 1);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { name?: string } } })?.response?.data?.name;
      Alert.alert('Failed to save', msg ?? 'Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  function confirmDelete(category: Category) {
    Alert.alert('Delete?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive', onPress: async () => {
          try {
            await apiClient.delete(API_ENDPOINTS.categoryDetail(category.id));
            setRefreshToken((t) => t + 1);
          } catch (err: unknown) {
            const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            Alert.alert('Delete failed', msg ?? 'Please try again.');
          }
        },
      },
    ]);
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Categories</Text>
        <Button title={formOpen ? 'Cancel' : '+ Add'} variant={formOpen ? 'secondary' : 'primary'} onPress={() => setFormOpen((o) => !o)} />
      </View>

      {formOpen && (
        <Card style={{ marginHorizontal: spacing.md, marginBottom: spacing.sm, gap: spacing.sm }}>
          <Input label="Name" value={name} onChangeText={setName} />
          <Input label="Description" value={description} onChangeText={setDescription} />
          <Button title="Save" onPress={handleCreate} loading={submitting} />
        </Card>
      )}

      <View style={{ paddingHorizontal: spacing.md, marginBottom: spacing.sm }}>
        <Input placeholder="Search categories…" value={search} onChangeText={setSearch} />
      </View>

      <InfiniteCardList<Category>
        fetchPage={fetchPage}
        resetKey={[search, refreshToken]}
        keyExtractor={(c) => c.id}
        emptyMessage="No categories found."
        renderItem={(c) => (
          <Card style={{ marginBottom: spacing.sm, gap: 4 }}>
            <Text style={styles.cardTitle}>{c.name}</Text>
            {c.description ? <Text style={styles.cardSub}>{c.description}</Text> : null}
            <Pressable onPress={() => confirmDelete(c)} style={styles.deleteBtn}>
              <Text style={styles.deleteText}>Delete</Text>
            </Pressable>
          </Card>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, paddingTop: 60 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.md, marginBottom: spacing.sm },
  title: { fontSize: 22, fontWeight: '800', color: colors.textPrimary },
  cardTitle: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  cardSub: { fontSize: 13, color: colors.textSecondary },
  deleteBtn: { alignSelf: 'flex-start', borderWidth: 1, borderColor: colors.danger, borderRadius: 8, paddingVertical: 6, paddingHorizontal: 12, marginTop: 4 },
  deleteText: { fontSize: 12, fontWeight: '700', color: colors.danger },
});
