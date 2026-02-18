'use client';

import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { getAccessToken, getMe, logout as logoutRequest, refreshAccessToken, setAccessToken, type AuthMe } from '@/lib/api';

type AuthContextValue = {
  token: string | null;
  user: AuthMe | null;
  loading: boolean;
  setToken: (token: string | null) => void;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const PUBLIC_PATHS = new Set(['/login', '/register']);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<AuthMe | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const setToken = (value: string | null) => {
    setAccessToken(value);
    setTokenState(value);
  };

  const logout = async () => {
    await logoutRequest();
    setToken(null);
    setUser(null);
    router.replace('/login');
  };

  useEffect(() => {
    const bootstrapAuth = async () => {
      const refreshed = await refreshAccessToken();
      if (!refreshed) {
        setToken(null);
        setUser(null);
        setLoading(false);
        if (!PUBLIC_PATHS.has(pathname)) {
          router.replace('/login');
        }
        return;
      }

      const nextToken = getAccessToken();
      setTokenState(nextToken);
      const profile = await getMe();
      if (!profile) {
        await logout();
        setLoading(false);
        return;
      }
      setUser(profile);
      setLoading(false);
      if (pathname === '/login' || pathname === '/register') {
        router.replace('/');
      }
    };

    bootstrapAuth();
  }, [pathname, router]);

  const value = useMemo(() => ({ token, user, loading, setToken, logout }), [token, user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
