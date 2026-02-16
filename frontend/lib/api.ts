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
  const [daily, profile, vitals] = await Promise.all([
    readJson<DailySummary>('/daily-summary?user_id=1'),
    readJson<Profile>('/profile?user_id=1'),
    readJson<VitalsSummary>('/vitals-summary?user_id=1'),
  ]);

  return {
    daily,
    profile,
    vitals,
  };
}
