import { motion } from 'framer-motion';

interface HubNodeProps {
  id: string;
  name: string;
  x: number;
  y: number;
  crR: number;
  crG: number;
  crB: number;
}

export function HubNode({ id, name, x, y, crR, crG, crB }: HubNodeProps) {
  return (
    <g key={id}>
      {/* Glowing outer hub ring */}
      <motion.circle
        cx={x}
        cy={y}
        r={22}
        fill="none"
        stroke={`rgba(${crR},${crG},${crB},0.15)`}
        strokeWidth={2}
        animate={{ scale: [0.95, 1.1, 0.95] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
      />
      <circle
        cx={x}
        cy={y}
        r={18}
        fill="#020614"
        stroke={`rgba(${crR},${crG},${crB},0.8)`}
        strokeWidth={1.5}
      />
      {/* Text label centered on the hub */}
      <text
        x={x}
        y={y + 3}
        textAnchor="middle"
        fill="#FFFFFF"
        fontSize="6.5px"
        fontFamily="monospace"
        fontWeight="bold"
        letterSpacing="0.1em"
        className="uppercase pointer-events-none select-none"
      >
        {name}
      </text>
    </g>
  );
}
