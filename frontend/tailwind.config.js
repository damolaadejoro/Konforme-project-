/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0B1F3A',
          50: '#E8EDF4',
          100: '#C5D0DF',
          200: '#9AAFC8',
          300: '#6F8DB0',
          400: '#4F729F',
          500: '#305789',
          600: '#244471',
          700: '#183459',
          800: '#0E2445',
          900: '#0B1F3A',
          950: '#071426',
        },
        cyan: {
          DEFAULT: '#00C2D4',
          50: '#E0F9FB',
          100: '#B3F0F5',
          200: '#80E6EF',
          300: '#4DDBE9',
          400: '#26D3E3',
          500: '#00C2D4',
          600: '#00A8B8',
          700: '#008A98',
          800: '#006D78',
          900: '#004F58',
        },
        'off-white': '#F4F7FB',
      },
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        'dm-sans': ['DM Sans', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan-line': 'scanLine 2s ease-in-out infinite',
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.4s ease-out forwards',
      },
      keyframes: {
        scanLine: {
          '0%, 100%': { opacity: '0.3' },
          '50%': { opacity: '1' },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
