/**
 * NEXUS Design System — Typography Tokens
 * 
 * Font families, sizes, weights, and line heights.
 */

export const typography = {
  // ── Font Families ──
  fontFamily: {
    sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
    heading: ['Orbitron', 'sans-serif'],
    label: ['"Exo 2"', 'sans-serif'],
    mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
  },

  // ── Font Sizes (in rem) ──
  fontSize: {
    /** 10px — status bar, micro labels, badge text */
    micro: '0.625rem',
    /** 12px — metadata, timestamps, captions, helper text */
    xs: '0.75rem',
    /** 14px — body text, input text, list items, buttons */
    sm: '0.875rem',
    /** 16px — default body, card titles, form labels */
    base: '1rem',
    /** 18px — section headings, emphasized body */
    lg: '1.125rem',
    /** 20px — page subheadings, modal titles */
    xl: '1.25rem',
    /** 24px — page titles, hero headings */
    '2xl': '1.5rem',
    /** 30px — major section headers */
    '3xl': '1.875rem',
  },

  // ── Font Weights ──
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // ── Line Heights ──
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },

  // ── Letter Spacing ──
  letterSpacing: {
    tighter: '-0.02em',
    tight: '-0.01em',
    normal: '0',
    wide: '0.02em',
    wider: '0.05em',
  },
} as const;

export type TypographyToken = typeof typography;