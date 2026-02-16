import { motion } from 'framer-motion';
import { NeutralBodyOutline, StrengthOverlay } from '@/components/visuals/body-assets';
import type { BodyVisualState, StrengthVisualState } from '@/components/visuals/visual-logic';

function ProgressRow({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-slate-300"><span>{label}</span><span>{value.toFixed(0)}%</span></div>
      <div className="h-2 rounded-full bg-slate-800"><motion.div className="h-2 rounded-full bg-gradient-to-r from-emerald-400 to-electric" initial={{ width: 0 }} animate={{ width: `${value}%` }} transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }} /></div>
    </div>
  );
}

export function StrengthView({ bodyState, strengthState }: { bodyState: BodyVisualState; strengthState: StrengthVisualState }) {
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (strengthState.strengthIndex / 100) * circumference;

  return (
    <section className="space-y-4">
      <div className="glass-card p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Upper body focus</p>
        <div className="relative mx-auto mt-2 w-52">
          <NeutralBodyOutline state={bodyState} className="opacity-65" />
          <div className="absolute inset-0"><StrengthOverlay state={strengthState} /></div>
        </div>
      </div>

      <div className="glass-card p-4 text-center">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Strength Index Meter</p>
        <motion.svg viewBox="0 0 140 140" className="mx-auto mt-2 h-40 w-40" initial={{ rotate: -90 }} animate={{ rotate: -90 }}>
          <circle cx="70" cy="70" r="54" stroke="rgba(71,85,105,0.45)" strokeWidth="12" fill="none" />
          <circle cx="70" cy="70" r="54" stroke="rgba(16,185,129,0.95)" strokeWidth="12" fill="none" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" style={{ transition: "stroke-dashoffset 320ms cubic-bezier(0.22,1,0.36,1)" }} />
          <text x="70" y="76" textAnchor="middle" fill="white" fontSize="24" transform="rotate(90 70 70)">{strengthState.strengthIndex.toFixed(0)}</text>
        </motion.svg>
      </div>

      <div className="glass-card space-y-3 p-4">
        <ProgressRow label="Grip Endurance" value={strengthState.gripEndurancePct} />
        <ProgressRow label="Pull Strength" value={strengthState.pullStrengthPct} />
      </div>
    </section>
  );
}
