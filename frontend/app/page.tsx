import { Dashboard } from '@/components/dashboard';
import { getDashboardData } from '@/lib/api';

export default async function Home() {
  const { daily, profile, vitals } = await getDashboardData();

  const insulin = Math.round(daily?.insulin_load_score ?? 38);
  const complianceSignals = [
    daily?.validations?.protein_minimum,
    daily?.validations?.carb_limit,
    daily?.validations?.oil_limit,
  ].filter(Boolean).length;

  const compliance = Math.round((complianceSignals / 3) * 100) || 66;

  return (
    <Dashboard
      insulinScore={insulin}
      compliance={compliance}
      protein={daily?.total_protein ?? 62}
      carbs={daily?.total_carbs ?? 54}
      oil={daily?.total_hidden_oil ?? 2.1}
      chapatiCount={Math.min(1, profile?.max_chapati_per_day ?? 2)}
      chapatiLimit={profile?.max_chapati_per_day ?? 2}
      restingHr={vitals?.latest_resting_hr ?? 72}
      sleepHours={vitals?.latest_sleep_hours ?? 6.8}
    />
  );
}
