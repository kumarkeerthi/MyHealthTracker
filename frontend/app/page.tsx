import { Dashboard } from '@/components/dashboard';
import { getDashboardData } from '@/lib/api';

export default async function Home() {
  const { daily, profile, vitals, exercise, challenge, monthlyChallenge, recipes, recipeSuggestion, analytics, habitIntelligence, metabolicPerformance } = await getDashboardData();

  const insulin = Math.round(daily?.insulin_load_score ?? 38);
  const complianceSignals = [daily?.validations?.protein_minimum, daily?.validations?.carb_limit, daily?.validations?.oil_limit].filter(Boolean).length;

  const compliance = Math.round((complianceSignals / 3) * 100) || 66;

  return (
    <Dashboard
      insulinScore={insulin}
      compliance={compliance}
      protein={daily?.total_protein ?? 62}
      carbs={daily?.total_carbs ?? 54}
      oil={daily?.total_hidden_oil ?? 2.1}
      sugar={daily?.total_sugar ?? 0}
      fiber={daily?.total_fiber ?? 0}
      fruitServings={daily?.fruit_servings ?? 0}
      fruitBudget={daily?.fruit_budget ?? 1}
      nutServings={daily?.nuts_servings ?? 0}
      nutBudget={daily?.nuts_budget ?? 1}
      remainingCarbBudget={daily?.remaining_carb_budget ?? 0}
      fruitNutWarnings={daily?.warnings ?? []}
      chapatiCount={Math.min(1, profile?.max_chapati_per_day ?? 2)}
      chapatiLimit={profile?.max_chapati_per_day ?? 2}
      restingHr={vitals?.latest_resting_hr ?? 72}
      sleepHours={vitals?.latest_sleep_hours ?? 6.8}
      proteinHit={daily?.validations?.protein_minimum ?? true}
      carbUnderCeiling={daily?.validations?.carb_limit ?? true}
      strengthIndex={exercise?.strength_index ?? 0}
      gripImprovementPct={exercise?.grip_strength_improvement_pct ?? 0}
      monkeyBarProgress={exercise?.monkey_bar_progress ?? { dead_hang_duration_seconds: 0, pull_up_count: 0, assisted_pull_up_reps: 0, grip_endurance_seconds: 0 }}
      weeklyStrengthGraph={exercise?.weekly_strength_graph ?? [0, 0, 0, 0, 0, 0, 0]}
      metabolicExerciseMessage={exercise?.metabolic_message ?? 'Strength momentum stable'}
      challenge={challenge ?? {
        title: 'Protein First Day',
        description: 'Start each meal with protein to reduce glucose spikes.',
        current_streak: 0,
        longest_streak: 0,
        completed: false,
        banner_title: '7 Day Insulin Control Challenge',
      }}
      monthlyChallenge={monthlyChallenge ?? {
        title: '10k Step Day',
        description: 'Complete at least 20 days above 10k steps this month.',
        completed: false,
      }}
      recipeSuggestion={recipeSuggestion?.suggestion ?? 'Based on carb load remaining, try: Spinach + tofu stir fry.'}
      carbLoadRemaining={recipeSuggestion?.carb_load_remaining ?? 0}
      recipes={recipes ?? recipeSuggestion?.recipes ?? []}
      analytics={analytics ?? null}
      habitIntelligence={habitIntelligence ?? null}
      metabolicPerformance={metabolicPerformance ?? null}
      waterMl={daily?.water_ml ?? 0}
      hydrationScore={daily?.hydration_score ?? 0}
      hydrationTargetMinMl={daily?.hydration_target_min_ml ?? 2500}
      hydrationTargetAchieved={daily?.hydration_target_achieved ?? false}
      streakDays={challenge?.current_streak ?? 0}
      strengthStreakDays={Math.max(0, Math.round((exercise?.grip_strength_improvement_pct ?? 0) / 5))}
      fastingWindowIntact={daily?.validations?.carb_limit ?? true}
      waistChangeCm={Math.max(0, (challenge?.current_streak ?? 0) * 0.2)}
      noCarbDinnerStreak={Math.floor((challenge?.current_streak ?? 0) / 2)}
    />
  );
}
