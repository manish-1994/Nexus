import React, { useRef, useState } from 'react';
import { motion, HTMLMotionProps, useSpring } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Spring configurations
export const springs = {
  bouncy: { type: 'spring' as const, stiffness: 400, damping: 15 },
  smooth: { type: 'spring' as const, stiffness: 200, damping: 20 },
  gentle: { type: 'spring' as const, stiffness: 100, damping: 20 },
};

export const MotionCard = React.forwardRef<HTMLDivElement, HTMLMotionProps<'div'>>(({ className, children, ...props }, ref) => {
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={springs.smooth}
      whileHover={{ y: -2, scale: 1.01 }}
      className={cn(
        'glass-panel rounded-2xl p-6 transition-colors hover:border-accent-light/30',
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

  const rotateX = useSpring(0, { stiffness: 150, damping: 20 });
  const rotateY = useSpring(0, { stiffness: 150, damping: 20 });

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
          'glass-panel rounded-2xl p-6 transition-all duration-200 hover:shadow-glow hover:border-accent-light/20',
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
      transition={springs.bouncy}
      className={cn(
        'inline-flex items-center justify-center rounded-xl bg-surface border border-white/10 px-4 py-2 text-sm font-medium text-text shadow-sm hover:bg-elevated hover:text-white focus:outline-none focus:ring-2 focus:ring-accent-light focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:pointer-events-none',
        className
      )}
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
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={springs.smooth}
      className={cn('glass-elevated rounded-3xl overflow-hidden', className)}
      {...props}
    >
      {children}
    </motion.div>
  );
});
MotionGlassContainer.displayName = 'MotionGlassContainer';
