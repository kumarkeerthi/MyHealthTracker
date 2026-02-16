export type DailySummary = {
  total_protein: number;
  total_carbs: number;
  total_hidden_oil: number;
  total_sugar: number;
  total_fiber: number;
  insulin_load_score: number | null;
  fruit_servings: number;
  fruit_budget: number;
  nuts_servings: number;
  nuts_budget: number;
  remaining_carb_budget: number;
  warnings: string[];
  validations: {
    protein_minimum: boolean;
    carb_limit: boolean;
    oil_limit: boolean;
  };
};

export type Profile = {
  max_chapati_per_day: number;
};

export type VitalsSummary = {
  latest_resting_hr: number | null;
  latest_sleep_hours: number | null;
};

export type ExerciseSummary = {
  strength_index: number;
  grip_strength_improvement_pct: number;
  metabolic_message: string;
  monkey_bar_progress: {
    dead_hang_duration_seconds: number;
    pull_up_count: number;
    assisted_pull_up_reps: number;
    grip_endurance_seconds: number;
  };
  weekly_strength_graph: number[];
};

export type Challenge = {
  challenge_id: number;
  frequency: string;
  title: string;
  description: string;
  goal_metric: string;
  goal_target: number;
  completed: boolean;
  current_streak: number;
  longest_streak: number;
  banner_title: string;
};

export type NotificationSettings = {
  user_id: number;
  whatsapp_enabled: boolean;
  push_enabled: boolean;
  email_enabled: boolean;
  silent_mode: boolean;
};

export type Recipe = {
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
};



export type AnalyticsPoint = {
  date: string;
  value: number;
};

export type TrendSeries = {
  key: string;
  label: string;
  trend: 'improvement' | 'steady' | 'regression';
  improving: boolean;
  points: AnalyticsPoint[];
};

export type AdvancedAnalytics = {
  start_date: string;
  end_date: string;
  insulin_load_trend: TrendSeries;
  fruit_frequency_trend: TrendSeries;
  nut_frequency_trend: TrendSeries;
  sugar_load_trend: TrendSeries;
  hdl_support_trend: TrendSeries;
  waist_trend: TrendSeries;
  weight_trend: TrendSeries;
  protein_intake_consistency: TrendSeries;
  carb_intake_pattern: TrendSeries;
  oil_usage_pattern: TrendSeries;
  strength_score_trend: TrendSeries;
  grip_strength_trend: TrendSeries;
  sleep_trend: TrendSeries;
  resting_heart_rate_trend: TrendSeries;
  habit_compliance_trend: TrendSeries;
  clean_streak_trend: TrendSeries;
  metabolic_momentum: {
    score: number;
    insulin_load_component: number;
    waist_component: number;
    strength_component: number;
    sleep_component: number;
  };
};



export type HabitFailurePattern = {
  reason: string;
  count: number;
};

export type HabitStat = {
  habit_id: number;
  code: string;
  name: string;
  description: string;
  challenge_type: string;
  recommended_challenge_type: string;
  current_streak: number;
  longest_streak: number;
  success_rate: number;
  failures: number;
  failure_patterns: HabitFailurePattern[];
};

export type HabitHeatmapCell = {
  date: string;
  intensity: number;
  count: number;
};

export type HabitIntelligence = {
  habits: HabitStat[];
  heatmap: HabitHeatmapCell[];
  insights: string[];
  overall_success_rate: number;
};

export type RecipeSuggestion = {
  user_id: number;
  carb_load_remaining: number;
  suggestion: string;
  recipes: Recipe[];
};

