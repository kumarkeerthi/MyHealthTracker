import { motion } from 'framer-motion';

export function ChallengesView({ challengeTitle, challengeDesc, streak }: { challengeTitle: string; challengeDesc: string; streak: number }) {
  return (
    <section className="glass-card p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Challenges</p>
      <p className="mt-2 text-lg font-semibold text-white">{challengeTitle}</p>
      <p className="mt-1 text-sm text-slate-300">{challengeDesc}</p>
      <motion.div className="mt-3 text-sm text-emerald-200" key={streak} initial={{ scale: 0.95, opacity: 0.7 }} animate={{ scale: [1, 1.04, 1], opacity: 1 }} transition={{ duration: 0.3 }}>
        Current streak: {streak} days
      </motion.div>
    </section>
  );
}
