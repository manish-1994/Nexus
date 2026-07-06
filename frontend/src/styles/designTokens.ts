/**
 * NEXUS Design System — Unified Design Tokens
 * 
 * Aggregates all token categories into a single export.
 * Import { tokens } from 'styles/designTokens' for all-in-one access.
 */

import { colors } from './colors';
import { spacing, spacingRem } from './spacing';
import { typography } from './typography';
import { springs, durations, transitions, pageTransition, cardEntrance, listItem, hoverLift, hoverGlow, overlayEntrance, drawerRight, dropdownEntrance } from './motion';

export const tokens = {
  colors,
  spacing,
  spacingRem,
  typography,
  motion: {
    springs,
    durations,
    transitions,
  },
  variants: {
    pageTransition,
    cardEntrance,
    listItem,
    hoverLift,
    hoverGlow,
    overlayEntrance,
    drawerRight,
    dropdownEntrance,
  },
} as const;

// ── Individual re-exports for tree-shaking ──
export { colors } from './colors';
export { spacing, spacingRem } from './spacing';
export { typography } from './typography';
export {
  springs,
  durations,
  transitions,
  pageTransition,
  cardEntrance,
  listItem,
  hoverLift,
  hoverGlow,
  overlayEntrance,
  drawerRight,
  dropdownEntrance,
} from './motion';

export type DesignTokens = typeof tokens;