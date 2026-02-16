'use client';

import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Bolt, Camera, Dumbbell, Hand, HeartPulse, Moon, SquareMenu, TrendingUp, Zap } from 'lucide-react';
import { analyzeFoodImage, confirmFoodImageLog, type AdvancedAnalytics, type AnalyzeFoodImageResponse, type ImageAnalyzedFood, type TrendSeries } from '@/lib/api';

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
  analytics: AdvancedAnalytics | null;
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



function trendTone(trend: TrendSeries['trend']) {
  if (trend === 'improvement') {
    return { stroke: '#34d399', fillA: 'rgba(16,185,129,0.35)', fillB: 'rgba(16,185,129,0.02)', glow: 'shadow-[0_0_22px_rgba(16,185,129,0.55)]' };
  }
  if (trend === 'regression') {
    return { stroke: '#ef4444', fillA: 'rgba(239,68,68,0.3)', fillB: 'rgba(239,68,68,0.02)', glow: '' };
  }
  return { stroke: '#f59e0b', fillA: 'rgba(245,158,11,0.3)', fillB: 'rgba(245,158,11,0.02)', glow: '' };
}

function TrendGraphCard({ series, bold = false }: { series: TrendSeries; bold?: boolean }) {
  const tone = trendTone(series.trend);
  const gradientId = `grad-${series.key}`;
  const width = 320;
  const height = bold ? 224 : 160;
  const padding = 20;
  const values = series.points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const coordinates = series.points.map((point, index) => {
    const x = padding + (index / Math.max(series.points.length - 1, 1)) * (width - padding * 2);
    const y = height - padding - ((point.value - min) / span) * (height - padding * 2);
    return { x, y };
  });
  const linePath = coordinates.map((point, index) => `${index === 0 ? 'M' : 'L'}${point.x},${point.y}`).join(' ');
  const areaPath = `${linePath} L${coordinates[coordinates.length - 1]?.x ?? width - padding},${height - padding} L${coordinates[0]?.x ?? padding},${height - padding} Z`;

  return (
    <section className={`glass-card p-4 ${bold ? 'border-emerald-300/40 ring-1 ring-emerald-300/25' : ''} ${series.improving ? tone.glow : ''}`}>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-300">{series.label}</p>
        <span className={`rounded-full px-2 py-1 text-[10px] uppercase tracking-[0.18em] ${series.trend === 'improvement' ? 'bg-emerald-500/20 text-emerald-200' : series.trend === 'regression' ? 'bg-red-500/20 text-red-200' : 'bg-amber-500/20 text-amber-200'}`}>
          {series.trend}
        </span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={tone.fillA} />
            <stop offset="100%" stopColor={tone.fillB} />
          </linearGradient>
        </defs>
        {Array.from({ length: 4 }).map((_, idx) => (
          <line key={idx} x1={padding} x2={width - padding} y1={padding + ((height - padding * 2) * idx) / 3} y2={padding + ((height - padding * 2) * idx) / 3} stroke="rgba(148,163,184,0.2)" strokeDasharray="2 3" />
        ))}
        <path d={areaPath} fill={`url(#${gradientId})`} className="animate-pulse" />
        <path d={linePath} fill="none" stroke={tone.stroke} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ filter: series.improving ? 'drop-shadow(0 0 8px rgba(16,185,129,0.7))' : undefined }} />
      </svg>
      <div className="mt-2 flex justify-between text-[10px] text-slate-400">
        <span>{series.points[0]?.date}</span>
        <span>{series.points[series.points.length - 1]?.date}</span>
      </div>
    </section>
  );
}

function MetabolicMomentumCard({ analytics }: { analytics: AdvancedAnalytics }) {
  const score = analytics.metabolic_momentum.score;
  const quality = score >= 75 ? 'On fire' : score >= 55 ? 'Building' : 'Recovery mode';

  return (
    <section className="glass-card p-5 shadow-[0_0_26px_rgba(16,185,129,0.3)]">
      <p className="text-xs uppercase tracking-[0.22em] text-emerald-200">Metabolic Momentum Score</p>
      <div className="mt-2 flex items-end justify-between">
        <p className="text-4xl font-semibold text-emerald-300">{score.toFixed(1)}</p>
        <p className="text-sm text-slate-300">{quality}</p>
      </div>
      <div className="mt-4 space-y-2 text-xs text-slate-300">
        <div className="flex justify-between"><span>Insulin load</span><span>{analytics.metabolic_momentum.insulin_load_component.toFixed(1)}</span></div>
        <div className="flex justify-between"><span>Waist change</span><span>{analytics.metabolic_momentum.waist_component.toFixed(1)}</span></div>
        <div className="flex justify-between"><span>Strength increase</span><span>{analytics.metabolic_momentum.strength_component.toFixed(1)}</span></div>
        <div className="flex justify-between"><span>Sleep quality</span><span>{analytics.metabolic_momentum.sleep_component.toFixed(1)}</span></div>
      </div>
    </section>
  );
}

