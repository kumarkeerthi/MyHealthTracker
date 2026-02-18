'use client';

import { useState } from 'react';
import { AppModal } from '@/components/ui/AppModal';
import { useDashboardData } from '@/context/dashboard-data-context';
import { logHydration } from '@/lib/api';
import { useToast } from '@/components/ui/toast';

export default function WaterLogModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [amount, setAmount] = useState('250');
  const [loading, setLoading] = useState(false);
  const { refreshDashboard } = useDashboardData();
  const { show } = useToast();

  const submit = async () => {
    setLoading(true);
    try {
      await logHydration(Number(amount));
      show('success', 'Hydration updated');
      await refreshDashboard();
      onClose();
    } catch {
      show('error', 'Unable to log hydration');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppModal open={open} onClose={onClose} title="Log Water">
      <div className="space-y-3">
        <input aria-label="Water amount" className="w-full rounded bg-white/10 p-2" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <button className="rounded bg-cyan-600 px-4 py-2 disabled:opacity-60" disabled={loading} onClick={() => void submit()} type="button">{loading ? 'Saving...' : 'Save water'}</button>
      </div>
    </AppModal>
  );
}
