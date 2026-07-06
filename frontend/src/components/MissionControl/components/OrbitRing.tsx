import { motion } from 'framer-motion';

interface OrbitRingProps {
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  crR: number;
  crG: number;
  crB: number;
  idx: number;
}

export function OrbitRing({ cx, cy, rx, ry, crR, crG, crB, idx }: OrbitRingProps) {
  return (
    <g>
      {/* Dashed faint orbital ring */}
      <ellipse
        cx={cx}
        cy={cy}
        rx={rx}
        ry={ry}
        fill="none"
        stroke={`rgba(${crR},${crG},${crB},${0.18 - idx * 0.04})`}
        strokeWidth={1}
        strokeDasharray={idx === 0 ? "4 6" : "6 8"}
        className="pointer-events-none"
      />
      {/* Slow rotating orbital dot representing system heartbeat */}
      <motion.circle
        cx={cx}
        cy={cy}
        r={2}
        fill={`rgba(${crR},${crG},${crB},0.35)`}
        style={{
          transformOrigin: `${cx}px ${cy}px`,
        }}
        animate={{ rotate: idx % 2 === 0 ? 360 : -360 }}
        transition={{
          duration: 25 + idx * 8,
          repeat: Infinity,
          ease: 'linear'
        }}
      />
    </g>
  );
}
export default OrbitRing;
