/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0B0F19',
          900: '#111827',
          850: '#161F32',
          800: '#1E293B',
          700: '#334155',
          600: '#475569',
        },
        brand: {
          blue: '#2563EB',
          teal: '#0D9488',
          cyan: '#06B6D4',
          sky: '#0284C7',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
