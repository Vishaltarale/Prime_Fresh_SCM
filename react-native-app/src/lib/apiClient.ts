import * as SecureStore from 'expo-secure-store';
import { createApiClient, type TokenStorage } from '@shared/apiClient';
import type { AuthTokens } from '@shared/types';

const STORAGE_KEY = 'primefresh_tokens';

const nativeTokenStorage: TokenStorage = {
  getTokens: async () => {
    const raw = await SecureStore.getItemAsync(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuthTokens) : null;
  },
  setTokens: async (tokens) => {
    if (tokens) {
      await SecureStore.setItemAsync(STORAGE_KEY, JSON.stringify(tokens));
    } else {
      await SecureStore.deleteItemAsync(STORAGE_KEY);
    }
  },
};

const baseURL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

export const apiClient = createApiClient(baseURL, nativeTokenStorage);
export { nativeTokenStorage };
