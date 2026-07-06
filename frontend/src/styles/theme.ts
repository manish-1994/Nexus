/**
 * NEXUS Design System — Theme Configuration
 * 
 * Central theme object for programmatic access to design tokens.
 * Use this for dynamic styling, theme switching, or CSS-in-JS.
 * For Tailwind classes, use tailwind.config.js directly.
 */

import { tokens } from './designTokens';

export const theme = {
  // ── Color Palette ──
  colors: tokens.colors,

  // ── Spacing Scale ──
  spacing: tokens.spacing,

  // ── Typography Scale ──
  typography: tokens.typography,

  // ── Motion Presets ──
  motion: tokens.motion,

  // ── Animation Variants ──
  variants: tokens.variants,

  // ── Border Radius Scale ──
  radius: {
    /** 14px — buttons, badges, small interactive elements */
    button: '0.875rem',
    /** 16px — inputs, textareas, select triggers */
    input: '1rem',
    /** 18px — cards, panels, list items */
    card: '1.125rem',
    /** 22px — panels, sidebars, drawers, topbar */
    panel: '1.375rem',
    /** 24px — dialogs, modals, popovers */
    dialog: '1.5rem',
    /** 22px — chat bubbles (user & assistant) */
    bubble: '1.375rem',
  },

  // ── Glass Presets ──
  glass: {
    surface: {
      background: 'rgba(17,24,39,0.40)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255,255,255,0.05)',
      boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
    },
    elevated: {
      background: 'rgba(22,31,46,0.50)',
      backdropFilter: 'blur(16px)',
      border: '1px solid rgba(255,255,255,0.08)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
    },
    input: {
      background: 'rgba(17,24,39,0.35)',
      backdropFilter: 'blur(8px)',
      border: '1px solid rgba(255,255,255,0.08)',
    },
  },

  // ── Shadow Presets ──
  shadows: {
    /** Default soft shadow for cards */
    soft: '0 4px 24px rgba(0,0,0,0.12)',
    /** Hover glow — soft blue */
    glow: '0 0 24px rgba(0,229,255,0.25), 0 4px 20px rgba(0,0,0,0.15)',
    /** Elevated shadow for modals/drawers */
    elevated: '0 16px 48px rgba(0,0,0,0.25)',
    /** Subtle shadow for dropdowns */
    subtle: '0 2px 12px rgba(0,0,0,0.10)',
  },
} as const;

export type Theme = typeof theme;