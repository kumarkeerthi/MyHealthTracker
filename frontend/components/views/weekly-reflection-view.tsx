type Props = {
  waistChangeCm: number;
  insulinAverage: number;
  strengthGain: number;
  habitCompliance: number;
  sleepConsistency: number;
  isSunday: boolean;
};

const timeline = [
  'Week 1: Stabilizing.',
  'Week 2: Energy improving.',
  'Week 3: Waist reducing.',
  'Week 4: Metabolic momentum.',
];

export function WeeklyReflectionView({ waistChangeCm, insulinAverage, strengthGain, habitCompliance, sleepConsistency, isSunday }: Props) {
  return (
    <section className="space-y-3">
      <div className="glass-card p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Progress Timeline</p>
        <div className="mt-3 flex snap-x gap-2 overflow-x-auto pb-1">
          {timeline.map((entry) => (
            <div key={entry} className="min-w-[170px] snap-start rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-200">
              {entry}
            </div>
          ))}
        </div>
      </div>

      {isSunday && (
        <div className="glass-card p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Weekly Reflection</p>
          <div className="mt-3 space-y-2 text-sm text-slate-200">
            <div className="flex justify-between"><span>Waist change</span><span>{waistChangeCm.toFixed(1)} cm</span></div>
            <div className="flex justify-between"><span>Insulin average</span><span>{insulinAverage.toFixed(1)}</span></div>
            <div className="flex justify-between"><span>Strength gain</span><span>{strengthGain.toFixed(1)}%</span></div>
            <div className="flex justify-between"><span>Habit compliance</span><span>{habitCompliance.toFixed(0)}%</span></div>
            <div className="flex justify-between"><span>Sleep consistency</span><span>{sleepConsistency.toFixed(0)}%</span></div>
          </div>
          <p className="mt-3 rounded-xl border border-emerald-300/30 bg-emerald-500/10 p-3 text-sm font-medium text-emerald-100">You are building control.</p>
        </div>
      )}
    </section>
  );
}
