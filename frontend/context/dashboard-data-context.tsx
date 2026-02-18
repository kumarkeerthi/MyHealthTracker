'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { getDashboardData } from '@/lib/api';
import { useAuth } from '@/context/auth-provider';

type DashboardDataValue = {
  data: Awaited<ReturnType<typeof getDashboardData>> | null;
  loading: boolean;
  refreshDashboard: () => Promise<void>;
};

const DashboardDataContext = createContext<DashboardDataValue | undefined>(undefined);

export function DashboardDataProvider({ children }: { children: React.ReactNode }) {
  const { token, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<Awaited<ReturnType<typeof getDashboardData>> | null>(null);

  const refreshDashboard = useCallback(async () => {
    if (!token || !user) return;
    setLoading(true);
    try {
      const next = await getDashboardData(user.id);
      setData(next);
    } finally {
      setLoading(false);
    }
  }, [token, user]);

  useEffect(() => {
    void refreshDashboard();
  }, [refreshDashboard]);

  const value = useMemo(() => ({ data, loading, refreshDashboard }), [data, loading, refreshDashboard]);

  return <DashboardDataContext.Provider value={value}>{children}</DashboardDataContext.Provider>;
}

export function useDashboardData() {
  const context = useContext(DashboardDataContext);
  if (!context) {
    throw new Error('useDashboardData must be used inside DashboardDataProvider');
  }
  return context;
}
