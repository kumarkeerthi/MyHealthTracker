'use client';

import { createContext, useContext, useMemo, useState } from 'react';

type Toast = { id: number; kind: 'success' | 'error'; message: string };

const ToastContext = createContext<{ show: (kind: Toast['kind'], message: string) => void } | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const show = (kind: Toast['kind'], message: string) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, kind, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 2800);
  };

  const value = useMemo(() => ({ show }), []);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 top-4 z-[90] space-y-2">
        {toasts.map((toast) => (
          <div key={toast.id} className={`rounded-xl px-4 py-2 text-sm shadow-lg ${toast.kind === 'success' ? 'bg-emerald-500/90' : 'bg-rose-500/90'}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}
