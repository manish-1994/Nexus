import { motion } from 'framer-motion';
import type { GraphNode } from '../graph/graphModel';

interface JunctionProps {
  node: GraphNode;
  crR: number;
  crG: number;
  crB: number;
}

export function Junction({ node, crR, crG, crB }: JunctionProps) {
  return (
    <g key={node.id}>
      <motion.circle
        cx={node.position.x}
        cy={node.position.y}
        r={6}
        fill="none"
        stroke={`rgba(${crR},${crG},${crB},0.35)`}
        strokeWidth={1.2}
        animate={{ scale: [0.85, 1.35, 0.85], opacity: [0.3, 0.75, 0.3] }}
        transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut", delay: node.angle * 0.05 }}
      />
      <circle
        cx={node.position.x}
        cy={node.position.y}
        r={3.5}
        fill={`rgba(${crR},${crG},${crB},0.95)`}
        stroke="#FFFFFF"
        strokeWidth={1.0}
      />
    </g>
  );
}
