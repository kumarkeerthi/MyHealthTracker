import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: ['./app/**/*.{js,ts,jsx,tsx,mdx}', './components/**/*.{js,ts,jsx,tsx,mdx}', './lib/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0f172a',
        card: '#111827',
        borderSoft: '#253149',
        electric: '#3b82f6',
        emerald: '#34d399',
        amber: '#f59e0b',
        crimson: '#ef4444',
        purpleSoft: '#a78bfa',
      },
      backgroundImage: {
        'hero-gradient': 'radial-gradient(circle at top, rgba(59,130,246,0.22) 0%, rgba(15,23,42,1) 55%)',
        'card-gradient': 'linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02))',
      },
      boxShadow: {
        glow: '0 16px 40px rgba(59, 130, 246, 0.2)',
        emerald: '0 0 24px rgba(52, 211, 153, 0.45)',
      },
      keyframes: {
        riseIn: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(52, 211, 153, 0.25)' },
          '50%': { boxShadow: '0 0 28px rgba(52, 211, 153, 0.75)' },
        },
      },
      animation: {
        riseIn: 'riseIn 450ms ease-out forwards',
        pulseGlow: 'pulseGlow 2.2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

export default config;
