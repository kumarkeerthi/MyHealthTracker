'use client';

import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

export function AppModal({ open, title, onClose, children }: { open: boolean; title: string; onClose: () => void; children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    setTimeout(() => ref.current?.querySelector<HTMLElement>('input,button,select,textarea')?.focus(), 0);
    return () => {
      document.body.style.overflow = prevOverflow;
      document.removeEventListener('keydown', onKey);
    };
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.button className="fixed inset-0 z-[81] bg-black/70" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} aria-label="Close modal" />
          <motion.section role="dialog" aria-modal="true" aria-label={title} ref={ref} className="fixed inset-x-4 top-1/2 z-[82] max-h-[90vh] -translate-y-1/2 overflow-auto rounded-2xl border border-white/20 bg-slate-900 p-5" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 12 }}>
            <h3 className="mb-4 text-lg font-semibold">{title}</h3>
            {children}
          </motion.section>
        </>
      ) : null}
    </AnimatePresence>
  );
}
