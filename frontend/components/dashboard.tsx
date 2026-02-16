import type { ReactNode } from 'react';
import { Bolt, Coffee, Drumstick, HeartPulse, Moon, Scale, Sandwich, SquareMenu, Target, Zap } from 'lucide-react';

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
};

const quickAdds = ['Egg', 'Whey', 'Chapati', 'Dal', 'Paneer', 'Tofu', 'Chocolate', 'Coffee'];

function Ring({ score }: { score: number }) {
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score));
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative flex h-40 w-40 items-center justify-center">
      <svg className="h-40 w-40 -rotate-90" viewBox="0 0 160 160">
        <circle cx="80" cy="80" r={radius} stroke="#1B2333" strokeWidth="12" fill="none" />
        <circle
          cx="80"
          cy="80"
          r={radius}
          stroke="url(#scoreGradient)"
          strokeWidth="12"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700 ease-out"
        />
        <defs>
          <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#57E6B0" />
            <stop offset="100%" stopColor="#7C9BFF" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute text-center">
        <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Insulin Load</p>
        <p className="text-3xl font-semibold text-white">{score}</p>
      </div>
    </div>
  );
}

function MacroBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const width = Math.min(100, (value / max) * 100);
  return (
    <div className="space-y-2 rounded-2xl border border-borderSoft bg-card p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-300">{label}</span>
        <span className="font-medium text-white">{value.toFixed(1)}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-800">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${width}%`, background: color }} />
      </div>
    </div>
  );
}

function StatCard({ icon, title, value }: { icon: ReactNode; title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-borderSoft bg-card p-4 shadow-glow">
      <div className="mb-3 flex items-center gap-2 text-slate-300">
        {icon}
        <p className="text-xs uppercase tracking-wider">{title}</p>
      </div>
      <p className="text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

export function Dashboard(props: DashboardProps) {
  const vitals = [
    { title: 'Weight', value: '74.2 kg', icon: <Scale className="h-4 w-4" /> },
    { title: 'Waist', value: '86 cm', icon: <Target className="h-4 w-4" /> },
    { title: 'BP', value: '118 / 76', icon: <HeartPulse className="h-4 w-4" /> },
    { title: 'Resting HR', value: `${props.restingHr} bpm`, icon: <Zap className="h-4 w-4" /> },
    { title: 'Sleep', value: `${props.sleepHours.toFixed(1)} h`, icon: <Moon className="h-4 w-4" /> },
    { title: 'Energy', value: 'High', icon: <Bolt className="h-4 w-4" /> },
    { title: 'Hunger', value: 'Controlled', icon: <Sandwich className="h-4 w-4" /> },
  ];

  return (
    <main className="mx-auto max-w-md space-y-5 px-4 pb-28 pt-6 text-white animate-riseIn">
      <section className="rounded-3xl border border-borderSoft bg-card p-5 shadow-glow">
        <div className="flex items-center justify-between">
          <Ring score={props.insulinScore} />
          <div className="space-y-2 text-right">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Compliance</p>
            <p className="text-4xl font-semibold">{props.compliance}%</p>
            <p className="text-sm text-mint">On track</p>
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <MacroBar label="Protein" value={props.protein} max={120} color="#57E6B0" />
        <MacroBar label="Carbs" value={props.carbs} max={120} color="#7C9BFF" />
        <MacroBar label="Oil" value={props.oil} max={6} color="#F6C96A" />
        <div className="rounded-2xl border border-borderSoft bg-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-300">Chapati Counter</span>
            <span className="text-base font-semibold">{props.chapatiCount}/{props.chapatiLimit}</span>
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
          {quickAdds.map((item) => (
            <button
              key={item}
              className="flex min-h-14 items-center justify-center gap-2 rounded-2xl border border-borderSoft bg-card text-sm font-medium text-white transition duration-200 active:scale-[0.98] active:bg-slate-800"
            >
              {item === 'Coffee' ? <Coffee className="h-4 w-4" /> : <Drumstick className="h-4 w-4" />}
              + {item}
            </button>
          ))}
        </div>
      </section>

      <div className="fixed bottom-0 left-0 right-0 border-t border-borderSoft bg-[#090D15]/95 px-4 py-3 backdrop-blur-sm">
        <div className="mx-auto flex max-w-md items-center gap-3 rounded-2xl border border-borderSoft bg-card px-4 py-3">
          <SquareMenu className="h-4 w-4 text-slate-400" />
          <span className="text-sm text-slate-400">Ask about food…</span>
        </div>
      </div>
    </main>
  );
}
