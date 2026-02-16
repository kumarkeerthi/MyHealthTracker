export function ChallengesView({ challengeTitle, challengeDesc, streak }: { challengeTitle: string; challengeDesc: string; streak: number }) {
  return (
    <section className="glass-card p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Challenges</p>
      <p className="mt-2 text-lg font-semibold text-white">{challengeTitle}</p>
      <p className="mt-1 text-sm text-slate-300">{challengeDesc}</p>
      <p className="mt-3 text-sm text-emerald-200">Current streak: {streak} days</p>
    </section>
  );
}
