import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { User, AuthTokens, RegisterInput } from '@shared/types';
import { API_ENDPOINTS } from '@shared/constants';
import { apiClient, webTokenStorage } from '../lib/apiClient';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterInput) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const tokens = await webTokenStorage.getTokens();
      if (!tokens) {
        setIsLoading(false);
        return;
      }
      try {
        const res = await apiClient.get<User>(API_ENDPOINTS.me);
        setUser(res.data);
      } catch {
        await webTokenStorage.setTokens(null);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  async function login(email: string, password: string) {
    const res = await apiClient.post<{ user: User; tokens: AuthTokens }>(API_ENDPOINTS.login, { email, password });
    await webTokenStorage.setTokens(res.data.tokens);
    setUser(res.data.user);
  }

  async function register(data: RegisterInput) {
    const res = await apiClient.post<{ user: User; tokens: AuthTokens }>(API_ENDPOINTS.register, data);
    await webTokenStorage.setTokens(res.data.tokens);
    setUser(res.data.user);
  }

  function logout() {
    webTokenStorage.setTokens(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
