import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { AuthTokens } from './types';

export type { AuthTokens };

export interface TokenStorage {
  getTokens: () => Promise<AuthTokens | null>;
  setTokens: (tokens: AuthTokens | null) => Promise<void>;
}

// Web (localStorage) and native (expo-secure-store) each provide their own
// TokenStorage implementation; the refresh/interceptor logic below is shared.
export function createApiClient(baseURL: string, storage: TokenStorage): AxiosInstance {
  const client = axios.create({ baseURL });

  client.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
    const tokens = await storage.getTokens();
    if (tokens?.access) {
      config.headers.Authorization = `Bearer ${tokens.access}`;
    }
    return config;
  });

  let refreshing: Promise<string | null> | null = null;

  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
      if (!original) return Promise.reject(error);
      if (error.response?.status === 401 && !original._retry) {
        original._retry = true;
        const tokens = await storage.getTokens();
        if (!tokens?.refresh) {
          await storage.setTokens(null);
          return Promise.reject(error);
        }

        if (!refreshing) {
          refreshing = axios
            .post<{ access: string }>(`${baseURL}/auth/refresh/`, { refresh: tokens.refresh })
            .then(async (res) => {
              const newTokens = { access: res.data.access, refresh: tokens.refresh };
              await storage.setTokens(newTokens);
              return newTokens.access as string;
            })
            .catch(async () => {
              await storage.setTokens(null);
              return null;
            })
            .finally(() => {
              refreshing = null;
            });
        }

        const newAccess = await refreshing;
        if (newAccess) {
          original.headers.Authorization = `Bearer ${newAccess}`;
          return client(original);
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
}
