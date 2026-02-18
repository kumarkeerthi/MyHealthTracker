'use client';

import { useState } from 'react';
import { AppModal } from '@/components/ui/AppModal';
import { useDashboardData } from '@/context/dashboard-data-context';
import { logFood } from '@/lib/api';
import { useToast } from '@/components/ui/toast';

export default function MealLogModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [foodId, setFoodId] = useState('1');
  const [servings, setServings] = useState('1');
  const [loading, setLoading] = useState(false);
  const { refreshDashboard } = useDashboardData();
  const { show } = useToast();

  const submit = async () => {
    setLoading(true);
    try {
      await logFood({ entries: [{ food_item_id: Number(foodId), servings: Number(servings) }], meal_context: 'snack' });
      show('success', 'Meal logged successfully');
      await refreshDashboard();
      onClose();
    } catch {
      show('error', 'Unable to log meal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppModal open={open} onClose={onClose} title="Log Meal">
      <div className="space-y-3">
        <input aria-label="Food item id" className="w-full rounded bg-white/10 p-2" value={foodId} onChange={(e) => setFoodId(e.target.value)} />
        <input aria-label="Servings" className="w-full rounded bg-white/10 p-2" value={servings} onChange={(e) => setServings(e.target.value)} />
        <button className="rounded bg-cyan-600 px-4 py-2 disabled:opacity-60" disabled={loading} onClick={() => void submit()} type="button">{loading ? 'Saving...' : 'Save meal'}</button>
      </div>
    </AppModal>
  );
}
