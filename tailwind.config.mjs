/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        base: {
          950: 'rgb(var(--base-950) / <alpha-value>)',
          900: 'rgb(var(--base-900) / <alpha-value>)',
          800: 'rgb(var(--base-800) / <alpha-value>)',
          700: 'rgb(var(--base-700) / <alpha-value>)',
          600: 'rgb(var(--base-600) / <alpha-value>)',
        },
        ink: {
          DEFAULT: 'rgb(var(--ink) / <alpha-value>)',
          muted: 'rgb(var(--muted) / <alpha-value>)',
          inverse: 'rgb(var(--ink-inverse) / <alpha-value>)',
        },
        line: {
          DEFAULT: 'rgb(var(--line) / <alpha-value>)',
          strong: 'rgb(var(--line-strong) / <alpha-value>)',
        },
        brand: {
          blue: 'rgb(var(--accent) / <alpha-value>)',
          glow: 'rgb(var(--accent-strong) / <alpha-value>)',
          emerald: 'rgb(var(--accent) / <alpha-value>)',
          amber: 'rgb(var(--accent) / <alpha-value>)',
          purple: 'rgb(var(--accent) / <alpha-value>)',
          gold: 'rgb(var(--accent) / <alpha-value>)',
        }
      },
      fontFamily: {
        sans: [
          '"Plus Jakarta Sans"',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
        serif: ['"Instrument Serif"', '"Playfair Display"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
};
