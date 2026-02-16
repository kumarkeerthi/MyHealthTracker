import type { CSSProperties, ReactNode } from 'react';

type MotionProps = {
  children?: ReactNode;
  className?: string;
  style?: CSSProperties;
  [key: string]: unknown;
};

function MotionDiv({ children, ...rest }: MotionProps) {
  return <div {...(rest as Record<string, unknown>)}>{children}</div>;
}

function MotionSvg({ children, ...rest }: MotionProps) {
  return <svg {...(rest as Record<string, unknown>)}>{children}</svg>;
}

function MotionPath(props: MotionProps) {
  return <path {...(props as Record<string, unknown>)} />;
}

export const motion = {
  div: MotionDiv,
  svg: MotionSvg,
  path: MotionPath,
};

export function AnimatePresence({ children }: { children: ReactNode; mode?: 'wait' | 'sync' | 'popLayout' }) {
  return <>{children}</>;
}
