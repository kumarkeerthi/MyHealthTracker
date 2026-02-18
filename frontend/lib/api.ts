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
  water_ml: number;
  hydration_score: number;
  hydration_target_min_ml: number;
  hydration_target_max_ml: number;
  hydration_target_achieved: boolean;
  validations: {
    protein_minimum: boolean;
    carb_limit: boolean;
    oil_limit: boolean;
  };
  dinner_logged: boolean;
  dinner_carbs: number;
  dinner_protein: number;
  dinner_mode: string | null;
  dinner_insulin_impact: number;
  evening_insulin_spike_risk: boolean;
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
  protein_reminders_enabled: boolean;
  fasting_alerts_enabled: boolean;
  hydration_alerts_enabled: boolean;
  insulin_alerts_enabled: boolean;
  strength_reminders_enabled: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  movement_reminder_delay_minutes: number;
  movement_sensitivity: string;
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
  walk_vs_insulin_correlation: TrendSeries;
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

export type MovementPanel = {
  post_meal_walk_status: string;
  steps_today: number;
  walk_streak: number;
  recovery_prompt: string;
  badge?: string | null;
  alerts_remaining: number;
  post_meal_walk_bonus: boolean;
};

export type MovementSettings = {
  user_id: number;
  reminder_delay_minutes: number;
  sensitivity: 'strict' | 'balanced' | 'relaxed' | string;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  movement_reminder_delay_minutes: number;
  movement_sensitivity: string;
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

const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

let accessToken: string | null = null;

function getCsrfTokenFromCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const cookie = document.cookie.split('; ').find((item) => item.startsWith('csrf_token='));
  if (!cookie) return null;
  return decodeURIComponent(cookie.split('=')[1] ?? '');
}

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

async function apiRequest(path: string, init: RequestInit = {}, retryOn401 = true): Promise<Response> {
  const headers = new Headers(init.headers ?? {});
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  const method = (init.method ?? 'GET').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = getCsrfTokenFromCookie();
    if (csrf) headers.set('X-CSRF-Token', csrf);
  }
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers,
    credentials: 'include',
    cache: 'no-store',
  });

  if (response.status === 401 && retryOn401 && path !== '/auth/refresh') {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return apiRequest(path, init, false);
    }
  }

  return response;
}

