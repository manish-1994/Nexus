# NEXUS Unified Design Token System — Phase 1 Plan

## Overview

This document defines the unified design token system that will replace the current ad-hoc styling across the NEXUS frontend. All tokens are designed for the **dark glassmorphism theme** (background `#090B10`).

---

## 1. Border Radius Tokens

Replace all ad-hoc `rounded-lg`, `rounded-xl`, `rounded-2xl`, `rounded-3xl`, `rounded-md` with a 3-tier system:

| Token | Value | Usage |
|---|---|---|
| `radius-sm` | `0.5rem` (8px) | Buttons, inputs, badges, small interactive elements |
| `radius-md` | `0.75rem` (12px) | Cards, panels, dropdowns, modals — **PRIMARY card radius** |
| `radius-lg` | `1rem` (16px) | Large containers: main content area, sidebar, topbar |

**Tailwind config addition:**
```js
borderRadius: {
  'sm': '0.5rem',   // rounded-sm → 8px
  'md': '0.75rem',  // rounded-md → 12px (DEFAULT for cards)
  'lg': '1rem',     // rounded-lg → 16px
}
```

**Migration mapping:**
- `rounded-lg` → `rounded-md` (cards, panels)
- `rounded-xl` → `rounded-md` (buttons, inputs, dropdowns)
- `rounded-2xl` → `rounded-lg` (large containers)
- `rounded-3xl` → `rounded-lg` (large containers)
- `rounded-md` → `rounded-sm` (small elements)
- `rounded-full` → stays (badges, pills)

---

## 2. Glass Effect Presets

Replace 5+ ad-hoc glass recipes with 3 standardized presets:

| Token | Background | Blur | Border | Shadow | Usage |
|---|---|---|---|---|
| `glass-surface` | `bg-surface/40` | `backdrop-blur-md` | `border-white/5` | `shadow-glass` | Cards, panels, dropdowns |
| `glass-elevated` | `bg-elevated/50` | `backdrop-blur-lg` | `border-white/10` | `shadow-glass` | Modals, drawers, spotlight |
| `glass-subtle` | `bg-surface/20` | `backdrop-blur-sm` | `border-white/[0.03]` | none | Background regions, section dividers |

**CSS component classes (in index.css):**
```css
.glass-surface {
  @apply bg-surface/40 backdrop-blur-md border border-white/5 shadow-glass;
}
.glass-elevated {
  @apply bg-elevated/50 backdrop-blur-lg border border-white/10 shadow-glass;
}
.glass-subtle {
  @apply bg-surface/20 backdrop-blur-sm border border-white/[0.03];
}
```

**Migration:**
- Current `glass-panel` → `glass-surface` (rename for clarity)
- Current `glass-elevated` → stays (but updated to match new spec)
- `bg-surface/30` ad-hoc → `glass-surface`
- `bg-elevated/40` ad-hoc → `glass-surface` or `glass-elevated` depending on context
- `bg-surface/50` ad-hoc → `glass-elevated`

---

## 3. Spacing System (8px Base)

Replace ad-hoc `p-3`, `p-4`, `p-5`, `p-6`, `p-8` with a consistent 8px scale:

| Token | Value | Tailwind Class | Usage |
|---|---|---|---|
| `space-xs` | 8px | `p-2` / `gap-2` | Compact: badges, button groups, icon spacing |
| `space-sm` | 16px | `p-4` / `gap-4` | Standard: card padding, section gaps |
| `space-md` | 24px | `p-6` / `gap-6` | Comfortable: page sections, card grids |
| `space-lg` | 32px | `p-8` / `gap-8` | Generous: main content padding, hero sections |

**Standardization rules:**
- **Card internal padding**: always `p-4` (16px)
- **Page section gaps**: always `gap-6` (24px)
- **Main content area padding**: `p-6` (24px) — reduced from current `p-8`
- **Grid gaps**: `gap-4` (16px) for card grids
- **Form field gaps**: `gap-4` (16px)

---

## 4. Shadow Variants

Replace 2 shadow definitions with a 5-tier system:

| Token | Value | Usage |
|---|---|---|
| `shadow-glass` | `0 4px 30px rgba(0, 0, 0, 0.1)` | Default card/panel shadow (keep existing) |
| `shadow-glow-sm` | `0 0 10px rgba(59, 130, 246, 0.3)` | Subtle glow: hover states, active indicators |
| `shadow-glow` | `0 0 20px rgba(59, 130, 246, 0.4)` | Standard glow: buttons, selected cards (keep existing, rename) |
| `shadow-glow-lg` | `0 0 40px rgba(59, 130, 246, 0.5)` | Strong glow: spotlight, modals |
| `shadow-glow-secondary` | `0 0 20px rgba(168, 85, 247, 0.4)` | Purple glow: secondary elements |

**Tailwind config:**
```js
boxShadow: {
  'glass': '0 4px 30px rgba(0, 0, 0, 0.1)',
  'glow-sm': '0 0 10px rgba(59, 130, 246, 0.3)',
  'glow': '0 0 20px rgba(59, 130, 246, 0.4)',
  'glow-lg': '0 0 40px rgba(59, 130, 246, 0.5)',
  'glow-secondary': '0 0 20px rgba(168, 85, 247, 0.4)',
}
```

---

## 5. Spring Animation Tokens

Replace 6+ ad-hoc spring configs with 4 standardized presets in [`Motion.tsx`](frontend/src/components/common/Motion.tsx):

| Token | Stiffness | Damping | Usage |
|---|---|---|---|
| `springs.instant` | 400 | 25 | Button taps, toggle switches, quick micro-interactions |
| `springs.smooth` | 200 | 20 | Card entrances, page transitions, hover lifts |
| `springs.gentle` | 100 | 20 | Large panels, sidebar, background animations |
| `springs.slow` | 60 | 20 | Ambient effects, floating particles, parallax |

