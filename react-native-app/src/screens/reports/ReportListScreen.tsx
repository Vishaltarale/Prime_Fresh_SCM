import { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../../navigation/types';
import type { ReportData } from '@shared/types';
import { API_ENDPOINTS, REPORT_NAV } from '@shared/constants';
import { apiClient, nativeTokenStorage } from '../../lib/apiClient';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AppStackParamList, 'ReportList'>;

export function ReportListScreen(_props: Props) {
  const [reportType, setReportType] = useState('inventory');
  const [threshold, setThreshold] = useState('10');
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<'pdf' | 'excel' | null>(null);

  useEffect(() => {
    setLoading(true);
    const params = reportType === 'low-stock' ? { threshold } : undefined;
    apiClient.get<ReportData>(API_ENDPOINTS.report(reportType), { params })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [reportType, threshold]);

  async function handleExport(format: 'pdf' | 'excel') {
    setExporting(format);
    try {
      const ext = format === 'pdf' ? 'pdf' : 'xlsx';
      const endpoint = format === 'pdf' ? API_ENDPOINTS.reportExportPdf(reportType) : API_ENDPOINTS.reportExportExcel(reportType);
      const fileUri = `${FileSystem.cacheDirectory}${reportType}_report.${ext}`;
      const tokens = await nativeTokenStorage.getTokens();
      const query = reportType === 'low-stock' ? `?threshold=${threshold}` : '';
      const download = await FileSystem.downloadAsync(
        `${apiClient.defaults.baseURL}${endpoint}${query}`,
        fileUri,
        { headers: tokens?.access ? { Authorization: `Bearer ${tokens.access}` } : {} }
      );
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(download.uri);
      } else {
        Alert.alert('Downloaded', `Saved to ${download.uri}`);
      }
    } catch {
      Alert.alert('Export failed', 'Please try again.');
    } finally {
      setExporting(null);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Reports</Text>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipsRow} contentContainerStyle={{ gap: 8, paddingHorizontal: spacing.md }}>
        {REPORT_NAV.map((r) => (
          <Button
            key={r.type}
            title={`${r.icon} ${r.label}`}
            variant={r.type === reportType ? 'primary' : 'secondary'}
            onPress={() => setReportType(r.type)}
          />
        ))}
      </ScrollView>

      {reportType === 'low-stock' && (
        <View style={{ paddingHorizontal: spacing.md, marginTop: spacing.sm }}>
          <Input label="Threshold" keyboardType="numeric" value={threshold} onChangeText={setThreshold} />
        </View>
      )}

      <View style={{ flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.md, marginTop: spacing.sm }}>
        <Button title="Export PDF" variant="secondary" onPress={() => handleExport('pdf')} loading={exporting === 'pdf'} style={{ flex: 1 }} />
        <Button title="Export Excel" variant="secondary" onPress={() => handleExport('excel')} loading={exporting === 'excel'} style={{ flex: 1 }} />
      </View>

      <ScrollView contentContainerStyle={{ padding: spacing.md, gap: spacing.sm }}>
        {loading ? (
          <Text style={styles.muted}>Loading…</Text>
        ) : !data || data.rows.length === 0 ? (
          <Text style={styles.muted}>No data for this report.</Text>
        ) : (
          <>
            {data.summary && (
              <Card style={{ marginBottom: spacing.sm }}>
                <Text style={styles.summary}>{data.summary}</Text>
              </Card>
            )}
            {data.rows.map((row, i) => (
              <Card key={i} style={{ gap: 2 }}>
                {row.map((cell, j) => (
                  <Text key={j} style={styles.fieldLine}>
                    <Text style={styles.fieldLabel}>{data.headers[j]}: </Text>
                    {String(cell)}
                  </Text>
                ))}
              </Card>
            ))}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, paddingTop: 60 },
  title: { fontSize: 22, fontWeight: '800', color: colors.textPrimary, paddingHorizontal: spacing.md, marginBottom: spacing.sm },
  chipsRow: { flexGrow: 0, marginBottom: spacing.sm },
  muted: { fontSize: 13, color: colors.textSecondary, padding: spacing.md },
  summary: { fontSize: 15, fontWeight: '700', color: colors.textPrimary },
  fieldLine: { fontSize: 13, color: colors.textPrimary },
  fieldLabel: { fontWeight: '700', color: colors.textSecondary },
});
