import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#05070C',
        card: '#0E121D',
        borderSoft: '#1E2635',
        accent: '#7C9BFF',
        mint: '#57E6B0',
        amber: '#F6C96A',
      },
      boxShadow: {
        glow: '0 12px 40px rgba(124, 155, 255, 0.18)',
      },
      keyframes: {
        riseIn: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        riseIn: 'riseIn 450ms ease-out forwards',
      },
    },
  },
  plugins: [],
};

export default config;