**Migration:**
- Layout Sidebar: `stiffness:300/damping:30` → `springs.gentle` (100/20)
- AmbientBackground mouse glow: `damping:50/stiffness:200` → `springs.slow` (60/20)
- InteractiveCard3D tilt: `stiffness:150/damping:20` → `springs.smooth` (200/20)
- Dashboard telemetry bars: inline springs → `springs.smooth`
- MessageBubble entrance: inline springs → `springs.smooth`
- MotionButton: `springs.bouncy` (400/15) → `springs.instant` (400/25)

---

## 6. Animation Duration Tokens

Standardize CSS transition durations:

| Token | Value | Usage |
|---|---|---|
| `duration-fast` | 150ms | Micro-interactions: hover color changes, icon swaps |
| `duration-normal` | 200ms | Standard transitions: card hover, button states |
| `duration-slow` | 300ms | Deliberate transitions: page changes, panel open/close |
| `duration-ambient` | 6000ms+ | Background animations: aurora, floating lights |

**Tailwind config:**
```js
transitionDuration: {
  'fast': '150ms',
  'normal': '200ms',
  'slow': '300ms',
}
```

---

## 7. Typography Scale

Standardize text sizes for the dark theme:

| Token | Size | Line Height | Usage |
|---|---|---|---|
| `text-caption` | 10px | 1.4 | Status bar, timestamps, micro-labels |
| `text-label` | 11px | 1.4 | Badges, button labels, HUD labels |
| `text-xs` | 12px | 1.5 | Secondary text, descriptions, metadata |
| `text-sm` | 14px | 1.5 | Body text, form labels, list items |
| `text-base` | 16px | 1.6 | Primary content, card titles |
| `text-lg` | 18px | 1.6 | Section headers |
| `text-xl` | 20px | 1.4 | Page titles (with tracking-wider uppercase) |
| `text-2xl` | 24px | 1.3 | Major page headings |
| `text-3xl` | 30px | 1.2 | Hero headings |

---

## 8. Input/Form Standardization

All inputs must follow this pattern for visibility:

```css
/* Standard input */
.input-standard {
  @apply bg-surface/40 text-text placeholder-text-muted/70 
         border border-white/10 rounded-sm
         px-3 py-2 text-sm
         focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent/40
         caret-accent selection:bg-accent/30
         disabled:opacity-40 disabled:cursor-not-allowed
         transition-all duration-fast;
}
```

**Key changes:**
- Placeholder opacity: **70%** minimum (up from 40%/50%) — ensures WCAG AA contrast
- Border: always `border-white/10` (not `border-gray-300`)
- Focus ring: `ring-accent/30` with `border-accent/40`
- Background: always `bg-surface/40` (not `bg-white` or `bg-transparent`)

---

## 9. Badge/Pill Standardization

All badges must use dark-theme-appropriate colors:

| Type | Background | Text | Border |
|---|---|---|---|
| Success/Active | `bg-success/15` | `text-success` | `border-success/30` |
| Warning/Pending | `bg-warning/15` | `text-warning` | `border-warning/30` |
| Danger/Error | `bg-danger/15` | `text-danger` | `border-danger/30` |
| Info/Accent | `bg-accent/15` | `text-accent-light` | `border-accent/30` |
| Secondary | `bg-secondary/15` | `text-secondary-light` | `border-secondary/30` |
| Neutral/Muted | `bg-white/5` | `text-text-muted` | `border-white/10` |

**Migration from light theme badges:**
- `bg-green-100 text-green-800` → `bg-success/15 text-success border-success/30`
- `bg-red-100 text-red-800` → `bg-danger/15 text-danger border-danger/30`
- `bg-yellow-100 text-yellow-800` → `bg-warning/15 text-warning border-warning/30`
- `bg-blue-100 text-blue-800` → `bg-accent/15 text-accent-light border-accent/30`
- `bg-gray-100 text-gray-800` → `bg-white/5 text-text-muted border-white/10`
- `bg-purple-100 text-purple-800` → `bg-secondary/15 text-secondary-light border-secondary/30`

---

## 10. Color Token Additions

Add missing semantic tokens to tailwind config:

```js
colors: {
  // ... existing tokens ...
  text: {
    DEFAULT: '#f9fafb',
    muted: '#9ca3af',
    dim: '#6b7280',        // NEW: for very subtle text (timestamps, metadata)
    inverse: '#111827',    // NEW: for text on light backgrounds (rare)
  },
  border: {
    DEFAULT: 'rgba(255,255,255,0.05)',   // NEW: standard border
    subtle: 'rgba(255,255,255,0.03)',    // NEW: very subtle border
    strong: 'rgba(255,255,255,0.10)',    // NEW: emphasized border
  },
}
```

---

## Implementation Order

1. **Update `tailwind.config.js`** — add all new tokens (radii, shadows, durations, colors)
2. **Update `index.css`** — add new glass component classes, input-standard class, reduced-motion media query
3. **Update `Motion.tsx`** — standardize spring presets, update component defaults to use new tokens
4. **Verify build** — ensure no Tailwind compilation errors

---

## Files Modified in Phase 1

| File | Changes |
|---|---|
| [`tailwind.config.js`](frontend/tailwind.config.js) | Add borderRadius, boxShadow variants, transitionDuration, text.dim, text.inverse, border.* tokens |
| [`index.css`](frontend/src/assets/index.css) | Add `.glass-surface`, `.glass-subtle`, `.input-standard`, `@media (prefers-reduced-motion)` |
| [`Motion.tsx`](frontend/src/components/common/Motion.tsx) | Standardize springs (4 presets), update component class defaults |