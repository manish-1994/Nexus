/**
 * NEXUS Design System — Spacing Tokens
 * 
 * Strict 8px-based spacing system.
 * All spacing must use these values — no arbitrary px values allowed.
 */

export const spacing = {
  /** 8px — tight: icon padding, badge gaps, inline separators */
  xs: 8,
  /** 12px — compact: input padding-x, small card padding, list item gaps */
  sm: 12,
  /** 16px — standard: card padding, section gaps, button padding-x */
  md: 16,
  /** 24px — relaxed: panel padding, form group gaps, sidebar padding */
  lg: 24,
  /** 32px — wide: page section gaps, large container padding */
  xl: 32,
  /** 48px — generous: hero sections, major layout divisions */
  '2xl': 48,
  /** 64px — expansive: page-level margins, max-width containers */
  '3xl': 64,
} as const;

/** Tailwind-compatible spacing scale (px → rem at 16px base) */
export const spacingRem = {
  xs: '0.5rem',   // 8px
  sm: '0.75rem',  // 12px
  md: '1rem',     // 16px
  lg: '1.5rem',   // 24px
  xl: '2rem',     // 32px
  '2xl': '3rem',  // 48px
  '3xl': '4rem',  // 64px
} as const;

export type SpacingToken = typeof spacing;