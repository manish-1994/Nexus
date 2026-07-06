/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // ── NEXUS Color Palette ──
      colors: {
        background: {
          DEFAULT: '#090D16',
          deep: '#060B14',
        },
        surface: {
          DEFAULT: '#111827',
          elevated: '#161F2E',
          overlay: '#1A2332',
        },
        accent: {
          DEFAULT: '#00E5FF',   // Cyan — primary accent
          light: '#33EAFF',
          dark: '#00B8D4',
        },
        primary: {
          DEFAULT: '#3B82F6',   // Blue — secondary brand
          light: '#60A5FA',
          dark: '#2563EB',
        },
        success: '#00FF95',
        warning: '#F59E0B',
        danger: '#FF4D67',
        text: {
          DEFAULT: '#F5F7FA',   // Primary text
          secondary: '#94A3B8', // Secondary text
          muted: '#64748B',     // Muted / metadata
          inverse: '#111827',   // Text on light backgrounds
        },
        border: {
          DEFAULT: 'rgba(255,255,255,0.05)',
          subtle: 'rgba(255,255,255,0.03)',
          strong: 'rgba(255,255,255,0.10)',
          glow: 'rgba(0,229,255,0.15)',
        },
      },

      // ── Font Families ──
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        heading: ['Orbitron', 'sans-serif'],
        label: ['"Exo 2"', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },

      // ── Border Radius Scale ──
      borderRadius: {
        'button': '0.875rem',   // 14px
        'input': '1rem',        // 16px
        'card': '1.125rem',     // 18px
        'panel': '1.375rem',    // 22px
        'dialog': '1.5rem',     // 24px
        'bubble': '1.375rem',   // 22px
      },

      // ── Layered Shadows ──
      boxShadow: {
        'soft': '0 4px 24px rgba(0, 0, 0, 0.12)',
        'glow': '0 0 24px rgba(0, 229, 255, 0.25), 0 4px 20px rgba(0, 0, 0, 0.15)',
        'glow-sm': '0 0 12px rgba(0, 229, 255, 0.20), 0 2px 8px rgba(0, 0, 0, 0.10)',
        'glow-lg': '0 0 40px rgba(0, 229, 255, 0.30), 0 8px 32px rgba(0, 0, 0, 0.20)',
        'elevated': '0 16px 48px rgba(0, 0, 0, 0.25)',
        'subtle': '0 2px 12px rgba(0, 0, 0, 0.10)',
      },

      // ── Transition Durations ──
      transitionDuration: {
        'instant': '80ms',
        'fast': '150ms',
        'normal': '220ms',
        'slow': '300ms',
        'ambient': '500ms',
      },

      // ── Custom Spacing (8px grid) ──
      spacing: {
        'xs': '0.5rem',   // 8px
        'sm': '0.75rem',  // 12px
        'md': '1rem',     // 16px
        'lg': '1.5rem',   // 24px
        'xl': '2rem',     // 32px
        '2xl': '3rem',    // 48px
        '3xl': '4rem',    // 64px
      },
    },
  },
  plugins: [],
}