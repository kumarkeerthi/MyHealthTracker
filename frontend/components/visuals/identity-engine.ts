export type IdentityInputs = {
  waistReductionCm: number;
  strengthIncrease: boolean;
  cleanStreakDays: number;
  hdlSupportDays: number;
  insulinLoad: number;
  carbCeilingMaintained: boolean;
  hydrationTargetAchieved: boolean;
  fastingWindowIntact: boolean;
  monkeyBarProgress: boolean;
  pushupImprovement: boolean;
  strengthIndexRising: boolean;
  consistencyStreak: number;
  noCarbDinnerStreak: number;
  proteinCompliance7d: boolean;
};

export type EmotionSignal = {
  label: string;
  active: boolean;
};

export type EmotionState = {
  pride: EmotionSignal[];
  control: EmotionSignal[];
  strength: EmotionSignal[];
  discipline: EmotionSignal[];
  prideScore: number;
  controlScore: number;
  strengthScore: number;
  disciplineScore: number;
};

export type IdentityTier = 'Bronze' | 'Silver' | 'Gold' | 'Elite';

export type IdentityVisualMode = 'controlled_strength' | 'recomposition' | 'stabilizing' | 'foundation';

export function computeEmotionState(inputs: IdentityInputs): EmotionState {
  const pride = [
    { label: 'Waist reduction', active: inputs.waistReductionCm >= 1 },
    { label: 'Strength increase', active: inputs.strengthIncrease },
    { label: 'Clean streak > 5 days', active: inputs.cleanStreakDays > 5 },
    { label: 'HDL-support days', active: inputs.hdlSupportDays >= 4 },
  ];

  const control = [
    { label: 'Insulin Load < 40', active: inputs.insulinLoad < 40 },
    { label: 'Carb ceiling maintained', active: inputs.carbCeilingMaintained },
    { label: 'Hydration target achieved', active: inputs.hydrationTargetAchieved },
    { label: 'Fasting window intact', active: inputs.fastingWindowIntact },
  ];

  const strength = [
    { label: 'Monkey bar progress', active: inputs.monkeyBarProgress },
    { label: 'Pushup improvement', active: inputs.pushupImprovement },
    { label: 'Strength Index rising', active: inputs.strengthIndexRising },
  ];

  const discipline = [
    { label: 'Consistency streak', active: inputs.consistencyStreak >= 5 },
    { label: 'No carb dinner streak', active: inputs.noCarbDinnerStreak >= 3 },
    { label: '7-day protein compliance', active: inputs.proteinCompliance7d },
  ];

  return {
    pride,
    control,
    strength,
    discipline,
    prideScore: toPercent(pride),
    controlScore: toPercent(control),
    strengthScore: toPercent(strength),
    disciplineScore: toPercent(discipline),
  };
}

export function resolveIdentityState(emotion: EmotionState): { label: string; mode: IdentityVisualMode } {
  const allGood = [emotion.prideScore, emotion.controlScore, emotion.strengthScore, emotion.disciplineScore].every((score) => score >= 75);
  if (allGood) {
    return { label: 'Controlled Strength Mode', mode: 'controlled_strength' };
  }

  if (emotion.pride[0]?.active && emotion.pride[1]?.active) {
    return { label: 'Recomposition Active', mode: 'recomposition' };
  }

  if (!emotion.control[0]?.active) {
    return { label: 'Stabilizing', mode: 'stabilizing' };
  }

  return { label: 'Foundation Building', mode: 'foundation' };
}

export function computeIdentityScore(params: {
  strengthScore: number;
  insulinControlScore: number;
  habitConsistencyScore: number;
  waistImprovementScore: number;
}): { score: number; tier: IdentityTier } {
  const weightedScore =
    params.strengthScore * 0.3
    + params.insulinControlScore * 0.3
    + params.habitConsistencyScore * 0.2
    + params.waistImprovementScore * 0.2;

  const score = clamp(weightedScore, 0, 100);

  if (score >= 85) return { score, tier: 'Elite' };
  if (score >= 70) return { score, tier: 'Gold' };
  if (score >= 50) return { score, tier: 'Silver' };
  return { score, tier: 'Bronze' };
}

export function computeIdentityVisualState(params: {
  mode: IdentityVisualMode;
  insulinScore: number;
  strengthScore: number;
}) {
  const insulinControl = clamp((60 - params.insulinScore) / 40, 0, 1);
  const muscleDefinition = clamp(params.strengthScore / 100, 0, 1);

  if (params.mode === 'stabilizing') {
    return {
      postureLift: 0,
      abdomenGlowOpacity: 0.3,
      muscleDefinition: muscleDefinition * 0.55,
    };
  }

  return {
    postureLift: params.mode === 'controlled_strength' ? 6 : params.mode === 'recomposition' ? 4 : 2,
    abdomenGlowOpacity: 0.35 - insulinControl * 0.22,
    muscleDefinition: muscleDefinition * (params.mode === 'controlled_strength' ? 1 : 0.8),
  };
}

function toPercent(signals: EmotionSignal[]) {
  if (!signals.length) return 0;
  const activeCount = signals.filter((signal) => signal.active).length;
  return Math.round((activeCount / signals.length) * 100);
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}
