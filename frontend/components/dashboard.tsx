'use client';

import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { BarChart3, Home, Trophy, User, Dumbbell, Droplets } from 'lucide-react';
import type { AdvancedAnalytics, HabitIntelligence, MetabolicPhasePerformance } from '@/lib/api';
import { PwaClient } from '@/components/pwa-client';
import { DashboardView } from '@/components/views/dashboard-view';
import { IdentityHeader } from '@/components/views/identity-header';
import { BodyProgressView } from '@/components/views/body-progress-view';
import { StrengthView } from '@/components/views/strength-view';
import { AnalyticsView } from '@/components/views/analytics-view';
import { ProfileView } from '@/components/views/profile-view';
import { WeeklyReflectionView } from '@/components/views/weekly-reflection-view';
import { ChallengesView } from '@/components/views/challenges-view';
import { computeBodyVisualState, computeStatusBadges, computeStrengthVisualState, metabolicMomentumBanner, type VisualMode } from '@/components/visuals/visual-logic';
import { computeEmotionState, computeIdentityScore, computeIdentityVisualState, resolveIdentityState } from '@/components/visuals/identity-engine';
import { tabTransition } from '@/components/visuals/animation-config';

type DashboardProps = {
  insulinScore: number;
  compliance: number;
  protein: number;
  carbs: number;
  oil: number;
  sugar: number;
  fiber: number;
  fruitServings: number;
  fruitBudget: number;
  nutServings: number;
  nutBudget: number;
  remainingCarbBudget: number;
  fruitNutWarnings: string[];
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
  habitIntelligence: HabitIntelligence | null;
  metabolicPerformance: MetabolicPhasePerformance | null;
  waterMl: number;
  hydrationScore: number;
  hydrationTargetMinMl: number;
  hydrationTargetAchieved: boolean;
  streakDays: number;
  strengthStreakDays: number;
  fastingWindowIntact: boolean;
  waistChangeCm: number;
  noCarbDinnerStreak: number;
};

type TabKey = 'home' | 'body' | 'strength' | 'analytics' | 'profile';

