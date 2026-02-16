'use client';

import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Bolt, Dumbbell, Hand, HeartPulse, Moon, SquareMenu, TrendingUp, Zap } from 'lucide-react';

type DashboardProps = {
  insulinScore: number;
  compliance: number;
  protein: number;
  carbs: number;
  oil: number;
  chapatiCount: number;
  chapatiLimit: number;
  restingHr: number;
  sleepHours: number;
  proteinHit: boolean;
  carbUnderCeiling: boolean;
  strengthIndex: number;
  gripImprovementPct: number;
  monkeyBarProgress: {
    dead_hang_duration_seconds: number;
    pull_up_count: number;
    assisted_pull_up_reps: number;
    grip_endurance_seconds: number;
  };
  weeklyStrengthGraph: number[];
  metabolicExerciseMessage: string;
  challenge: {
    title: string;
    description: string;
    current_streak: number;
    longest_streak: number;
    completed: boolean;
    banner_title: string;
  };
  monthlyChallenge: {
    title: string;
    description: string;
    completed: boolean;
  };
  recipeSuggestion: string;
  carbLoadRemaining: number;
  recipes: Array<{
    id: number;
    name: string;
    ingredients: string;
    macros: {
      protein: number;
      carbs: number;
      fats: number;
    };
    cooking_time_minutes: number;
    oil_usage_tsp: number;
    insulin_score_impact: number;
    external_links: string[];
  }>;
};

function StatCard({ title, value, icon }: { title: string; value: string; icon: ReactNode }) {
  return (
    <div className="glass-card p-4">
      <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">{icon}{title}</div>
      <p className="text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function MacroBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const width = Math.min(100, (value / max) * 100);
  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between text-sm"><span>{label}</span><span>{value.toFixed(1)}</span></div>
      <div className="mt-2 h-2 rounded-full bg-slate-800"><div className="h-full rounded-full" style={{ width: `${width}%`, background: color }} /></div>
    </div>
  );
}


function ChallengeCard({
  challenge,
  monthlyChallenge,
}: {
  challenge: DashboardProps["challenge"];
  monthlyChallenge: DashboardProps["monthlyChallenge"];
}) {
  return (
    <section className="glass-card p-5">
      <p className="text-xs uppercase tracking-[0.22em] text-electric">{challenge.banner_title}</p>
      <p className="mt-2 text-lg font-semibold">{challenge.title}</p>
      <p className="mt-1 text-sm text-slate-300">{challenge.description}</p>
      <div className="mt-3 flex items-center justify-between text-sm">
        <span>Streak: {challenge.current_streak} days</span>
        <span className="text-slate-400">Best: {challenge.longest_streak} days</span>
      </div>
      <p className={`mt-2 text-sm ${challenge.completed ? 'text-emerald-300' : 'text-amber-300'}`}>
        {challenge.completed ? 'Completed today' : 'Pending today'}
      </p>
      <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Monthly mode</p>
        <p className="mt-1 text-sm font-medium">{monthlyChallenge.title}</p>
        <p className="text-xs text-slate-300">{monthlyChallenge.description}</p>
      </div>
    </section>
  );
}

function StrengthGraph({ values }: { values: number[] }) {
  const max = Math.max(1, ...values);
  return (
    <div className="glass-card p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Weekly Strength Graph</p>
      <div className="mt-3 flex h-24 items-end gap-2">
        {values.map((value, i) => (
          <div key={`${i}-${value}`} className="flex-1 rounded-t bg-electric/70" style={{ height: `${Math.max(8, (value / max) * 100)}%` }} />
        ))}
      </div>
    </div>
  );
}

