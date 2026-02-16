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

export type NotificationSettings = {
  user_id: number;
  whatsapp_enabled: boolean;
  push_enabled: boolean;
  email_enabled: boolean;
  silent_mode: boolean;
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
  const [daily, profile, vitals, exercise] = await Promise.all([
    readJson<DailySummary>('/daily-summary?user_id=1'),
    readJson<Profile>('/profile?user_id=1'),
    readJson<VitalsSummary>('/vitals-summary?user_id=1'),
    readJson<ExerciseSummary>('/exercise-summary?user_id=1'),
  ]);

  return {
    daily,
    profile,
    vitals,
    exercise,
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
