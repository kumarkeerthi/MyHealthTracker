'use client';

import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

export type ActivityType = 'meal' | 'water' | 'exercise' | 'vital' | 'report';

const options: Array<{ key: ActivityType; label: string; icon: string }> = [
  { key: 'meal', label: 'Meal', icon: '🍽' },
  { key: 'water', label: 'Water', icon: '💧' },
  { key: 'exercise', label: 'Exercise', icon: '🏋' },
  { key: 'vital', label: 'Vital', icon: '❤️' },
  { key: 'report', label: 'Upload Report', icon: '📄' },
];

export function BottomSheet({ open, onClose, onSelect }: { open: boolean; onClose: () => void; onSelect: (activity: ActivityType) => void }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab' && ref.current) {
        const nodes = ref.current.querySelectorAll<HTMLElement>('button');
        if (!nodes.length) return;
        const first = nodes[0];
        const last = nodes[nodes.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener('keydown', onKey);
    setTimeout(() => ref.current?.querySelector('button')?.focus(), 0);
    return () => {
      document.body.style.overflow = prevOverflow;
      document.removeEventListener('keydown', onKey);
    };
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.div
            role="button"
            tabIndex={0}
            aria-label="Close logging menu"
            className="fixed inset-0 z-[70] bg-black/60"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={(event: React.MouseEvent<HTMLDivElement>) => {
              event.preventDefault();
              onClose();
            }}
            onKeyDown={(event: React.KeyboardEvent<HTMLDivElement>) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onClose();
              }
            }}
          />
          <motion.div role="dialog" aria-modal="true" aria-label="Log Activity" ref={ref} className="fixed inset-x-0 bottom-0 z-[80] rounded-t-3xl border border-white/20 bg-slate-950 p-5" initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }} transition={{ duration: 0.22 }}>
            <h2 className="mb-4 text-lg font-semibold">Log Activity</h2>
            <div className="grid grid-cols-2 gap-3">
              {options.map((item) => (
                <button key={item.key} aria-label={`Log ${item.label}`} className="rounded-xl border border-white/15 bg-white/5 px-3 py-4 text-left hover:bg-white/10" onClick={() => onSelect(item.key)} type="button">
                  <div className="text-xl">{item.icon}</div>
                  <div className="mt-2 text-sm">{item.label}</div>
                </button>
              ))}
            </div>
          </motion.div>
        </>
      ) : null}
    </AnimatePresence>
  );
}
