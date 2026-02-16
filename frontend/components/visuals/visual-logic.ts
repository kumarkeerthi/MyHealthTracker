export type VisualMode = 'clinical' | 'performance';

export type BodyVisualState = {
  waistScale: number;
  visceralTone: 'high' | 'controlled';
  energyAura: boolean;
  comparisonScale: number;
};

export type StrengthVisualState = {
  armActive: boolean;
  backActive: boolean;
  gripActive: boolean;
  strengthIndex: number;
  gripEndurancePct: number;
  pullStrengthPct: number;
};

export function computeBodyVisualState(params: {
  insulinScore: number;
  hydrationTargetAchieved: boolean;
  proteinHit: boolean;
  carbUnderCeiling: boolean;
  baselineWaist: number;
  currentWaist: number;
}): BodyVisualState {
  const waistDelta = Math.max(-12, Math.min(12, params.currentWaist - params.baselineWaist));
  return {
    waistScale: Math.max(0.82, Math.min(1.08, 1 + waistDelta / 100)),
    visceralTone: params.insulinScore < 40 ? 'controlled' : 'high',
    energyAura: params.hydrationTargetAchieved && params.proteinHit,
    comparisonScale: params.carbUnderCeiling ? 0.92 : 1,
  };
}

export function computeStrengthVisualState(params: {
  pushupsLogged: boolean;
  pullupsLogged: boolean;
  monkeyBarTracked: boolean;
  strengthIndex: number;
  gripEnduranceSeconds: number;
  pullUps: number;
}): StrengthVisualState {
  return {
    armActive: params.pushupsLogged,
    backActive: params.pullupsLogged,
    gripActive: params.monkeyBarTracked,
    strengthIndex: Math.max(0, Math.min(100, params.strengthIndex)),
    gripEndurancePct: Math.max(0, Math.min(100, (params.gripEnduranceSeconds / 180) * 100)),
    pullStrengthPct: Math.max(0, Math.min(100, (params.pullUps / 20) * 100)),
  };
}

export function computeStatusBadges(params: {
  insulinScore: number;
  strengthStreakDays: number;
  hydrationTargetAchieved: boolean;
  carbUnderCeiling: boolean;
  streakDays: number;
}) {
  return [
    params.insulinScore < 40 ? 'Controlled' : null,
    params.strengthStreakDays > 5 ? 'Consistent' : null,
    params.hydrationTargetAchieved ? 'Hydrated' : null,
    params.carbUnderCeiling && params.streakDays >= 7 ? 'Triglyceride Drop Mode' : null,
  ].filter((badge): badge is string => Boolean(badge));
}

export function metabolicMomentumBanner(insulinScore: number, carbUnderCeiling: boolean, strengthIndex: number) {
  if (insulinScore < 35 && strengthIndex > 60) return 'Burn Phase';
  if (carbUnderCeiling && strengthIndex > 40) return 'Recomposition Mode';
  return 'HDL Recovery Active';
}