export function Dashboard(props: DashboardProps) {
  const [tab, setTab] = useState<TabKey>('home');
  const [mode, setMode] = useState<VisualMode>('performance');
  const isSunday = new Date().getDay() === 0;

  const emotionState = useMemo(
    () => computeEmotionState({
      waistReductionCm: Math.max(0, props.waistChangeCm),
      strengthIncrease: props.strengthIndex > 40,
      cleanStreakDays: props.streakDays,
      hdlSupportDays: Math.min(7, Math.round(props.compliance / 14)),
      insulinLoad: props.insulinScore,
      carbCeilingMaintained: props.carbUnderCeiling,
      hydrationTargetAchieved: props.hydrationTargetAchieved,
      fastingWindowIntact: props.fastingWindowIntact,
      monkeyBarProgress: props.monkeyBarProgress.grip_endurance_seconds > 0 || props.monkeyBarProgress.pull_up_count > 0,
      pushupImprovement: props.strengthIndex > 30,
      strengthIndexRising: props.gripImprovementPct > 0,
      consistencyStreak: props.streakDays,
      noCarbDinnerStreak: props.noCarbDinnerStreak,
      proteinCompliance7d: props.streakDays >= 7 && props.proteinHit,
    }),
    [props.carbUnderCeiling, props.compliance, props.fastingWindowIntact, props.gripImprovementPct, props.hydrationTargetAchieved, props.insulinScore, props.monkeyBarProgress.grip_endurance_seconds, props.monkeyBarProgress.pull_up_count, props.noCarbDinnerStreak, props.proteinHit, props.streakDays, props.strengthIndex, props.waistChangeCm],
  );

  const identityState = useMemo(() => resolveIdentityState(emotionState), [emotionState]);

  const identityScore = useMemo(
    () => computeIdentityScore({
      strengthScore: emotionState.strengthScore,
      insulinControlScore: emotionState.controlScore,
      habitConsistencyScore: emotionState.disciplineScore,
      waistImprovementScore: emotionState.pride[0]?.active ? 100 : 40,
    }),
    [emotionState],
  );

  const identityVisualState = useMemo(
    () => computeIdentityVisualState({
      mode: identityState.mode,
      insulinScore: props.insulinScore,
      strengthScore: emotionState.strengthScore,
    }),
    [emotionState.strengthScore, identityState.mode, props.insulinScore],
  );

  const bodyState = useMemo(
    () => ({
      ...computeBodyVisualState({
        insulinScore: props.insulinScore,
        hydrationTargetAchieved: props.hydrationTargetAchieved,
        proteinHit: props.proteinHit,
        carbUnderCeiling: props.carbUnderCeiling,
        baselineWaist: 102,
        currentWaist: 102 - Math.min(12, props.challenge.current_streak * 0.5),
      }),
      postureLift: identityVisualState.postureLift,
      abdomenGlowOpacity: identityVisualState.abdomenGlowOpacity,
      muscleDefinition: identityVisualState.muscleDefinition,
    }),
    [props.carbUnderCeiling, props.challenge.current_streak, props.hydrationTargetAchieved, props.insulinScore, props.proteinHit, identityVisualState],
  );

  const strengthState = useMemo(
    () => computeStrengthVisualState({
      pushupsLogged: props.strengthIndex > 20,
      pullupsLogged: props.monkeyBarProgress.pull_up_count > 0,
      monkeyBarTracked: props.monkeyBarProgress.grip_endurance_seconds > 0,
      strengthIndex: props.strengthIndex,
      gripEnduranceSeconds: props.monkeyBarProgress.grip_endurance_seconds,
      pullUps: props.monkeyBarProgress.pull_up_count,
    }),
    [props.monkeyBarProgress.grip_endurance_seconds, props.monkeyBarProgress.pull_up_count, props.strengthIndex],
  );

  const badges = useMemo(
    () => computeStatusBadges({
      insulinScore: props.insulinScore,
      strengthStreakDays: props.strengthStreakDays,
      hydrationTargetAchieved: props.hydrationTargetAchieved,
      carbUnderCeiling: props.carbUnderCeiling,
      streakDays: props.streakDays,
    }),
    [props.carbUnderCeiling, props.hydrationTargetAchieved, props.insulinScore, props.streakDays, props.strengthStreakDays],
  );

  const momentumLabel = useMemo(
    () => metabolicMomentumBanner(props.insulinScore, props.carbUnderCeiling, props.strengthIndex),
    [props.carbUnderCeiling, props.insulinScore, props.strengthIndex],
  );

  const tabButtons: Array<{ key: TabKey; label: string; icon: ReactNode }> = [
    { key: 'home', label: 'Home', icon: <Home size={16} /> },
    { key: 'body', label: 'Body', icon: <User size={16} /> },
    { key: 'strength', label: 'Strength', icon: <Dumbbell size={16} /> },
    { key: 'analytics', label: 'Analytics', icon: <BarChart3 size={16} /> },
    { key: 'profile', label: 'Profile', icon: <Trophy size={16} /> },
  ];

  return (
    <main className="mx-auto max-w-md space-y-4 px-4 pb-28 pt-6 text-white">
      <PwaClient />

      <IdentityHeader
        stateLabel={identityState.label}
        identityScore={identityScore.score}
        tier={identityScore.tier}
        emotionState={emotionState}
      />

      <section className="glass-card p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Performance Mode</p>
          <button onClick={() => setMode((prev) => (prev === 'clinical' ? 'performance' : 'clinical'))} className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-xs">
            {mode === 'clinical' ? 'Clinical View' : 'Performance View'}
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {badges.map((badge) => <span key={badge} className="rounded-full border border-emerald-300/35 bg-emerald-400/10 px-3 py-1 text-[11px] uppercase tracking-[0.15em] text-emerald-200">{badge}</span>)}
          {!badges.length && <span className="text-xs text-slate-400">No active status badges.</span>}
        </div>
      </section>

      <AnimatePresence mode="wait">
        <motion.div key={tab + mode} {...tabTransition}>
          {tab === 'home' && (
            <div className="space-y-4">
              <DashboardView insulinScore={props.insulinScore} compliance={props.compliance} hydrationScore={props.hydrationScore} waterMl={props.waterMl} sleepHours={props.sleepHours} protein={props.protein} carbs={props.carbs} oil={props.oil} proteinHit={props.proteinHit} carbUnderCeiling={props.carbUnderCeiling} hydrationTargetAchieved={props.hydrationTargetAchieved} strengthLogged={props.strengthIndex > 0} />
              <ChallengesView challengeTitle={props.challenge.title} challengeDesc={props.challenge.description} streak={props.challenge.current_streak} />
            </div>
          )}
          {tab === 'body' && <BodyProgressView bodyState={bodyState} />}
          {tab === 'strength' && <StrengthView bodyState={bodyState} strengthState={strengthState} />}
          {tab === 'analytics' && (
            <div className="space-y-4">
              <AnalyticsView analytics={props.analytics} momentumLabel={momentumLabel} />
              <WeeklyReflectionView
                waistChangeCm={props.waistChangeCm}
                insulinAverage={props.insulinScore}
                strengthGain={Math.max(0, props.gripImprovementPct)}
                habitCompliance={props.compliance}
                sleepConsistency={Math.min(100, (props.sleepHours / 8) * 100)}
                isSunday={isSunday}
              />
            </div>
          )}
          {tab === 'profile' && (
            <div className="space-y-4">
              <ProfileView chapatiCount={props.chapatiCount} chapatiLimit={props.chapatiLimit} recipeSuggestion={props.recipeSuggestion} />
              {mode === 'clinical' && (
                <section className="glass-card p-4 text-xs text-slate-300">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Clinical Metrics</p>
                  <div className="mt-2 space-y-1">
                    <p>Resting HR: {props.restingHr}</p>
                    <p>Fiber: {props.fiber.toFixed(1)} g</p>
                    <p>Sugar: {props.sugar.toFixed(1)} g</p>
                    <p>Fruit/Nuts: {props.fruitServings.toFixed(1)}/{props.fruitBudget.toFixed(1)} · {props.nutServings.toFixed(1)}/{props.nutBudget.toFixed(1)}</p>
                    <p>Carb budget remaining: {props.remainingCarbBudget.toFixed(1)} g</p>
                    <p className="text-slate-400">{props.metabolicExerciseMessage}</p>
                  </div>
                </section>
              )}
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      <nav className="fixed inset-x-0 bottom-0 mx-auto w-full max-w-md border-t border-white/10 bg-slate-950/95 px-3 pb-5 pt-2 backdrop-blur-xl">
        <div className="grid grid-cols-5 gap-1">
          {tabButtons.map((item) => (
            <button key={item.key} onClick={() => setTab(item.key)} className={`flex flex-col items-center rounded-xl px-1 py-2 text-[11px] ${tab === item.key ? 'bg-electric/30 text-white' : 'text-slate-400'}`}>
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      <button className="fixed bottom-24 right-5 rounded-full bg-cyan-500/85 p-3 shadow-glow" aria-label="hydration target">
        <Droplets size={16} />
      </button>
    </main>
  );
}