async function readJson<T>(path: string): Promise<T | null> {
  try {
    const response = await apiRequest(path);
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function refreshAccessToken(): Promise<boolean> {
  const response = await fetch(`${baseUrl}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) {
    setAccessToken(null);
    return false;
  }
  const payload = (await response.json()) as { access_token: string };
  setAccessToken(payload.access_token);
  return true;
}

export async function getDashboardData(userId: number) {
  const [daily, profile, vitals, exercise, challenge, monthlyChallenge, recipes, recipeSuggestion, analytics, habitIntelligence, metabolicPerformance, movementPanel] = await Promise.all([
    readJson<DailySummary>(`/daily-summary?user_id=${userId}`),
    readJson<Profile>(`/profile?user_id=${userId}`),
    readJson<VitalsSummary>(`/vitals-summary?user_id=${userId}`),
    readJson<ExerciseSummary>(`/exercise-summary?user_id=${userId}`),
    readJson<Challenge>(`/challenge?user_id=${userId}`),
    readJson<Challenge>(`/challenge/monthly?user_id=${userId}`),
    readJson<Recipe[]>('/recipes'),
    readJson<RecipeSuggestion>(`/recipes/suggestions?user_id=${userId}`),
    readJson<AdvancedAnalytics>(`/analytics/advanced?user_id=${userId}&days=30`),
    readJson<HabitIntelligence>(`/habits/intelligence?user_id=${userId}&days=90`),
    readJson<MetabolicPhasePerformance>(`/metabolic/performance-view?user_id=${userId}`),
    readJson<MovementPanel>(`/movement/panel?user_id=${userId}`),
  ]);

  return { daily, profile, vitals, exercise, challenge, monthlyChallenge, recipes, recipeSuggestion, analytics, habitIntelligence, metabolicPerformance, movementPanel };
}

export async function getNotificationSettings() {
  return await readJson<NotificationSettings>('/notification-settings?user_id=1');
}

export async function updateNotificationSettings(payload: Partial<Omit<NotificationSettings, 'user_id'>>) {
  const response = await apiRequest('/notification-settings?user_id=1', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to update notification settings');
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
  if (mealContext) formData.append('meal_context', mealContext);
  const response = await apiRequest('/analyze-food-image', { method: 'POST', body: formData });
  if (!response.ok) throw new Error('Failed to analyze image');
  return (await response.json()) as AnalyzeFoodImageResponse;
}

export async function confirmFoodImageLog(payload: { foods: ImageAnalyzedFood[]; image_url: string; vision_confidence: number; portion_scale_factor: number; manual_adjustment_flag: boolean; meal_context?: string; }) {
  const response = await apiRequest('/analyze-food-image/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to confirm food log');
  return await response.json();
}

export async function getPushPublicKey() {
  return await readJson<{ public_key: string }>('/push/public-key');
}

export async function subscribePush(payload: { user_id: number; endpoint: string; expirationTime: number | null; keys: { p256dh: string; auth: string }; user_agent?: string; }) {
  const response = await apiRequest('/push/subscribe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!response.ok) throw new Error('Failed to subscribe for push');
  return await response.json();
}

export async function logHydration(amountMl: number) {
  const response = await apiRequest('/hydration/log', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: 1, amount_ml: amountMl }) });
  if (!response.ok) throw new Error('Failed to log hydration');
  return await response.json();
}

export async function getMovementSettings() {
  return await readJson<MovementSettings>('/movement/settings?user_id=1');
}

export type AuthMe = { id: number; email: string; role: string };

type AuthTokenResponse = { access_token: string };

export async function login(email: string, password: string): Promise<AuthTokenResponse> {
  const response = await fetch(`${baseUrl}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error('Invalid credentials');
  const payload = (await response.json()) as AuthTokenResponse;
  setAccessToken(payload.access_token);
  return payload;
}

export async function register(email: string, password: string): Promise<AuthTokenResponse> {
  const response = await fetch(`${baseUrl}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error('Registration failed');
  const payload = (await response.json()) as AuthTokenResponse;
  setAccessToken(payload.access_token);
  return payload;
}

export async function getMe(): Promise<AuthMe | null> {
  return await readJson<AuthMe>('/auth/me');
}

export async function logout() {
  const csrf = getCsrfTokenFromCookie();
  await fetch(`${baseUrl}/auth/logout`, { method: 'POST', credentials: 'include', headers: csrf ? { 'X-CSRF-Token': csrf } : undefined });
  setAccessToken(null);
}


export async function logFood(payload: { entries: Array<{ food_item_id: number; servings: number }>; meal_context?: string; dinner_mode?: string | null; consumed_at?: string; }) {
  const response = await apiRequest('/log-food', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 1, entries: payload.entries, meal_context: payload.meal_context ?? 'snack', dinner_mode: payload.dinner_mode ?? null, consumed_at: payload.consumed_at ?? new Date().toISOString() }),
  });
  if (!response.ok) throw new Error('Failed to log food');
  return await response.json();
}

export async function logVitals(payload: { resting_hr?: number; sleep_hours?: number; fasting_glucose?: number }) {
  const response = await apiRequest('/log-vitals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 1, recorded_at: new Date().toISOString(), ...payload }),
  });
  if (!response.ok) throw new Error('Failed to log vitals');
  return await response.json();
}

export async function logExercise(payload: { activity_type: string; duration_minutes: number; exercise_category?: string; movement_type?: string }) {
  const response = await apiRequest('/log-exercise', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 1, exercise_category: payload.exercise_category ?? 'STRENGTH', activity_type: payload.activity_type, movement_type: payload.movement_type ?? 'general', muscle_group: 'full_body', duration_minutes: payload.duration_minutes, perceived_intensity: 5, progression_level: 1 }),
  });
  if (!response.ok) throw new Error('Failed to log exercise');
  return await response.json();
}

export type ParsedReportParameter = { name: string; normalized_key: string; value: number; unit: string; reference_range?: string | null; };
export type ParsedReport = { file_token: string; report_date: string | null; parameters: ParsedReportParameter[] };

export async function uploadReport(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiRequest('/reports/upload', { method: 'POST', body: formData });
  if (!response.ok) throw new Error('Failed to upload report');
  return (await response.json()) as ParsedReport;
}

export async function confirmReport(payload: ParsedReport) {
  const response = await apiRequest('/reports/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to save report');
  return await response.json();
}
