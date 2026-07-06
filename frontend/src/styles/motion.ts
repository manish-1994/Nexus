/**
 * NEXUS Design System — Motion Tokens
 * 
 * All animation configurations. Components must use these presets.
 * No ad-hoc springs or durations allowed.
 */

import type { Transition } from 'framer-motion';

// ── Duration Tokens ──
export const durations = {
  /** 80ms — micro-interactions: button tap, toggle, ripple */
  instant: 0.08,
  /** 150ms — quick transitions: hover color, icon rotate, tooltip */
  fast: 0.15,
  /** 220ms — standard: card hover, dropdown toggle, focus ring */
  normal: 0.22,
  /** 300ms — deliberate: page transitions, drawer open, modal */
  slow: 0.30,
  /** 500ms — ambient: background particles, parallax, breathing glow */
  ambient: 0.50,
} as const;

// ── Spring Physics Presets ──
// Typed as Transition to avoid framer-motion Spring type mismatches across versions.
export const springs: Record<string, Transition> = {
  /** Button taps, toggle switches, quick micro-interactions */
  instant: {
    type: 'spring',
    stiffness: 400,
    damping: 25,
    mass: 0.5,
  },
  /** Card entrances, hover lifts, dropdown open/close — DEFAULT for most UI */
  smooth: {
    type: 'spring',
    stiffness: 200,
    damping: 22,
    mass: 0.8,
  },
  /** Page transitions, panel open/close, sidebar */
  gentle: {
    type: 'spring',
    stiffness: 120,
    damping: 18,
    mass: 1,
  },
  /** Ambient effects, floating particles, parallax, background animations */
  slow: {
    type: 'spring',
    stiffness: 60,
    damping: 20,
    mass: 1.2,
  },
} as const;

// ── Transition Presets (non-spring) ──
export const transitions: Record<string, Transition> = {
  fade: { duration: durations.normal, ease: 'easeInOut' },
  fadeFast: { duration: durations.fast, ease: 'easeOut' },
  slideUp: { duration: durations.slow, ease: [0.25, 0.1, 0.25, 1] },
  slideDown: { duration: durations.normal, ease: [0.25, 0.1, 0.25, 1] },
} as const;

// ── Shared Animation Variants ──

/** Page transitions: fade + 20px translate up */
export const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

/** Card entrance: fade + scale 0.98 → 1 */
export const cardEntrance = {
  initial: { opacity: 0, scale: 0.98 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.98 },
};

/** List item stagger */
export const listItem = {
  initial: { opacity: 0, x: -8 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -8 },
};

/** Hover lift: 4px up + subtle scale */
export const hoverLift = {
  whileHover: { y: -4, scale: 1.02, transition: springs.smooth },
};

/** Hover glow: soft blue border glow */
export const hoverGlow = {
  whileHover: {
    boxShadow: '0 0 24px rgba(0,229,255,0.25), 0 4px 20px rgba(0,0,0,0.15)',
    borderColor: 'rgba(0,229,255,0.20)',
    transition: { duration: durations.normal },
  },
};

/** Modal / overlay entrance */
export const overlayEntrance = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

/** Drawer slide-in from right */
export const drawerRight = {
  initial: { x: '100%', opacity: 0 },
  animate: { x: 0, opacity: 1 },
  exit: { x: '100%', opacity: 0 },
};

/** Dropdown / popover entrance */
export const dropdownEntrance = {
  initial: { opacity: 0, scale: 0.95, y: -4 },
  animate: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.95, y: -4 },
};

export type MotionToken = typeof springs;
export type DurationToken = typeof durations;
