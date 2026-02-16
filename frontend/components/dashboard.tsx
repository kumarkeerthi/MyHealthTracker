'use client';

import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import {
  Bolt,
  BrainCircuit,
  Coffee,
  Drumstick,
  Flame,
  Hand,
  HeartPulse,
  Moon,
  Scale,
  Sandwich,
  SquareMenu,
  Target,
  TrendingUp,
  Zap,
} from 'lucide-react';

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
};

type TrendSeries = {
  label: string;
  color: string;
  values: number[];
  postfix: string;
};

const quickAdds = [
  { label: 'Egg', proteinDelta: 12, carbDelta: 1, icon: Drumstick },
  { label: 'Whey', proteinDelta: 24, carbDelta: 3, icon: Zap },
  { label: 'Chapati', proteinDelta: 3, carbDelta: 21, icon: Flame },
  { label: 'Dal', proteinDelta: 8, carbDelta: 14, icon: Bolt },
  { label: 'Paneer', proteinDelta: 16, carbDelta: 4, icon: Drumstick },
  { label: 'Tofu', proteinDelta: 13, carbDelta: 5, icon: BrainCircuit },
  { label: 'Chocolate', proteinDelta: 2, carbDelta: 15, icon: Flame },
  { label: 'Coffee', proteinDelta: 1, carbDelta: 0, icon: Coffee },
];

function StatusBanner({ insulinScore, proteinHit, carbUnderCeiling }: { insulinScore: number; proteinHit: boolean; carbUnderCeiling: boolean }) {
  const status =
    insulinScore < 40
      ? 'Stable Burn Mode'
      : insulinScore < 65
        ? 'Insulin Controlled'
        : 'High Carb Day – Recover Tomorrow';

  const tone = insulinScore < 40 ? 'text-emerald-200' : insulinScore < 65 ? 'text-amber-200' : 'text-red-200';

  const messages = [proteinHit ? 'HDL Support Achieved' : 'Protein top-up keeps recovery sharp'];
  messages.push(carbUnderCeiling ? 'Triglyceride Drop Mode Active' : 'Higher insulin load today. Adjust tomorrow.');

  return (
    <section className="glass-card relative overflow-hidden p-5">
      <div className="absolute -right-20 -top-20 h-44 w-44 rounded-full bg-electric/25 blur-3xl" />
      <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Metabolic Status Banner</p>
      <h1 className={`mt-3 text-2xl font-semibold ${tone}`}>{status}</h1>
      <div className="mt-4 space-y-2">
        {messages.map((message) => (
          <p key={message} className="text-sm text-slate-200">
            {message}
          </p>
        ))}
      </div>
    </section>
  );
}

function InsulinRing({ score }: { score: number }) {
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score));
  const offset = circumference - (progress / 100) * circumference;
  const lowRisk = score < 40;

  return (
    <div className="relative flex h-40 w-40 items-center justify-center">
      <svg className="h-40 w-40 -rotate-90" viewBox="0 0 160 160">
        <circle cx="80" cy="80" r={radius} stroke="#202B3E" strokeWidth="14" fill="none" />
        <circle
          cx="80"
          cy="80"
          r={radius}
          stroke="url(#insulinGradient)"
          strokeWidth="14"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
        <defs>
          <linearGradient id="insulinGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#34d399" />
            <stop offset="60%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#a78bfa" />
          </linearGradient>
        </defs>
      </svg>
      <div className={`absolute rounded-full px-5 py-4 text-center ${lowRisk ? 'animate-pulseGlow' : ''}`}>
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Insulin Score</p>
        <p className="text-3xl font-semibold text-white">{score}</p>
      </div>
    </div>
  );
}

