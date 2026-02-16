import type { ReactNode } from 'react';
import { Droplets, Moon, Target, Zap } from 'lucide-react';

type Props = {
  insulinScore: number;
  compliance: number;
  hydrationScore: number;
  waterMl: number;
  sleepHours: number;
  protein: number;
  carbs: number;
  oil: number;
};

function MetricCard({ label, value, icon }: { label: string; value: string; icon: ReactNode }) {
  return (
    <div className="glass-card p-4">
      <p className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-400">{icon}{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

export function DashboardView({ insulinScore, compliance, hydrationScore, waterMl, sleepHours, protein, carbs, oil }: Props) {
  return (
    <section className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="Insulin" value={insulinScore.toFixed(0)} icon={<Zap size={14} />} />
        <MetricCard label="Compliance" value={`${compliance}%`} icon={<Target size={14} />} />
        <MetricCard label="Hydration" value={`${hydrationScore.toFixed(0)}%`} icon={<Droplets size={14} />} />
        <MetricCard label="Sleep" value={`${sleepHours.toFixed(1)}h`} icon={<Moon size={14} />} />
      </div>
      <div className="glass-card p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Daily Macro Metrics</p>
        <div className="mt-3 space-y-2 text-sm text-slate-200">
          <div className="flex justify-between"><span>Protein</span><span>{protein.toFixed(1)} g</span></div>
          <div className="flex justify-between"><span>Carbs</span><span>{carbs.toFixed(1)} g</span></div>
          <div className="flex justify-between"><span>Hidden Oil</span><span>{oil.toFixed(1)} tsp</span></div>
          <div className="flex justify-between"><span>Water</span><span>{waterMl.toFixed(0)} ml</span></div>
        </div>
      </div>
    </section>
  );
}
