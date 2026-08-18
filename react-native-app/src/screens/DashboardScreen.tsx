import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../navigation/types';
import type { DashboardSummary } from '@shared/types';
import { ENTITY_NAV, API_ENDPOINTS, ROLE_ACCESS } from '@shared/constants';
import { apiClient } from '../lib/apiClient';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { BarChart } from '../components/BarChart';
import { useAuth } from '../context/AuthContext';
import { colors, spacing, radius } from '../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'Dashboard'>;

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <View style={styles.statTile}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
    </View>
  );
}

export function DashboardScreen({ navigation }: Props) {
  const { user, logout } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const role = user?.role;
  const showDashboard = role && ROLE_ACCESS.dashboard.includes(role);
  const showGrn = role && ROLE_ACCESS.grn.includes(role);
  const showMyDeliveries = role && ROLE_ACCESS.myDeliveries.includes(role);
  const showOrders = role && ROLE_ACCESS.orders.includes(role);
  const showMyOrders = role && ROLE_ACCESS.myOrders.includes(role);
  const showReports = role && ROLE_ACCESS.reports.includes(role);
  const showRegistrations = role && ROLE_ACCESS.registrations.includes(role);
  const showCatalogManage = role && ROLE_ACCESS.catalogManage.includes(role);

  useEffect(() => {
    if (!showDashboard) {
      setLoading(false);
      return;
    }
    apiClient.get<DashboardSummary>(API_ENDPOINTS.dashboard)
      .then((res) => setSummary(res.data))
      .finally(() => setLoading(false));
  }, [showDashboard]);

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: spacing.xl }}>
      <Text style={styles.title}>Welcome, {user?.full_name}</Text>
      <Text style={styles.subtitle}>{user?.role}</Text>

      {showDashboard && (loading || !summary ? (
        <Card style={{ marginTop: spacing.lg }}><Text style={styles.subtitle}>Loading overview…</Text></Card>
      ) : (
        <>
          <View style={styles.statGrid}>
            <StatTile label="Orders" value={summary.counts.orders} />
            <StatTile label="Revenue" value={`₹${summary.total_revenue.toFixed(0)}`} />
            <StatTile label="Products" value={summary.counts.products} />
            <StatTile label="Low Stock" value={summary.counts.low_stock_products} />
          </View>

          <Card style={{ marginTop: spacing.md, gap: spacing.sm }}>
            <Text style={styles.cardTitle}>Orders by Status</Text>
            <BarChart data={summary.order_status_breakdown.map((s) => ({ label: s.status, value: s.count }))} />
          </Card>

          <Card style={{ marginTop: spacing.md, gap: spacing.sm }}>
            <Text style={styles.cardTitle}>Inventory by Category</Text>
            <BarChart data={summary.inventory_by_category.map((c) => ({ label: c.category, value: c.quantity }))} />
          </Card>
        </>
      ))}

      {(showGrn || showMyDeliveries || showOrders || showMyOrders || showReports) && (
        <Card style={{ marginTop: spacing.lg, gap: spacing.md }}>
          {showGrn && <Button title="Goods Receipt Notes" onPress={() => navigation.navigate('GrnList')} />}
          {showMyDeliveries && <Button title="🚚 My Deliveries" onPress={() => navigation.navigate('GrnList')} />}
          {showOrders && <Button title="Orders" variant="secondary" onPress={() => navigation.navigate('OrderList')} />}
          {showMyOrders && <Button title="🧾 My Orders" onPress={() => navigation.navigate('OrderList')} />}
          {showReports && <Button title="📊 Reports" variant="secondary" onPress={() => navigation.navigate('ReportList')} />}
        </Card>
      )}

      {showRegistrations && (
        <>
          <Text style={styles.sectionTitle}>Registrations</Text>
          <Card style={{ gap: spacing.md }}>
            {ENTITY_NAV.map((item) => (
              <Button
                key={item.entity}
                title={`${item.icon} ${item.label}`}
                variant="secondary"
                onPress={() => navigation.navigate('EntityList', { entity: item.entity, label: item.label })}
              />
            ))}
          </Card>
        </>
      )}

      {showCatalogManage && (
        <>
          <Text style={styles.sectionTitle}>Catalog</Text>
          <Card style={{ gap: spacing.md }}>
            <Button title="🗂️ Categories" variant="secondary" onPress={() => navigation.navigate('CategoryList')} />
            <Button title="📁 Subcategories" variant="secondary" onPress={() => navigation.navigate('SubcategoryList')} />
            <Button title="📐 Units of Measurement" variant="secondary" onPress={() => navigation.navigate('UomList')} />
            <Button title="🛒 Products" variant="secondary" onPress={() => navigation.navigate('ProductList')} />
          </Card>
        </>
      )}

      <Card style={{ marginTop: spacing.lg, gap: spacing.md }}>
        <Button title="👤 My Profile" variant="secondary" onPress={() => navigation.navigate('Profile')} />
        <Button title="Sign out" variant="secondary" onPress={logout} />
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.lg, paddingTop: 80 },
  title: { fontSize: 24, fontWeight: '800', color: colors.textPrimary },
  subtitle: { fontSize: 14, color: colors.textSecondary, marginTop: 4 },
  sectionTitle: { fontSize: 14, fontWeight: '700', color: colors.textSecondary, marginTop: spacing.lg, marginBottom: spacing.sm, textTransform: 'uppercase' },
  cardTitle: { fontSize: 14, fontWeight: '700', color: colors.textPrimary },
  statGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.lg },
  statTile: {
    flexBasis: '47%',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.md,
  },
  statLabel: { fontSize: 12, fontWeight: '600', color: colors.textSecondary },
  statValue: { fontSize: 22, fontWeight: '800', color: colors.textPrimary, marginTop: 4 },
});
