/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#172033',
        muted: '#667085',
        line: '#e6eaf0',
        canvas: '#f7f8fc',
        signal: '#4f46e5',
        'signal-dark': '#3730a3',
        teal: '#0f9f8c',
      },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
      boxShadow: { soft: '0 14px 34px rgba(23,32,51,.07)', card: '0 1px 3px rgba(23,32,51,.05)' },
      borderRadius: { '2.5xl': '1.25rem' },
    },
  },
  plugins: [],
}
