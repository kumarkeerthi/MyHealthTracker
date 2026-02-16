import { ShieldCheck } from 'lucide-react';
import type { EmotionState, IdentityTier } from '@/components/visuals/identity-engine';

type Props = {
  stateLabel: string;
  identityScore: number;
  tier: IdentityTier;
  emotionState: EmotionState;
};

function EmotionRow({ title, score, items }: { title: string; score: number; items: Array<{ label: string; active: boolean }> }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3">
      <div className="flex items-center justify-between">
        <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">{title}</p>
        <p className="text-xs text-emerald-200">{score}%</p>
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item.label}
            className={`rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.08em] ${item.active ? 'border-emerald-300/40 bg-emerald-400/15 text-emerald-100' : 'border-slate-600/60 bg-slate-700/20 text-slate-400'}`}
          >
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export function IdentityHeader({ stateLabel, identityScore, tier, emotionState }: Props) {
  return (
    <section className="glass-card space-y-3 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Identity State</p>
          <p className="mt-1 text-lg font-semibold text-white">{stateLabel}</p>
        </div>
        <div className="text-right">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Identity Score</p>
          <p className="text-xl font-semibold text-emerald-300">{identityScore.toFixed(0)}</p>
          <p className="text-xs uppercase tracking-[0.12em] text-emerald-200">{tier}</p>
        </div>
      </div>

      <div className="rounded-xl border border-emerald-400/25 bg-emerald-500/10 p-3 text-sm text-emerald-100">
        <div className="flex items-center gap-2 font-medium">
          <ShieldCheck size={14} />
          You are building control.
        </div>
      </div>

      <div className="grid gap-2">
        <EmotionRow title="Pride" score={emotionState.prideScore} items={emotionState.pride} />
        <EmotionRow title="Control" score={emotionState.controlScore} items={emotionState.control} />
        <EmotionRow title="Strength" score={emotionState.strengthScore} items={emotionState.strength} />
        <EmotionRow title="Discipline" score={emotionState.disciplineScore} items={emotionState.discipline} />
      </div>
    </section>
  );
}
