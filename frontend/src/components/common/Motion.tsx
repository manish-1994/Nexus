import React, { useRef, useState } from 'react';
import { motion, HTMLMotionProps, useSpring } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ── Unified Spring Configurations ──
// All components MUST use these presets. No ad-hoc springs allowed.
export const springs = {
  /** Button taps, toggle switches, quick micro-interactions */
  instant: { type: 'spring' as const, stiffness: 400, damping: 25, mass: 0.5 },
  /** Card entrances, hover lifts, dropdown open/close — DEFAULT for most UI */
  smooth: { type: 'spring' as const, stiffness: 200, damping: 22, mass: 0.8 },
  /** Page transitions, panel open/close, sidebar */
  gentle: { type: 'spring' as const, stiffness: 120, damping: 18, mass: 1 },
  /** Ambient effects, floating particles, parallax, background animations */
  slow: { type: 'spring' as const, stiffness: 60, damping: 20, mass: 1.2 },
};

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
    transition: { duration: 0.22 },
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

// ── Motion Components ──

export const MotionCard = React.forwardRef<HTMLDivElement, HTMLMotionProps<'div'>>(({ className, children, ...props }, ref) => {
  return (
    <motion.div
      ref={ref}
      initial={cardEntrance.initial}
      animate={cardEntrance.animate}
      exit={cardEntrance.exit}
      transition={springs.smooth}
      whileHover={{ y: -4, scale: 1.02, transition: springs.smooth }}
      className={cn(
        'glass-surface rounded-card p-md transition-colors duration-normal hover:border-accent/20 hover:shadow-glow',
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
});
MotionCard.displayName = 'MotionCard';

export const InteractiveCard3D = React.forwardRef<HTMLDivElement, HTMLMotionProps<'div'>>(({ className, children, ...props }, ref) => {
  const localRef = useRef<HTMLDivElement>(null);
  const resolvedRef = (ref as React.RefObject<HTMLDivElement>) || localRef;

  const [hovering, setHovering] = useState(false);

  const rotateX = useSpring(0, springs.smooth);
  const rotateY = useSpring(0, springs.smooth);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!resolvedRef.current) return;
    const rect = resolvedRef.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left - width / 2;
    const mouseY = e.clientY - rect.top - height / 2;

    const rX = -(mouseY / (height / 2)) * 10;
    const rY = (mouseX / (width / 2)) * 10;

    rotateX.set(rX);
    rotateY.set(rY);
  };

  const handleMouseLeave = () => {
    setHovering(false);
    rotateX.set(0);
    rotateY.set(0);
  };

  return (
    <div style={{ perspective: '1000px' }}>
      <motion.div
        ref={resolvedRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={handleMouseLeave}
        style={{
          rotateX,
          rotateY,
          transformStyle: 'preserve-3d',
        }}
        animate={hovering ? {
          scale: 1.02,
          z: 30,
        } : {
          scale: 1,
          z: 0,
          y: [0, -4, 0],
          transition: {
            y: { repeat: Infinity, duration: 6, ease: "easeInOut" }
          }
        }}
        className={cn(
          'glass-surface rounded-card p-md transition-all duration-normal hover:shadow-glow hover:border-accent/20',
          className
        )}
        {...props}
      >
        <div style={{ transform: 'translateZ(20px)', transformStyle: 'preserve-3d' }}>
          {children as React.ReactNode}
        </div>
      </motion.div>
    </div>
  );
});
InteractiveCard3D.displayName = 'InteractiveCard3D';

export const MotionButton = React.forwardRef<HTMLButtonElement, HTMLMotionProps<'button'>>(({ className, children, ...props }, ref) => {
  return (
    <motion.button
      ref={ref}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={springs.instant}
      className={cn(
        'inline-flex items-center justify-center rounded-button bg-surface border px-md py-sm text-sm font-medium text-text shadow-subtle hover:bg-surface-elevated hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:pointer-events-none transition-all duration-normal',
        className
      )}
      style={{ borderColor: 'rgba(255,255,255,0.08)', ...props.style }}
      {...props}
    >
      {children}
    </motion.button>
  );
});
MotionButton.displayName = 'MotionButton';

export const MotionGlassContainer = React.forwardRef<HTMLDivElement, HTMLMotionProps<'div'>>(({ className, children, ...props }, ref) => {
  return (
    <motion.div
      ref={ref}
      initial={cardEntrance.initial}
      animate={cardEntrance.animate}
      exit={cardEntrance.exit}
      transition={springs.smooth}
      className={cn('glass-elevated rounded-panel overflow-hidden', className)}
      {...props}
    >
      {children}
    </motion.div>
  );
});
MotionGlassContainer.displayName = 'MotionGlassContainer';
