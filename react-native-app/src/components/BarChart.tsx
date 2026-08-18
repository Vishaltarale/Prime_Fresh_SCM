import { StyleSheet, Text, View } from 'react-native';
import { colors, radius, spacing } from '../theme';

// Fixed-order categorical palette (validated for CVD-safe adjacent contrast) — see dataviz skill.
const CATEGORICAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'];

interface BarChartProps {
  data: Array<{ label: string; value: number }>;
  emptyMessage?: string;
}

export function BarChart({ data, emptyMessage = 'No data yet.' }: BarChartProps) {
  if (data.length === 0) {
    return <Text style={styles.empty}>{emptyMessage}</Text>;
  }
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <View style={{ gap: spacing.sm }}>
      {data.map((d, i) => (
        <View key={d.label} style={{ gap: 4 }}>
          <View style={styles.labelRow}>
            <Text style={styles.label} numberOfLines={1}>{d.label}</Text>
            <Text style={styles.value}>{d.value}</Text>
          </View>
          <View style={styles.track}>
            <View style={[styles.fill, { width: `${Math.max((d.value / max) * 100, 4)}%`, backgroundColor: CATEGORICAL[i % CATEGORICAL.length] }]} />
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  empty: { fontSize: 13, color: colors.textSecondary },
  labelRow: { flexDirection: 'row', justifyContent: 'space-between' },
  label: { fontSize: 13, fontWeight: '600', color: colors.textPrimary, flex: 1, marginRight: 8 },
  value: { fontSize: 13, fontWeight: '700', color: colors.textSecondary },
  track: { height: 10, borderRadius: radius.pill, backgroundColor: colors.background, overflow: 'hidden' },
  fill: { height: '100%', borderRadius: radius.pill },
});
