import { useCallback, useEffect, useState } from 'react';
import { Alert, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { Category, Subcategory, Paginated } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { InfiniteCardList } from '../../components/InfiniteCardList';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { SelectField } from '../../components/SelectField';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'SubcategoryList'>;

export function SubcategoryListScreen(_props: Props) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [search, setSearch] = useState('');
  const [refreshToken, setRefreshToken] = useState(0);
  const [formOpen, setFormOpen] = useState(false);
  const [name, setName] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiClient.get<Paginated<Category>>(API_ENDPOINTS.categories, { params: { page_size: 100 } })
      .then((res) => setCategories(res.data.results));
  }, [refreshToken]);

  const fetchPage = useCallback(async (page: number) => {
    const res = await apiClient.get(API_ENDPOINTS.subcategories, { params: { search, page } });
    return res.data;
  }, [search]);

  async function handleCreate() {
    if (!name.trim() || !categoryId) return;
    setSubmitting(true);
    try {
      await apiClient.post(API_ENDPOINTS.subcategories, { name, category: categoryId });
      setName('');
      setCategoryId('');
      setFormOpen(false);
      setRefreshToken((t) => t + 1);
    } catch {
      Alert.alert('Failed to save', 'Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  function confirmDelete(sub: Subcategory) {
    Alert.alert('Delete?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive', onPress: async () => {
          try {
            await apiClient.delete(API_ENDPOINTS.subcategoryDetail(sub.id));
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
        <Text style={styles.title}>Subcategories</Text>
        <Button title={formOpen ? 'Cancel' : '+ Add'} variant={formOpen ? 'secondary' : 'primary'} onPress={() => setFormOpen((o) => !o)} />
      </View>

      {formOpen && (
        <Card style={{ marginHorizontal: spacing.md, marginBottom: spacing.sm, gap: spacing.sm }}>
          <Input label="Name" value={name} onChangeText={setName} />
          <SelectField label="Category" value={categoryId} onChange={setCategoryId} options={categories.map((c) => ({ label: c.name, value: c.id }))} />
          <Button title="Save" onPress={handleCreate} loading={submitting} />
        </Card>
      )}

      <View style={{ paddingHorizontal: spacing.md, marginBottom: spacing.sm }}>
        <Input placeholder="Search subcategories…" value={search} onChangeText={setSearch} />
      </View>

      <InfiniteCardList<Subcategory>
        fetchPage={fetchPage}
        resetKey={[search, refreshToken]}
        keyExtractor={(s) => s.id}
        emptyMessage="No subcategories found."
        renderItem={(s) => (
          <Card style={{ marginBottom: spacing.sm, gap: 4 }}>
            <Text style={styles.cardTitle}>{s.name}</Text>
            <Text style={styles.cardSub}>{s.category.name}</Text>
            <Button title="Delete" variant="danger" onPress={() => confirmDelete(s)} style={{ marginTop: 4, alignSelf: 'flex-start' }} />
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
});
