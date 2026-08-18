import { StyleSheet, Text, View } from 'react-native';
import { statusColors, colors, radius } from '../theme';

export function StatusBadge({ status }: { status: string }) {
  const color = statusColors[status] ?? colors.textSecondary;
  return (
    <View style={[styles.badge, { borderColor: color, backgroundColor: `${color}1a` }]}>
      <Text style={[styles.text, { color }]}>{status}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: radius.pill,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  text: { fontSize: 12, fontWeight: '600' },
});
