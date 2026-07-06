/**
 * NEXUS Design System — Color Tokens
 * 
 * Single source of truth for all color values.
 * Import from this file; never hardcode hex values in components.
 */

export const colors = {
  // ── Core Backgrounds ──
  background: {
    DEFAULT: '#090D16',
    deep: '#060B14',
  },

  // ── Surface Layers ──
  surface: {
    DEFAULT: '#111827',
    elevated: '#161F2E',
    overlay: '#1A2332',
  },

  // ── Brand ──
  brand: {
    primary: '#3B82F6',
    accent: '#00E5FF',
  },

  // ── Semantic ──
  semantic: {
    success: '#00FF95',
    warning: '#F59E0B',
    danger: '#FF4D67',
    info: '#00E5FF',
  },

  // ── Text ──
  text: {
    primary: '#F5F7FA',
    secondary: '#94A3B8',
    muted: '#64748B',
    inverse: '#111827',
  },

  // ── Border ──
  border: {
    DEFAULT: 'rgba(255,255,255,0.05)',
    subtle: 'rgba(255,255,255,0.03)',
    strong: 'rgba(255,255,255,0.10)',
    glow: 'rgba(0,229,255,0.15)',
  },

  // ── Glass Opacity Overrides ──
  glass: {
    surface: 'rgba(17,24,39,0.40)',
    elevated: 'rgba(22,31,46,0.50)',
    subtle: 'rgba(17,24,39,0.20)',
    input: 'rgba(17,24,39,0.35)',
  },

  // ── Effect Colors ──
  effect: {
    glow: {
      accent: 'rgba(0,229,255,0.40)',
      primary: 'rgba(59,130,246,0.35)',
      success: 'rgba(0,255,149,0.30)',
      danger: 'rgba(255,77,103,0.30)',
    },
    shimmer: {
      base: 'rgba(255,255,255,0.03)',
      peak: 'rgba(255,255,255,0.08)',
    },
  },
} as const;

export type ColorToken = typeof colors;