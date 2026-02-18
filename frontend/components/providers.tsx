'use client';

import { AuthProvider } from '@/context/auth-provider';
import { DashboardDataProvider } from '@/context/dashboard-data-context';
import { ToastProvider } from '@/components/ui/toast';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <DashboardDataProvider>
        <ToastProvider>{children}</ToastProvider>
      </DashboardDataProvider>
    </AuthProvider>
  );
}
