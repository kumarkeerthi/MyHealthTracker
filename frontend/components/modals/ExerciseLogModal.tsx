'use client';

import { useState } from 'react';
import { AppModal } from '@/components/ui/AppModal';
import { useDashboardData } from '@/context/dashboard-data-context';
import { logExercise } from '@/lib/api';
import { useToast } from '@/components/ui/toast';

export default function ExerciseLogModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [activity, setActivity] = useState('Bodyweight session');
  const [duration, setDuration] = useState('20');
  const [loading, setLoading] = useState(false);
  const { refreshDashboard } = useDashboardData();
  const { show } = useToast();

  const submit = async () => {
    setLoading(true);
    try {
      await logExercise({ activity_type: activity, duration_minutes: Number(duration) });
      show('success', 'Exercise logged');
      await refreshDashboard();
      onClose();
    } catch {
      show('error', 'Unable to log exercise');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppModal open={open} onClose={onClose} title="Log Exercise">
      <div className="space-y-3">
        <input aria-label="Activity" className="w-full rounded bg-white/10 p-2" value={activity} onChange={(e) => setActivity(e.target.value)} />
        <input aria-label="Duration" className="w-full rounded bg-white/10 p-2" value={duration} onChange={(e) => setDuration(e.target.value)} />
        <button className="rounded bg-cyan-600 px-4 py-2 disabled:opacity-60" disabled={loading} onClick={() => void submit()} type="button">{loading ? 'Saving...' : 'Save exercise'}</button>
      </div>
    </AppModal>
  );
}
