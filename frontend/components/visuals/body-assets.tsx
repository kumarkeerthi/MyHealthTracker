import type { BodyVisualState, StrengthVisualState } from '@/components/visuals/visual-logic';

export function NeutralBodyOutline({ state, className = '' }: { state: BodyVisualState; className?: string }) {
  const aura = state.energyAura ? 'drop-shadow-[0_0_14px_rgba(16,185,129,0.6)]' : '';
  const abdomenGlow = state.visceralTone === 'controlled' ? `rgba(16,185,129,${state.abdomenGlowOpacity})` : `rgba(239,68,68,${Math.max(0.18, state.abdomenGlowOpacity)})`;

  return (
    <svg viewBox="0 0 220 360" className={`w-full ${className} ${aura}`}>
      <defs>
        <linearGradient id="bodyShade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(148,163,184,0.22)" />
          <stop offset="100%" stopColor="rgba(51,65,85,0.08)" />
        </linearGradient>
      </defs>
      <circle cx="110" cy="42" r="24" stroke="rgba(203,213,225,0.75)" strokeWidth="2" fill="url(#bodyShade)" />
      <g transform={`translate(0 ${8 - state.postureLift}) scale(${state.waistScale} 1)`}>
        <path d="M70 78 C58 124, 58 196, 78 256 C87 283, 90 312, 90 344 M150 78 C162 124, 162 196, 142 256 C133 283, 130 312, 130 344" stroke="rgba(203,213,225,0.8)" strokeWidth="3" fill="none" strokeLinecap="round" />
      </g>
      <ellipse cx="110" cy="176" rx="31" ry="38" fill={abdomenGlow} className="transition-all duration-300" />
      <ellipse cx="110" cy="170" rx={24 + state.muscleDefinition * 6} ry={30 + state.muscleDefinition * 4} fill={`rgba(148,163,184,${0.08 + state.muscleDefinition * 0.15})`} className="transition-all duration-300" />
      <path d="M56 120 C34 168, 29 232, 48 270 M164 120 C186 168, 191 232, 172 270" stroke="rgba(148,163,184,0.55)" strokeWidth="2" fill="none" />
      <path d="M95 344 L81 356 M125 344 L139 356" stroke="rgba(148,163,184,0.65)" strokeWidth="2" />
    </svg>
  );
}

export function StrengthOverlay({ state }: { state: StrengthVisualState }) {
  return (
    <svg viewBox="0 0 220 360" className="w-full">
      <rect x="42" y="122" width="24" height="120" rx="12" fill={state.armActive ? 'rgba(59,130,246,0.45)' : 'rgba(71,85,105,0.2)'} />
      <rect x="154" y="122" width="24" height="120" rx="12" fill={state.armActive ? 'rgba(59,130,246,0.45)' : 'rgba(71,85,105,0.2)'} />
      <ellipse cx="110" cy="152" rx="54" ry="56" fill={state.backActive ? 'rgba(167,139,250,0.34)' : 'rgba(71,85,105,0.2)'} />
      <circle cx="54" cy="250" r="13" fill={state.gripActive ? 'rgba(16,185,129,0.5)' : 'rgba(71,85,105,0.3)'} />
      <circle cx="166" cy="250" r="13" fill={state.gripActive ? 'rgba(16,185,129,0.5)' : 'rgba(71,85,105,0.3)'} />
    </svg>
  );
}

export function HeartIcon({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className}>
      <path d="M32 54 C8 38, 8 18, 22 14 C28 12, 32 16, 32 21 C32 16, 36 12, 42 14 C56 18, 56 38, 32 54Z" fill="rgba(244,63,94,0.75)" />
    </svg>
  );
}

export function CleanArteryIcon({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className}>
      <path d="M10 34 C20 10, 44 10, 54 34" stroke="rgba(16,185,129,0.9)" strokeWidth="5" fill="none" strokeLinecap="round" />
      <path d="M10 40 C20 16, 44 16, 54 40" stroke="rgba(16,185,129,0.45)" strokeWidth="5" fill="none" strokeLinecap="round" />
    </svg>
  );
}

export function HeartPulseLine({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 120 40" className={className}>
      <path d="M2 22 H28 L36 12 L44 30 L53 18 H118" stroke="rgba(56,189,248,0.9)" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ShieldIcon({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className}>
      <path d="M32 8 L50 14 V30 C50 42, 42 52, 32 56 C22 52, 14 42, 14 30 V14 Z" fill="rgba(52,211,153,0.55)" stroke="rgba(167,243,208,0.9)" strokeWidth="2" />
    </svg>
  );
}
