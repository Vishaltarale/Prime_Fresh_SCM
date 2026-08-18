import { createApiClient, type TokenStorage } from '@shared/apiClient';
import type { AuthTokens } from '@shared/types';

const STORAGE_KEY = 'primefresh_tokens';

const webTokenStorage: TokenStorage = {
  getTokens: async () => {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuthTokens) : null;
  },
  setTokens: async (tokens) => {
    if (tokens) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  },
};

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const apiClient = createApiClient(baseURL, webTokenStorage);
export { webTokenStorage };