export type MetabolicPhasePerformance = {
  phase_model: {
    current_phase: 'RESET' | 'STABILIZATION' | 'RECOMPOSITION' | 'PERFORMANCE' | 'MAINTENANCE';
    identity: string;
    rules: {
      carb_ceiling: string;
      rice_rule: string;
      fruit_rule: string;
      strength_rule: string;
      identity: string;
    };
    all_phases: Array<{
      phase: 'RESET' | 'STABILIZATION' | 'RECOMPOSITION' | 'PERFORMANCE' | 'MAINTENANCE';
      identity: string;
      carb_ceiling: string;
      strength_rule: string;
    }>;
  };
  transition_logic: {
    should_transition: boolean;
    reason: string;
    signals: Record<string, boolean | number>;
  };
  carb_tolerance: {
    carb_challenge_day_logged: boolean;
    protocol: string;
    next_day_metrics: Record<string, number | null>;
    carb_tolerance_index: number;
    evaluation: string;
  };
  performance_dashboard: {
    strength_index: number;
    grip_score: number;
    carb_tolerance_index: number;
    recovery_score: number;
    sleep_consistency: number;
  };
  periodization: {
    monthly_cycle: Array<{ week: number; focus: string; target: string }>;
    monkey_bar_metrics: Record<string, number>;
  };
  example_transition_scenario: {
    starting_phase: string;
    outcome: string;
    next_constraints: Record<string, string>;
  };
};

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

async function readJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${baseUrl}${path}`, { cache: 'no-store' });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function getDashboardData() {
  const [daily, profile, vitals, exercise, challenge, monthlyChallenge, recipes, recipeSuggestion, analytics, habitIntelligence, metabolicPerformance] = await Promise.all([
    readJson<DailySummary>('/daily-summary?user_id=1'),
    readJson<Profile>('/profile?user_id=1'),
    readJson<VitalsSummary>('/vitals-summary?user_id=1'),
    readJson<ExerciseSummary>('/exercise-summary?user_id=1'),
    readJson<Challenge>('/challenge?user_id=1'),
    readJson<Challenge>('/challenge/monthly?user_id=1'),
    readJson<Recipe[]>('/recipes'),
    readJson<RecipeSuggestion>('/recipes/suggestions?user_id=1'),
    readJson<AdvancedAnalytics>('/analytics/advanced?user_id=1&days=30'),
    readJson<HabitIntelligence>('/habits/intelligence?user_id=1&days=90'),
    readJson<MetabolicPhasePerformance>('/metabolic/performance-view?user_id=1'),
  ]);

  return {
    daily,
    profile,
    vitals,
    exercise,
    challenge,
    monthlyChallenge,
    recipes,
    recipeSuggestion,
    analytics,
    habitIntelligence,
    metabolicPerformance,
  };
}

export async function getNotificationSettings() {
  return await readJson<NotificationSettings>('/notification-settings?user_id=1');
}

export async function updateNotificationSettings(payload: Partial<Omit<NotificationSettings, 'user_id'>>) {
  const response = await fetch(`${baseUrl}/notification-settings?user_id=1`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error('Failed to update notification settings');
  }

  return (await response.json()) as NotificationSettings;
}


export type ImageAnalyzedFood = {
  name: string;
  estimated_quantity_grams: number;
  confidence: number;
  estimated_protein: number;
  estimated_carbs: number;
  estimated_fat: number;
  estimated_hidden_oil: number;
};

export type AnalyzeFoodImageResponse = {
  foods: ImageAnalyzedFood[];
  plate_estimated_total_calories: number;
  overall_confidence: number;
  portion_scale_factor: number;
  portion_estimation_confidence: 'LOW' | 'MEDIUM' | 'HIGH';
  image_url: string;
  estimated_macros: { protein: number; carbs: number; fats: number };
  estimated_oil_tsp: number;
  insulin_load_impact: number;
  projected_daily_insulin_score: number;
  approval: 'Approved' | 'Moderate' | 'High Insulin Load';
  validation: { message: string; low_confidence_flag: boolean };
  coaching: { primary_message: string; tags: string[] };
  llm_prompt_template: string;
  example_analysis_json: Record<string, unknown>;
};

export async function analyzeFoodImage(file: File, mealContext?: string) {
  const formData = new FormData();
  formData.append('image', file);
  if (mealContext) {
    formData.append('meal_context', mealContext);
  }

  const response = await fetch(`${baseUrl}/analyze-food-image`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to analyze image');
  }

  return (await response.json()) as AnalyzeFoodImageResponse;
}

export async function confirmFoodImageLog(payload: {
  foods: ImageAnalyzedFood[];
  image_url: string;
  vision_confidence: number;
  portion_scale_factor: number;
  manual_adjustment_flag: boolean;
  meal_context?: string;
}) {
  const response = await fetch(`${baseUrl}/analyze-food-image/confirm`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error('Failed to confirm food log');
  }

  return await response.json();
}
