'use client';

import { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import { BottomSheet, type ActivityType } from '@/components/ui/BottomSheet';
import { FloatingActionButton } from '@/components/ui/FloatingActionButton';

const MealLogModal = lazy(() => import('@/components/modals/MealLogModal'));
const WaterLogModal = lazy(() => import('@/components/modals/WaterLogModal'));
const ExerciseLogModal = lazy(() => import('@/components/modals/ExerciseLogModal'));
const VitalLogModal = lazy(() => import('@/components/modals/VitalLogModal'));
const ReportUploadModal = lazy(() => import('@/components/modals/ReportUploadModal'));

export function ActivityHub() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [activeModal, setActiveModal] = useState<ActivityType | null>(null);

  const closeModal = () => setActiveModal(null);

  useEffect(() => {
    const handler = (event: Event) => {
      const custom = event as CustomEvent<ActivityType>;
      setActiveModal(custom.detail);
      setSheetOpen(false);
    };
    window.addEventListener('open-activity-modal', handler as EventListener);
    return () => window.removeEventListener('open-activity-modal', handler as EventListener);
  }, []);


  const modal = useMemo(() => {
    if (!activeModal) return null;
    if (activeModal === 'meal') return <MealLogModal open onClose={closeModal} />;
    if (activeModal === 'water') return <WaterLogModal open onClose={closeModal} />;
    if (activeModal === 'exercise') return <ExerciseLogModal open onClose={closeModal} />;
    if (activeModal === 'vital') return <VitalLogModal open onClose={closeModal} />;
    return <ReportUploadModal open onClose={closeModal} />;
  }, [activeModal]);

  const onSelect = (activity: ActivityType) => {
    setSheetOpen(false);
    setActiveModal(activity);
  };

  return (
    <>
      <FloatingActionButton onClick={() => setSheetOpen(true)} />
      <BottomSheet open={sheetOpen} onClose={() => setSheetOpen(false)} onSelect={onSelect} />
      <Suspense fallback={null}>{modal}</Suspense>
    </>
  );
}
