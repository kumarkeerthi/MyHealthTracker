export const tabTransition = {
  initial: { opacity: 0, y: 10, filter: 'blur(2px)' },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)' },
  exit: { opacity: 0, y: -10, filter: 'blur(2px)' },
  transition: { duration: 0.32, ease: [0.22, 1, 0.36, 1] },
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