function MacroBar({ label, value, max, color, microText }: { label: string; value: number; max: number; color: string; microText: string }) {
  const width = Math.min(100, (value / max) * 100);
  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-300">{label}</span>
        <span className="font-medium text-white">{value.toFixed(1)}</span>
      </div>
      <div className="mt-3 h-2 rounded-full bg-slate-800">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${width}%`, background: color, boxShadow: `0 0 16px ${color}` }}
        />
      </div>
      <p className="mt-2 text-xs text-slate-400">{microText}</p>
    </div>
  );
}

function StreakCard({ title, value, icon }: { title: string; value: string; icon: ReactNode }) {
  return (
    <div className="glass-card p-4">
      <div className="mb-2 flex items-center gap-2 text-slate-300">
        {icon}
        <p className="text-xs uppercase tracking-[0.2em]">{title}</p>
      </div>
      <p className="text-base font-semibold text-purple-soft">{value}</p>
    </div>
  );
}

function TrendLine({ series }: { series: TrendSeries }) {
  const points = useMemo(() => {
    const step = 220 / (series.values.length - 1);
    const min = Math.min(...series.values);
    const max = Math.max(...series.values);
    return series.values
      .map((value, index) => {
        const normalized = max === min ? 0.5 : (value - min) / (max - min);
        const x = 10 + index * step;
        const y = 68 - normalized * 54;
        return `${x},${y}`;
      })
      .join(' ');
  }, [series.values]);

  const latest = series.values[series.values.length - 1];

  return (
    <div className="glass-card p-4">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{series.label}</p>
        <p className="text-sm font-semibold text-white">
          {latest}
          {series.postfix}
        </p>
      </div>
      <svg viewBox="0 0 240 80" className="h-20 w-full">
        <polyline fill="none" stroke="#1f2937" strokeWidth="2" points="10,60 230,60" />
        <polyline fill="none" stroke={series.color} strokeWidth="3" strokeLinecap="round" points={points} />
      </svg>
    </div>
  );
}

function StatCard({ icon, title, value }: { icon: ReactNode; title: string; value: string }) {
  return (
    <div className="glass-card p-4">
      <div className="mb-2 flex items-center gap-2 text-slate-300">
        {icon}
        <p className="text-xs uppercase tracking-[0.18em]">{title}</p>
      </div>
      <p className="text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

export function Dashboard(props: DashboardProps) {
  const [proteinDisplay, setProteinDisplay] = useState(props.protein);
  const [carbDisplay, setCarbDisplay] = useState(props.carbs);
  const [dopamineMessage, setDopamineMessage] = useState('Log a meal to trigger momentum feedback.');

  const insulinLoadText = props.insulinScore < 40 ? 'Low insulin load' : props.insulinScore < 65 ? 'Moderate insulin load' : 'High insulin load';
  const weeklyTrends: TrendSeries[] = [
    { label: 'Waist Trend', color: '#34d399', values: [88.2, 87.8, 87.1, 86.8, 86.4, 86.2, 86], postfix: ' cm' },
    { label: 'Insulin Score Trend', color: '#3b82f6', values: [56, 52, 49, 46, 44, 41, props.insulinScore], postfix: '' },
    { label: 'Strength Trend', color: '#a78bfa', values: [62, 64, 65, 66, 68, 69, 71], postfix: ' pts' },
    { label: 'Sleep Trend', color: '#f59e0b', values: [6.2, 6.5, 6.7, 6.6, 6.9, 7, props.sleepHours], postfix: ' h' },
  ];

  const momentumScore = Math.round((props.compliance * 0.45) + ((100 - props.insulinScore) * 0.35) + ((props.sleepHours / 8) * 100 * 0.2));

  const vitals = [
    { title: 'Weight', value: '74.2 kg', icon: <Scale className="h-4 w-4" /> },
    { title: 'Waist', value: '86 cm', icon: <Target className="h-4 w-4" /> },
    { title: 'BP', value: '118 / 76', icon: <HeartPulse className="h-4 w-4" /> },
    { title: 'Resting HR', value: `${props.restingHr} bpm`, icon: <Zap className="h-4 w-4" /> },
    { title: 'Sleep', value: `${props.sleepHours.toFixed(1)} h`, icon: <Moon className="h-4 w-4" /> },
    { title: 'Energy', value: 'Focused', icon: <Bolt className="h-4 w-4" /> },
    { title: 'Hunger', value: 'Controlled', icon: <Sandwich className="h-4 w-4" /> },
  ];

  return (
    <main className="mx-auto max-w-md space-y-5 px-4 pb-28 pt-6 text-white animate-riseIn">
      <StatusBanner insulinScore={props.insulinScore} proteinHit={props.proteinHit} carbUnderCeiling={props.carbUnderCeiling} />

      <section className="glass-card p-5">
        <div className="flex items-center justify-between">
          <InsulinRing score={props.insulinScore} />
          <div className="space-y-2 text-right">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Daily Compliance</p>
            <p className="text-4xl font-semibold">{props.compliance}%</p>
            <p className="text-sm text-emerald-300">{insulinLoadText}</p>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-3">
        <StreakCard title="Clean Carb Streak" value="4 Days" icon={<Flame className="h-4 w-4" />} />
        <StreakCard title="Protein Target Streak" value="6 Days" icon={<TrendingUp className="h-4 w-4" />} />
        <StreakCard title="Monkey Bar Strength Streak" value="Grip Strength: Improving" icon={<Hand className="h-4 w-4" />} />
      </section>

      <section className="space-y-3">
        <MacroBar label="Protein" value={proteinDisplay} max={130} color="#34d399" microText={`Protein +${Math.max(0, Math.round(proteinDisplay - props.protein))}g`} />
        <MacroBar
          label="Carbs"
          value={carbDisplay}
          max={120}
          color="#f59e0b"
          microText={`Carb Budget Remaining: ${Math.max(0, Math.round(120 - carbDisplay))}g`}
        />
        <MacroBar label="Hidden Oil" value={props.oil} max={6} color="#ef4444" microText="Keep this low for better insulin control." />
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-300">Chapati Counter</span>
            <span className="text-base font-semibold">
              {props.chapatiCount}/{props.chapatiLimit}
            </span>
          </div>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm uppercase tracking-[0.22em] text-slate-400">Daily Flow Feedback</h2>
        <div className="glass-card p-4">
          <p className="text-sm text-electric transition-all duration-500">{dopamineMessage}</p>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm uppercase tracking-[0.22em] text-slate-400">Weekly Screen</h2>
        <div className="space-y-3">
          {weeklyTrends.map((series) => (
            <TrendLine key={series.label} series={series} />
          ))}
          <div className="glass-card flex items-center justify-between p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Metabolic Momentum Score</p>
            <p className="text-2xl font-semibold text-electric">{momentumScore}</p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm uppercase tracking-[0.22em] text-slate-400">Vitals</h2>
        <div className="grid grid-cols-2 gap-3">
          {vitals.map((vital) => (
            <StatCard key={vital.title} icon={vital.icon} title={vital.title} value={vital.value} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm uppercase tracking-[0.22em] text-slate-400">Quick Add</h2>
        <div className="grid grid-cols-2 gap-3">
          {quickAdds.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                onClick={() => {
                  setProteinDisplay((prev) => Number((prev + item.proteinDelta).toFixed(1)));
                  setCarbDisplay((prev) => Number((prev + item.carbDelta).toFixed(1)));
                  setDopamineMessage(`Protein +${item.proteinDelta}g · Carb Budget Remaining: ${Math.max(0, Math.round(120 - (carbDisplay + item.carbDelta)))}g`);
                }}
                className="glass-card flex min-h-14 items-center justify-center gap-2 text-sm font-medium text-white transition duration-200 active:scale-[0.98]"
              >
                <Icon className="h-4 w-4" />+ {item.label}
              </button>
            );
          })}
        </div>
      </section>

      <div className="fixed bottom-0 left-0 right-0 border-t border-white/10 bg-[#090D15]/75 px-4 py-3 backdrop-blur-xl">
        <div className="mx-auto flex max-w-md items-center gap-3 rounded-2xl border border-white/15 bg-white/5 px-4 py-3">
          <SquareMenu className="h-4 w-4 text-slate-400" />
          <span className="text-sm text-slate-400">Ask for meal optimization…</span>
        </div>
      </div>
    </main>
  );
}
