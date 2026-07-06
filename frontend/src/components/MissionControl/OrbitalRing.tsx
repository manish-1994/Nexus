import { motion } from 'framer-motion';

interface OrbitalRingProps {
  radius: number;       // px
  rotationSpeed: number; // seconds per full rotation
  color: string;
  opacity?: number;
  clockwise?: boolean;
  children?: React.ReactNode;
}

export function OrbitalRing({
  radius,
  rotationSpeed,
  color,
  opacity = 0.2,
  clockwise = true,
}: OrbitalRingProps) {
  const diameter = radius * 2;

  return (
    <div
      className="absolute rounded-full pointer-events-none"
      style={{
        width: diameter,
        height: diameter,
        left: `calc(50% - ${radius}px)`,
        top: `calc(50% - ${radius}px)`,
        border: `1px solid ${color}`,
        borderStyle: 'dashed',
        opacity,
      }}
    >
      {/* Animated rotation wrapper */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          border: `1px solid transparent`,
          borderTopColor: color,
          borderRightColor: color,
          opacity: opacity * 2,
        }}
        animate={{ rotate: clockwise ? 360 : -360 }}
        transition={{
          duration: rotationSpeed,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      {/* Orbiting dot */}
      <motion.div
        className="absolute w-2 h-2 rounded-full"
        style={{
          background: color,
          boxShadow: `0 0 6px ${color}`,
          top: -4,
          left: 'calc(50% - 4px)',
          transformOrigin: `calc(50% + ${radius}px) calc(50% + ${radius}px)`,
        }}
        animate={{ rotate: clockwise ? 360 : -360 }}
        transition={{
          duration: rotationSpeed * 0.7,
          repeat: Infinity,
          ease: 'linear',
        }}
      />
    </div>
  );
}

// ── Agent Orbit Layout ──
// Positions agents around the core in orbital rings
export interface AgentOrbitPosition {
  role: string;
  angle: number;   // degrees, 0 = top (12 o'clock)
  radius: number;  // px from center
}

const BUILTIN_ORBIT_POSITIONS: AgentOrbitPosition[] = [
  { role: 'planner', angle: 0, radius: 130 },       // top
  { role: 'research', angle: 300, radius: 130 },     // top-left
  { role: 'coder', angle: 240, radius: 130 },        // bottom-left
  { role: 'analyst', angle: 120, radius: 130 },      // bottom-right
  { role: 'memory', angle: 60, radius: 130 },        // top-right
  { role: 'tool', angle: 180, radius: 130 },         // bottom
];

/**
 * Compute absolute pixel positions for agent orbs around a center point.
 * Built-in agents get fixed positions. Custom agents are placed on an outer ring.
 */
export function computeOrbPositions(
  centerX: number,
  centerY: number,
  customRoles: string[],
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();

  // Built-in agents — fixed positions on inner ring
  for (const pos of BUILTIN_ORBIT_POSITIONS) {
    const rad = (pos.angle * Math.PI) / 180;
    positions.set(pos.role, {
      x: centerX + pos.radius * Math.sin(rad),
      y: centerY - pos.radius * Math.cos(rad),
    });
  }

  // Custom agents — evenly distributed on outer ring
  const outerRadius = 190;
  customRoles.forEach((role, i) => {
    const angle = (i * 360) / customRoles.length;
    const rad = (angle * Math.PI) / 180;
    positions.set(role, {
      x: centerX + outerRadius * Math.sin(rad),
      y: centerY - outerRadius * Math.cos(rad),
    });
  });

  return positions;
}