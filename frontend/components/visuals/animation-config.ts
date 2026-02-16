export const tabTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.3, ease: 'easeOut' },
};

export const pulseTransition = {
  animate: {
    opacity: [0.35, 0.75, 0.35],
    scale: [0.98, 1.02, 0.98],
  },
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};