export function Dashboard(props: DashboardProps) {
  const [tab, setTab] = useState<'metabolic' | 'exercise'>('metabolic');
  const insulinLoadText = useMemo(() => (props.insulinScore < 40 ? 'Excellent' : props.insulinScore < 65 ? 'Moderate' : 'Needs recovery'), [props.insulinScore]);

  return (
    <main className="mx-auto max-w-md space-y-5 px-4 pb-28 pt-6 text-white animate-riseIn">
      <section className="glass-card p-4">
        <div className="grid grid-cols-2 gap-2">
          <button className={`rounded-lg p-2 text-sm ${tab === 'metabolic' ? 'bg-electric/30' : 'bg-white/5'}`} onClick={() => setTab('metabolic')}>Metabolic</button>
          <button className={`rounded-lg p-2 text-sm ${tab === 'exercise' ? 'bg-electric/30' : 'bg-white/5'}`} onClick={() => setTab('exercise')}>Exercise</button>
        </div>
      </section>

      {tab === 'metabolic' ? (
        <>
          <section className="glass-card p-5">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Insulin Score</p>
            <p className="text-4xl font-semibold">{props.insulinScore}</p>
            <p className="text-sm text-emerald-300">{insulinLoadText}</p>
            <p className="mt-2 text-sm text-slate-300">Compliance {props.compliance}%</p>
          </section>

          <MacroBar label="Protein" value={props.protein} max={130} color="#34d399" />
          <MacroBar label="Carbs" value={props.carbs} max={120} color="#f59e0b" />
          <MacroBar label="Hidden Oil" value={props.oil} max={6} color="#ef4444" />

          <div className="glass-card p-4 text-sm">Chapati Counter: {props.chapatiCount}/{props.chapatiLimit}</div>

          <section className="glass-card p-5">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Smart meal suggestion</p>
            <p className="mt-2 text-sm text-emerald-300">{props.recipeSuggestion}</p>
            <p className="mt-1 text-xs text-slate-400">Carb load remaining: {props.carbLoadRemaining.toFixed(1)}g</p>
          </section>

          <section className="space-y-3">
            <h2 className="text-sm uppercase tracking-[0.22em] text-slate-400">Recipe database</h2>
            {props.recipes.slice(0, 5).map((recipe) => (
              <div key={recipe.id} className="glass-card p-4">
                <p className="text-sm font-semibold text-white">{recipe.name}</p>
                <p className="mt-1 text-xs text-slate-300">{recipe.ingredients}</p>
                <p className="mt-2 text-xs text-slate-400">
                  Macros P/C/F: {recipe.macros.protein}/{recipe.macros.carbs}/{recipe.macros.fats}g • {recipe.cooking_time_minutes}m • Oil {recipe.oil_usage_tsp} tsp
                </p>
                <p className="text-xs text-slate-400">Insulin score impact: {recipe.insulin_score_impact}</p>
                {recipe.external_links.length > 0 ? (
                  <div className="mt-2 flex flex-wrap gap-3 text-xs">
                    {recipe.external_links.map((link) => (
                      <a key={link} href={link} target="_blank" rel="noreferrer" className="text-electric underline">
                        Recipe ref
                      </a>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
          </section>
        </>
      ) : (
        <>
          <section className="glass-card p-5">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Strength Index</p>
            <p className="text-4xl font-semibold text-electric">{props.strengthIndex.toFixed(1)}</p>
            <p className="mt-2 text-sm text-slate-200">{props.metabolicExerciseMessage}</p>
            <p className="text-sm text-emerald-300">Grip strength improvement: {props.gripImprovementPct.toFixed(1)}%</p>
          </section>

          <section className="grid grid-cols-2 gap-3">
            <StatCard title="Dead Hang" value={`${props.monkeyBarProgress.dead_hang_duration_seconds}s`} icon={<Hand className="h-4 w-4" />} />
            <StatCard title="Pull-ups" value={`${props.monkeyBarProgress.pull_up_count}`} icon={<TrendingUp className="h-4 w-4" />} />
            <StatCard title="Assisted" value={`${props.monkeyBarProgress.assisted_pull_up_reps}`} icon={<Dumbbell className="h-4 w-4" />} />
            <StatCard title="Grip Endurance" value={`${props.monkeyBarProgress.grip_endurance_seconds}s`} icon={<Hand className="h-4 w-4" />} />
          </section>

          <StrengthGraph values={props.weeklyStrengthGraph} />
        </>
      )}

      <ChallengeCard challenge={props.challenge} monthlyChallenge={props.monthlyChallenge} />

      <section>
        <h2 className="mb-3 text-sm uppercase tracking-[0.22em] text-slate-400">Vitals</h2>
        <div className="grid grid-cols-2 gap-3">
          <StatCard title="Resting HR" value={`${props.restingHr} bpm`} icon={<Zap className="h-4 w-4" />} />
          <StatCard title="Sleep" value={`${props.sleepHours.toFixed(1)} h`} icon={<Moon className="h-4 w-4" />} />
          <StatCard title="Protein OK" value={props.proteinHit ? 'Yes' : 'No'} icon={<Bolt className="h-4 w-4" />} />
          <StatCard title="Carb In Range" value={props.carbUnderCeiling ? 'Yes' : 'No'} icon={<HeartPulse className="h-4 w-4" />} />
        </div>
      </section>

      <div className="fixed bottom-0 left-0 right-0 border-t border-white/10 bg-[#090D15]/75 px-4 py-3 backdrop-blur-xl">
        <div className="mx-auto max-w-md space-y-2">
          <div className="flex items-center gap-3 rounded-2xl border border-white/15 bg-white/5 px-4 py-3">
            <SquareMenu className="h-4 w-4 text-slate-400" />
            <span className="text-sm text-slate-400">Ask for workout + meal optimization…</span>
          </div>
          <a href="/settings/notifications" className="block text-center text-xs text-electric underline">
            Manage notification settings
          </a>
        </div>
      </div>
    </main>
  );
}
