import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import type { Paginated } from '@shared/types';
import { colors, spacing } from '../theme';

interface InfiniteCardListProps<T> {
  fetchPage: (page: number) => Promise<Paginated<T>>;
  renderItem: (item: T) => React.ReactElement;
  keyExtractor: (item: T) => string;
  /** Changing this array resets the list to page 1 (e.g. when a filter/search changes). */
  resetKey: unknown[];
  emptyMessage?: string;
  ListHeaderComponent?: React.ReactElement;
}

export function InfiniteCardList<T>({
  fetchPage,
  renderItem,
  keyExtractor,
  resetKey,
  emptyMessage = 'No records found.',
  ListHeaderComponent,
}: InfiniteCardListProps<T>) {
  const [items, setItems] = useState<T[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(false);

  const load = useCallback(async (targetPage: number, replace: boolean) => {
    try {
      setError(false);
      const res = await fetchPage(targetPage);
      setItems((prev) => (replace ? res.results : [...prev, ...res.results]));
      setHasMore(res.next !== null);
      setPage(targetPage);
    } catch {
      setError(true);
    }
  }, [fetchPage]);

  useEffect(() => {
    setLoadingInitial(true);
    load(1, true).finally(() => setLoadingInitial(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, resetKey);

  async function onEndReached() {
    if (loadingMore || loadingInitial || !hasMore) return;
    setLoadingMore(true);
    await load(page + 1, false);
    setLoadingMore(false);
  }

  async function onRefresh() {
    setRefreshing(true);
    await load(1, true);
    setRefreshing(false);
  }

  if (loadingInitial) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} size="large" />
      </View>
    );
  }

  if (error && items.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyText}>Something went wrong loading this list.</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={keyExtractor}
      renderItem={({ item }) => renderItem(item)}
      ListHeaderComponent={ListHeaderComponent}
      ListEmptyComponent={<View style={styles.center}><Text style={styles.emptyText}>{emptyMessage}</Text></View>}
      contentContainerStyle={items.length === 0 ? { flexGrow: 1 } : { padding: spacing.md, gap: spacing.sm }}
      onEndReachedThreshold={0.4}
      onEndReached={onEndReached}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      ListFooterComponent={
        loadingMore ? (
          <View style={{ paddingVertical: spacing.md }}>
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : !hasMore && items.length > 0 ? (
          <Text style={styles.endText}>You've reached the end.</Text>
        ) : null
      }
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyText: { color: colors.textSecondary, fontSize: 14, textAlign: 'center' },
  endText: { textAlign: 'center', color: colors.textSecondary, fontSize: 12, padding: spacing.md },
});
