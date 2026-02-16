import { motion } from 'framer-motion';
import { NeutralBodyOutline } from '@/components/visuals/body-assets';
import type { BodyVisualState } from '@/components/visuals/visual-logic';
import { pulseTransition } from '@/components/visuals/animation-config';

export function BodyProgressView({ bodyState }: { bodyState: BodyVisualState }) {
  return (
    <section className="space-y-4">
      <div className="glass-card overflow-hidden bg-slate-950 p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Body Progress View</p>
        <motion.div className="relative mx-auto mt-3 w-52" {...pulseTransition}>
          <div className="absolute inset-0 rounded-full bg-gradient-to-b from-white/10 to-transparent blur-2xl" />
          <motion.div animate={{ scaleX: bodyState.waistScale }} transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}>
            <NeutralBodyOutline state={bodyState} />
          </motion.div>
        </motion.div>
        <p className="mt-3 text-xs text-slate-300">Waist shape updates weekly with smooth transitions.</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="glass-card p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Week 1</p>
          <NeutralBodyOutline state={{ ...bodyState, waistScale: 1 }} className="mx-auto mt-2 w-28 opacity-70" />
        </div>
        <div className="glass-card p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Current</p>
          <motion.div animate={{ scaleX: bodyState.waistScale }} transition={{ duration: 0.32 }}>
            <NeutralBodyOutline state={bodyState} className="mx-auto mt-2 w-28" />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
