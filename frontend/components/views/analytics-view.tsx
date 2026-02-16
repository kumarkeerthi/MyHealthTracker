import { motion } from 'framer-motion';
import type { AdvancedAnalytics, TrendSeries } from '@/lib/api';
import { CleanArteryIcon, HeartIcon, HeartPulseLine, ShieldIcon } from '@/components/visuals/body-assets';

function TrendCard({ series }: { series: TrendSeries }) {
  const width = 280;
  const height = 132;
  const pad = 14;
  const vals = series.points.map((p) => p.value);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const span = max - min || 1;
  const coords = series.points.map((p, i) => {
    const x = pad + (i / Math.max(series.points.length - 1, 1)) * (width - pad * 2);
    const y = height - pad - ((p.value - min) / span) * (height - pad * 2);
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  return (
    <div className="glass-card p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{series.label}</p>
      <svg viewBox={`0 0 ${width} ${height}`} className="mt-2 w-full">
        <defs>
          <linearGradient id={`grad-${series.key}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(16,185,129,0.45)" />
            <stop offset="100%" stopColor="rgba(16,185,129,0.03)" />
          </linearGradient>
        </defs>
        <path d={`${coords} L ${width - pad} ${height - pad} L ${pad} ${height - pad} Z`} fill={`url(#grad-${series.key})`} />
        <motion.path d={coords} fill="none" stroke="rgba(52,211,153,0.95)" strokeWidth="2.5" animate={series.improving ? { opacity: [0.65, 1, 0.65] } : { opacity: 0.75 }} transition={{ duration: 1.8, repeat: Infinity }} />
      </svg>
    </div>
  );
}

export function AnalyticsView({ analytics, momentumLabel }: { analytics: AdvancedAnalytics | null; momentumLabel: string }) {
  if (!analytics) {
    return <section className="glass-card p-4 text-sm text-slate-300">Analytics are warming up.</section>;
  }

  const series = [analytics.waist_trend, analytics.insulin_load_trend, analytics.walk_vs_insulin_correlation, analytics.strength_score_trend, analytics.sleep_trend];

  return (
    <section className="space-y-4">
      <motion.div className="glass-card border border-emerald-300/30 bg-emerald-400/10 p-4" animate={{ boxShadow: ['0 0 0 rgba(16,185,129,0)', '0 0 24px rgba(16,185,129,0.35)', '0 0 0 rgba(16,185,129,0)'] }} transition={{ duration: 2.4, repeat: Infinity }}>
        <p className="text-xs uppercase tracking-[0.2em] text-emerald-100">Metabolic Momentum Banner</p>
        <p className="mt-1 text-xl font-semibold text-emerald-200">{momentumLabel}</p>
      </motion.div>

      {series.map((item) => <TrendCard key={item.key} series={item} />)}

      <div className="glass-card p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Why This Matters</p>
        <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-slate-300">
          <div className="rounded-xl bg-white/5 p-3"><HeartIcon className="h-10 w-10" />Healthy heart resilience</div>
          <div className="rounded-xl bg-white/5 p-3"><CleanArteryIcon className="h-10 w-10" />Cleaner lipid flow pattern</div>
          <div className="rounded-xl bg-white/5 p-3"><HeartPulseLine className="h-10 w-16" />Stable insulin pulse</div>
          <div className="rounded-xl bg-white/5 p-3"><ShieldIcon className="h-10 w-10" />Brain clarity + protection</div>
        </div>
      </div>
    </section>
  );
}
