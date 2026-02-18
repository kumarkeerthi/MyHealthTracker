import type { ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Droplets, Moon, Target, Zap } from 'lucide-react';

type Props = {
  onQuickAddWater: () => void;
  onOpenWaterModal: () => void;
  insulinScore: number;
  compliance: number;
  hydrationScore: number;
  waterMl: number;
  sleepHours: number;
  protein: number;
  carbs: number;
  oil: number;
  proteinHit: boolean;
  carbUnderCeiling: boolean;
  hydrationTargetAchieved: boolean;
  strengthLogged: boolean;
  dinnerLogged: boolean;
  dinnerCarbs: number;
  dinnerProtein: number;
  dinnerMode: string | null;
  dinnerInsulinImpact: number;
  eveningInsulinSpikeRisk: boolean;
};

function MetricCard({ label, value, icon, accent = false }: { label: string; value: string; icon: ReactNode; accent?: boolean }) {
  return (
    <motion.div className="glass-card p-4" transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}>
      <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-400">{icon}{label}</p>
      <motion.div className={`mt-2 text-2xl font-semibold ${accent ? 'text-emerald-200' : 'text-white'}`} key={value} initial={{ opacity: 0.5, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.28 }}>
        {value}
      </motion.div>
    </motion.div>
  );
}

export function DashboardView({ insulinScore, compliance, hydrationScore, waterMl, sleepHours, protein, carbs, oil, proteinHit, carbUnderCeiling, hydrationTargetAchieved, strengthLogged, dinnerLogged, dinnerCarbs, dinnerProtein, dinnerMode, dinnerInsulinImpact, eveningInsulinSpikeRisk, onQuickAddWater, onOpenWaterModal }: Props) {
  const dayComplete = proteinHit && carbUnderCeiling && hydrationTargetAchieved && strengthLogged;

  return (
    <section className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="Insulin" value={insulinScore.toFixed(0)} icon={<Zap size={14} />} />
        <MetricCard label="Compliance" value={`${compliance}%`} icon={<Target size={14} />} accent={proteinHit} />
        <button type="button" onClick={onQuickAddWater} onContextMenu={(e) => { e.preventDefault(); onOpenWaterModal(); }} onTouchStart={() => { const timer = setTimeout(onOpenWaterModal, 650); const clear = () => { clearTimeout(timer); window.removeEventListener('touchend', clear); }; window.addEventListener('touchend', clear); }} className="text-left">
          <MetricCard label="Hydration" value={`${hydrationScore.toFixed(0)}%`} icon={<Droplets size={14} />} />
        </button>
        <MetricCard label="Sleep" value={`${sleepHours.toFixed(1)}h`} icon={<Moon size={14} />} />
      </div>

      <div className="glass-card p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Daily Macro Metrics</p>
        <div className="mt-3 space-y-2 text-sm text-slate-200">
          <motion.div className="flex justify-between" animate={proteinHit ? { scale: [1, 1.01, 1] } : { scale: 1 }} transition={{ duration: 0.32 }}><span>Muscle supported</span><span>{protein.toFixed(1)} g</span></motion.div>
          <div className="flex justify-between"><span>Triglyceride recovery active</span><span>{carbs.toFixed(1)} g</span></div>
          <div className="flex justify-between"><span>Hidden Oil</span><span>{oil.toFixed(1)} tsp</span></div>
          <div className="flex justify-between"><span>Water</span><span>{waterMl.toFixed(0)} ml</span></div>
          <div className="h-2 rounded bg-white/10"><motion.div className="h-full rounded bg-cyan-400" animate={{ width: `${Math.max(0, Math.min(100, hydrationScore))}%` }} transition={{ duration: 0.4 }} /></div>
        </div>
      </div>

      <div className="glass-card p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Dinner</p>
        {!dinnerLogged ? (
          <p className="mt-2 text-sm text-slate-300">Dinner is optional. Use low-carb or protein-only mode for better evening insulin control.</p>
        ) : (
          <motion.div className="mt-2 space-y-1 text-sm text-slate-200" initial={{ opacity: 0.7, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <p>Carbs: {dinnerCarbs.toFixed(1)} g</p>
            <p>Protein: {dinnerProtein.toFixed(1)} g</p>
            <p>Mode: {(dinnerMode ?? 'standard').replace('_', ' ')}</p>
            <p>Insulin impact: +{dinnerInsulinImpact.toFixed(1)}</p>
            {eveningInsulinSpikeRisk ? <p className="text-amber-300">Evening insulin spike risk</p> : <p className="text-emerald-300">Evening insulin trend stable</p>}
          </motion.div>
        )}
      </div>

      <AnimatePresence>
        {dayComplete && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.3 }}
            className="relative overflow-hidden rounded-2xl border border-emerald-300/35 bg-emerald-500/12 p-4"
          >
            <motion.div
              className="absolute inset-0 rounded-2xl border border-emerald-300/40"
              animate={{ scale: [0.95, 1.05, 1.15], opacity: [0.4, 0.15, 0] }}
              transition={{ duration: 2.2, repeat: Infinity, ease: 'easeOut' }}
            />
            <p className="relative text-sm font-semibold uppercase tracking-[0.16em] text-emerald-100">Day Complete.</p>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
