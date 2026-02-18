'use client';

import { Plus } from 'lucide-react';
import { useAuth } from '@/context/auth-provider';

export function FloatingActionButton({ onClick }: { onClick: () => void }) {
  const { token, user } = useAuth();
  if (!token || !user) return null;

  return (
    <button
      type="button"
      aria-label="Log activity"
      onClick={onClick}
      className="fixed bottom-6 right-6 z-[60] flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 via-blue-500 to-violet-600 text-white shadow-[0_16px_35px_rgba(59,130,246,0.45)] transition hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
    >
      <Plus size={24} />
    </button>
  );
}
