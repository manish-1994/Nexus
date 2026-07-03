/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#090B10',
        surface: '#111827',
        elevated: '#182233',
        accent: {
          DEFAULT: '#3b82f6', // Electric Blue
          light: '#60a5fa',
          dark: '#2563eb'
        },
        secondary: {
          DEFAULT: '#a855f7', // Purple
          light: '#c084fc',
          dark: '#9333ea'
        },
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
        text: {
          DEFAULT: '#f9fafb', // Soft white
          muted: '#9ca3af' // Gray
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        heading: ['Orbitron', 'sans-serif'],
        label: ['"Exo 2"', 'sans-serif'],
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.1)',
        'glow': '0 0 15px rgba(59, 130, 246, 0.5)',
      }
    },
  },
  plugins: [],
}
