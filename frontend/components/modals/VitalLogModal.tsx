'use client';

import { useState } from 'react';
import { AppModal } from '@/components/ui/AppModal';
import { useDashboardData } from '@/context/dashboard-data-context';
import { logVitals } from '@/lib/api';
import { useToast } from '@/components/ui/toast';

export default function VitalLogModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [restingHr, setRestingHr] = useState('70');
  const [sleepHours, setSleepHours] = useState('7');
  const [loading, setLoading] = useState(false);
  const { refreshDashboard } = useDashboardData();
  const { show } = useToast();

  const submit = async () => {
    setLoading(true);
    try {
      await logVitals({ resting_hr: Number(restingHr), sleep_hours: Number(sleepHours) });
      show('success', 'Vitals logged');
      await refreshDashboard();
      onClose();
    } catch {
      show('error', 'Unable to log vitals');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppModal open={open} onClose={onClose} title="Log Vital">
      <div className="space-y-3">
        <input aria-label="Resting heart rate" className="w-full rounded bg-white/10 p-2" value={restingHr} onChange={(e) => setRestingHr(e.target.value)} />
        <input aria-label="Sleep hours" className="w-full rounded bg-white/10 p-2" value={sleepHours} onChange={(e) => setSleepHours(e.target.value)} />
        <button className="rounded bg-cyan-600 px-4 py-2 disabled:opacity-60" disabled={loading} onClick={() => void submit()} type="button">{loading ? 'Saving...' : 'Save vitals'}</button>
      </div>
    </AppModal>
  );
}
