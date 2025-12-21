/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  // Dark mode only - 'class' strategy with html.dark always set
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Navy-First Design System
        navy: {
          app: '#0b1020',       // Deepest - app bg
          surface: '#0f172a',   // Cards, modals
          elevated: '#131c3a',  // Hover, focus
          subtle: '#0c142e',    // Rows, separators
          inset: '#080d1a',     // Code blocks
          border: '#1f2a55',    // Default border
          'border-subtle': '#161f42',
          'border-strong': '#2a3a6e',
        },
        // Accent colors (text/icons only)
        accent: {
          success: '#4ade80',
          warning: '#fbbf24',
          danger: '#f87171',
          info: '#60a5fa',
          primary: '#818cf8',
        },
        // Legacy primary (for compatibility)
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
