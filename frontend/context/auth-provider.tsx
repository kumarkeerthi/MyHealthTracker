'use client';

import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { getMe, type AuthMe } from '@/lib/api';

type AuthContextValue = {
  token: string | null;
  user: AuthMe | null;
  loading: boolean;
  setToken: (token: string | null) => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<AuthMe | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const setToken = (value: string | null) => {
    if (value) {
      localStorage.setItem('token', value);
    } else {
      localStorage.removeItem('token');
    }
    setTokenState(value);
  };

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      setLoading(false);
      if (pathname !== '/login') {
        router.replace('/login');
      }
      return;
    }

    setTokenState(storedToken);
    getMe(storedToken)
      .then((profile) => {
        if (!profile) {
          setToken(null);
          router.replace('/login');
          return;
        }
        setUser(profile);
      })
      .finally(() => setLoading(false));
  }, [pathname, router]);

  const value = useMemo(() => ({ token, user, loading, setToken }), [token, user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
