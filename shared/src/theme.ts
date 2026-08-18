// Shared design tokens for React web and React Native.
// Consumers (web: CSS variables/Tailwind config, native: StyleSheet) both read from this single source.
export const colors = {
  primary: '#6D28D9',
  primaryDark: '#4C1D95',
  primaryLight: '#A78BFA',
  accent: '#4F46E5',
  success: '#16A34A',
  warning: '#D97706',
  danger: '#DC2626',
  background: '#F8FAFC',
  surface: '#FFFFFF',
  border: '#E2E8F0',
  textPrimary: '#0F172A',
  textSecondary: '#64748B',
  textInverse: '#FFFFFF',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const radius = {
  sm: 6,
  md: 10,
  lg: 16,
  pill: 999,
};

export const typography = {
  fontFamily: 'Inter, system-ui, sans-serif',
  sizes: { xs: 12, sm: 14, base: 16, lg: 18, xl: 22, xxl: 28 },
  weights: { regular: 400, medium: 500, semibold: 600, bold: 700 },
};

export const statusColors: Record<string, string> = {
  Draft: colors.warning,
  Confirmed: colors.success,
  Rejected: colors.danger,
};
