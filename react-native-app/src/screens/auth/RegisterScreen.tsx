import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AuthStackParamList } from '../../navigation/types';
import type { RegisterInput, Role } from '@shared/types';
import { Input } from '../../components/Input';
import { SelectField } from '../../components/SelectField';
import { Button } from '../../components/Button';
import { useAuth } from '../../context/AuthContext';
import { STAFF_ROLES, EXTERNAL_ROLES, REGISTER_PROFILE_FIELDS } from '@shared/constants';
import { colors, spacing } from '../../theme';

type Props = NativeStackScreenProps<AuthStackParamList, 'Register'>;

const FIELD_LABELS: Record<string, string> = {
  address: 'Address',
  city: 'City',
  state: 'State',
  district: 'District',
  village: 'Village',
  company_name: 'Company Name',
};

const emptyForm: RegisterInput = {
  full_name: '', email: '', phone: '', password: '', role: 'Customer',
  address: '', city: '', state: '', district: '', village: '', company_name: '',
};

const ROLE_OPTIONS = [...EXTERNAL_ROLES, ...STAFF_ROLES].map((r) => ({ label: r, value: r }));

export function RegisterScreen({ navigation }: Props) {
  const { register } = useAuth();
  const [form, setForm] = useState<RegisterInput>(emptyForm);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function update<K extends keyof RegisterInput>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  const profileFields = REGISTER_PROFILE_FIELDS[form.role] ?? [];

  async function handleSubmit() {
    setError('');
    setLoading(true);
    try {
      await register(form);
    } catch (err: unknown) {
      const respData = (err as { response?: { data?: Record<string, string> } })?.response?.data;
      setError(respData ? Object.values(respData).join(' ') : 'Registration failed. Check your details and try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: colors.background }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Create account</Text>
        <Text style={styles.subtitle}>Register a new Prime Fresh SCM account</Text>

        <View style={{ gap: spacing.md, marginTop: spacing.lg }}>
          <Input label="Full name" value={form.full_name} onChangeText={(v) => update('full_name', v)} />
          <Input label="Email" autoCapitalize="none" keyboardType="email-address" value={form.email} onChangeText={(v) => update('email', v)} />
          <Input label="Phone" keyboardType="phone-pad" value={form.phone} onChangeText={(v) => update('phone', v)} />
          <SelectField
            label="I am a…"
            value={form.role}
            onChange={(v) => update('role', v as Role)}
            options={ROLE_OPTIONS}
          />

          {profileFields.map((field) => (
            <Input
              key={field}
              label={FIELD_LABELS[field]}
              value={(form[field as keyof RegisterInput] as string) ?? ''}
              onChangeText={(v) => update(field as keyof RegisterInput, v)}
            />
          ))}

          <Input label="Password" secureTextEntry value={form.password} onChangeText={(v) => update('password', v)} />
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <Button title="Create account" onPress={handleSubmit} loading={loading} />
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Already registered?</Text>
          <Text style={styles.link} onPress={() => navigation.navigate('Login')}> Sign in</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg, paddingTop: 80, paddingBottom: 40 },
  title: { fontSize: 28, fontWeight: '800', color: colors.textPrimary },
  subtitle: { fontSize: 14, color: colors.textSecondary, marginTop: 4 },
  error: { color: colors.danger, fontSize: 13 },
  footer: { flexDirection: 'row', justifyContent: 'center', marginTop: spacing.lg },
  footerText: { color: colors.textSecondary, fontSize: 13 },
  link: { color: colors.primary, fontWeight: '700', fontSize: 13 },
});
