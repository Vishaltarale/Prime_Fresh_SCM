import { useCallback, useState } from 'react';
import { Alert, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { CatalogProduct } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient } from '../../lib/apiClient';
import { InfiniteCardList } from '../../components/InfiniteCardList';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'ProductList'>;

export function ProductListScreen({ navigation }: Props) {
  const [search, setSearch] = useState('');
  const [refreshToken, setRefreshToken] = useState(0);

  const fetchPage = useCallback(async (page: number) => {
    const res = await apiClient.get(API_ENDPOINTS.catalogProducts, { params: { search, page } });
    return res.data;
  }, [search]);

  function confirmDelete(product: CatalogProduct) {
    Alert.alert('Delete?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive', onPress: async () => {
          await apiClient.delete(API_ENDPOINTS.catalogProductDetail(product.id));
          setRefreshToken((t) => t + 1);
        },
      },
    ]);
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Products</Text>
        <Button title="+ New" onPress={() => navigation.navigate('ProductCreate')} />
      </View>

      <View style={{ paddingHorizontal: spacing.md, marginBottom: spacing.sm }}>
        <Input placeholder="Search name or SKU…" value={search} onChangeText={setSearch} />
      </View>

      <InfiniteCardList<CatalogProduct>
        fetchPage={fetchPage}
        resetKey={[search, refreshToken]}
        keyExtractor={(p) => p.id}
        emptyMessage="No products found."
        renderItem={(p) => (
          <Card style={{ marginBottom: spacing.sm, gap: 4 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={styles.cardTitle}>{p.name}</Text>
              <Text style={styles.cardSub}>{p.sku}</Text>
            </View>
            <Text style={styles.cardSub}>{p.category?.name} · {p.warehouse?.name}</Text>
            <Text style={styles.cardPrice}>₹{p.price_per_unit.toFixed(2)} / {p.uom?.name}</Text>
            <Text style={styles.cardSub}>Qty: {p.quantity_available}</Text>
            <Button title="Delete" variant="danger" onPress={() => confirmDelete(p)} style={{ marginTop: 4, alignSelf: 'flex-start' }} />
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
  cardPrice: { fontSize: 18, fontWeight: '700', color: colors.textPrimary },
});
