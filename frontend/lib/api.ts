export type DailySummary = {
  total_protein: number;
  total_carbs: number;
  total_hidden_oil: number;
  insulin_load_score: number | null;
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

export type RecipeSuggestion = {
  user_id: number;
  carb_load_remaining: number;
  suggestion: string;
  recipes: Recipe[];
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
  const [daily, profile, vitals, exercise, challenge, monthlyChallenge, recipes, recipeSuggestion] = await Promise.all([
    readJson<DailySummary>('/daily-summary?user_id=1'),
    readJson<Profile>('/profile?user_id=1'),
    readJson<VitalsSummary>('/vitals-summary?user_id=1'),
    readJson<ExerciseSummary>('/exercise-summary?user_id=1'),
    readJson<Challenge>('/challenge?user_id=1'),
    readJson<Challenge>('/challenge/monthly?user_id=1'),
    readJson<Recipe[]>('/recipes'),
    readJson<RecipeSuggestion>('/recipes/suggestions?user_id=1'),
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
