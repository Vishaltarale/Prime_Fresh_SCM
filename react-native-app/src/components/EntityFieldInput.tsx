import { StyleSheet, Switch, Text, View } from 'react-native';
import type { EntityField } from '@shared/types';
import { Input } from './Input';
import { SelectField } from './SelectField';
import { colors } from '../theme';

interface EntityFieldInputProps {
  field: EntityField;
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export function EntityFieldInput({ field, value, onChange, error }: EntityFieldInputProps) {
  if (field.type === 'select' && field.choices) {
    return (
      <SelectField
        label={field.label}
        value={value}
        onChange={onChange}
        options={field.choices.map((c) => ({ label: c, value: c }))}
        error={error}
      />
    );
  }

  if (field.type === 'bool') {
    return (
      <View style={styles.switchRow}>
        <Text style={styles.switchLabel}>{field.label}</Text>
        <Switch value={value === 'true'} onValueChange={(v) => onChange(String(v))} trackColor={{ true: colors.primary }} />
      </View>
    );
  }

  return (
    <Input
      label={field.label}
      value={field.type === 'date' ? value.slice(0, 10) : value}
      onChangeText={onChange}
      placeholder={field.type === 'date' ? 'YYYY-MM-DD' : undefined}
      keyboardType={field.type === 'email' ? 'email-address' : 'default'}
      autoCapitalize={field.type === 'email' ? 'none' : 'sentences'}
      multiline={field.type === 'textarea'}
      error={error}
    />
  );
}

const styles = StyleSheet.create({
  switchRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  switchLabel: { fontSize: 14, fontWeight: '600', color: colors.textSecondary },
});