function AdvancedAnalyticsSection({ analytics }: { analytics: AdvancedAnalytics | null }) {
  if (!analytics) return null;

  const graphSeries: Array<{ series: TrendSeries; bold?: boolean }> = [
    { series: analytics.insulin_load_trend },
    { series: analytics.waist_trend, bold: true },
    { series: analytics.weight_trend },
    { series: analytics.protein_intake_consistency },
    { series: analytics.carb_intake_pattern },
    { series: analytics.oil_usage_pattern },
    { series: analytics.strength_score_trend },
    { series: analytics.grip_strength_trend },
    { series: analytics.sleep_trend },
    { series: analytics.resting_heart_rate_trend },
    { series: analytics.habit_compliance_trend },
    { series: analytics.clean_streak_trend },
  ];

  return (
    <section className="space-y-4">
      <h2 className="text-sm uppercase tracking-[0.22em] text-slate-400">Advanced Analytics Engine</h2>
      <MetabolicMomentumCard analytics={analytics} />
      {graphSeries.map((item) => <TrendGraphCard key={item.series.key} series={item.series} bold={item.bold} />)}
    </section>
  );
}

export function Dashboard(props: DashboardProps) {
  const [tab, setTab] = useState<'metabolic' | 'exercise'>('metabolic');
  const [scanPreviewUrl, setScanPreviewUrl] = useState<string | null>(null);
  const [scanFile, setScanFile] = useState<File | null>(null);
  const [scanMealContext, setScanMealContext] = useState('lunch');
  const [scanBusy, setScanBusy] = useState(false);
  const [scanResult, setScanResult] = useState<AnalyzeFoodImageResponse | null>(null);
  const [editableFoods, setEditableFoods] = useState<ImageAnalyzedFood[]>([]);
  const [manualEdited, setManualEdited] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const insulinLoadText = useMemo(() => (props.insulinScore < 40 ? 'Excellent' : props.insulinScore < 65 ? 'Moderate' : 'Needs recovery'), [props.insulinScore]);

  const recomputedMetrics = useMemo(() => {
    if (!editableFoods.length) {
      return null;
    }
    const totals = editableFoods.reduce((acc, item) => {
      acc.protein += item.estimated_protein;
      acc.carbs += item.estimated_carbs;
      acc.fats += item.estimated_fat;
      acc.oil += item.estimated_hidden_oil;
      return acc;
    }, { protein: 0, carbs: 0, fats: 0, oil: 0 });
    const insulinImpact = Math.max(0, Math.min(100, totals.carbs + totals.oil * 0.5 - totals.protein * 0.3));
    return { ...totals, insulinImpact };
  }, [editableFoods]);

  async function runScan() {
    if (!scanFile) return;
    setScanBusy(true);
    setScanMessage(null);
    try {
      const response = await analyzeFoodImage(scanFile, scanMealContext);
      setScanResult(response);
      setEditableFoods(response.foods);
      setManualEdited(false);
    } catch {
      setScanMessage('Scan failed. Please retry with a clearer plate image.');
    } finally {
      setScanBusy(false);
    }
  }

  async function confirmLog() {
    if (!scanResult) return;
    setScanBusy(true);
    setScanMessage(null);
    try {
      await confirmFoodImageLog({
        foods: editableFoods,
        image_url: scanResult.image_url,
        vision_confidence: scanResult.overall_confidence,
        portion_scale_factor: scanResult.portion_scale_factor,
        manual_adjustment_flag: manualEdited,
        meal_context: scanMealContext,
      });
      setScanMessage('Meal logged successfully.');
    } catch {
      setScanMessage('Unable to log meal.');
    } finally {
      setScanBusy(false);
    }
  }

  function editPortion(index: number, grams: number) {
    setManualEdited(true);
    setEditableFoods((prev) => prev.map((item, i) => {
      if (i !== index) return item;
      const ratio = grams <= 0 ? 1 : grams / Math.max(item.estimated_quantity_grams, 1);
      return {
        ...item,
        estimated_quantity_grams: grams,
        estimated_protein: Number((item.estimated_protein * ratio).toFixed(2)),
        estimated_carbs: Number((item.estimated_carbs * ratio).toFixed(2)),
        estimated_fat: Number((item.estimated_fat * ratio).toFixed(2)),
        estimated_hidden_oil: Number((item.estimated_hidden_oil * ratio).toFixed(2)),
      };
    }));
  }

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


      <section className="glass-card p-5 space-y-3">
        <h2 className="text-sm uppercase tracking-[0.22em] text-slate-400">Quick Actions</h2>
        <p className="rounded-lg border border-electric/30 bg-electric/10 px-3 py-2 text-xs text-electric">Place reference card next to plate for portion accuracy.</p>
        <div className="flex items-center gap-2">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-electric/30 px-3 py-2 text-sm">
            <Camera className="h-4 w-4" /> Scan Food
            <input
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                setScanFile(file);
                setScanPreviewUrl(URL.createObjectURL(file));
                setScanResult(null);
              }}
            />
          </label>
          <select value={scanMealContext} onChange={(event) => setScanMealContext(event.target.value)} className="rounded-lg bg-white/10 px-2 py-2 text-xs">
            <option value="breakfast">Breakfast</option>
            <option value="lunch">Lunch</option>
            <option value="dinner">Dinner</option>
          </select>
          <button disabled={!scanFile || scanBusy} onClick={runScan} className="rounded-lg border border-white/20 px-3 py-2 text-xs disabled:opacity-40">
            {scanBusy ? 'Analyzing…' : 'Analyze'}
          </button>
        </div>

        {scanPreviewUrl ? <img src={scanPreviewUrl} alt="Food preview" className="h-40 w-full rounded-xl object-cover" /> : null}

        {scanResult ? (
          <div className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-3">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Food Detected</p>
            {editableFoods.map((food, index) => (
              <div key={`${food.name}-${index}`} className="space-y-1 rounded-lg border border-white/10 p-2">
                <p className="text-sm font-medium">{food.name}</p>
                <label className="text-xs text-slate-300">
                  Portion (g)
                  <input
                    type="number"
                    value={food.estimated_quantity_grams}
                    min={1}
                    className="ml-2 w-20 rounded bg-white/10 px-2 py-1"
                    onChange={(event) => editPortion(index, Number(event.target.value))}
                  />
                </label>
              </div>
            ))}

            <div className="text-sm text-slate-200">
              <p>Protein: {(recomputedMetrics?.protein ?? scanResult.estimated_macros.protein).toFixed(1)} g</p>
              <p>Carbs: {(recomputedMetrics?.carbs ?? scanResult.estimated_macros.carbs).toFixed(1)} g</p>
              <p>Fat: {(recomputedMetrics?.fats ?? scanResult.estimated_macros.fats).toFixed(1)} g</p>
              <p>Oil Estimate: {(recomputedMetrics?.oil ?? scanResult.estimated_oil_tsp).toFixed(1)} tsp</p>
              <p>Insulin Impact: +{(recomputedMetrics?.insulinImpact ?? scanResult.insulin_load_impact).toFixed(1)} score increase</p>
              <p>Approval: {scanResult.approval}</p>
              <p className="text-xs text-amber-300">{scanResult.validation.message}</p>
              <p className="text-xs text-emerald-300">{scanResult.coaching.primary_message}</p>
            </div>

            <div className="flex gap-2">
              <button onClick={confirmLog} disabled={scanBusy} className="rounded-lg bg-emerald-600 px-3 py-2 text-xs">Confirm & Log</button>
              <button onClick={() => setManualEdited(true)} className="rounded-lg border border-white/20 px-3 py-2 text-xs">Edit Portion</button>
              <button onClick={() => { setScanResult(null); setEditableFoods([]); setScanFile(null); setScanPreviewUrl(null); }} className="rounded-lg border border-white/20 px-3 py-2 text-xs">Discard</button>
            </div>
          </div>
        ) : null}

        {scanMessage ? <p className="text-xs text-slate-300">{scanMessage}</p> : null}
      </section>

      <AdvancedAnalyticsSection analytics={props.analytics} />

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
