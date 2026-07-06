import { motion } from 'framer-motion';
import type { GraphNode, GraphEdge } from '../graph/graphModel';
import { routeEdge } from '../graph/graphRouter';

interface NeuralEdgeProps {
  edge: GraphEdge;
  fromNode: GraphNode;
  toNode: GraphNode;
  isAgentActive: boolean;
  activeAlpha: number;
  brR: number;
  brG: number;
  brB: number;
  idx: number;
  // Full path context for pulses
  cx: number;
  cy: number;
  shiftX: number;
  shiftY: number;
  j1?: GraphNode;
  j2?: GraphNode;
  j3?: GraphNode;
  clusterName: string;
  isAgentActiveAny: boolean;
}

export function NeuralEdge({
  edge,
  fromNode,
  toNode,
  isAgentActive,
  activeAlpha,
  brR,
  brG,
  brB,
  idx,
  cx,
  cy,
  shiftX,
  shiftY,
  j1,
  j2,
  j3,
  clusterName,
  isAgentActiveAny
}: NeuralEdgeProps) {
  const isAgent = edge.type === 'branch';

  // Compute curve with role-based routing
  const route = routeEdge(fromNode.position, toNode.position, isAgent, toNode.role);

  // Build full trunk path for energy flow
  let trunkD = '';
  if (isAgent && j1) {
    // If it's a bottom step branch, just use the custom routed path directly
    if (['browser', 'tool', 'voice', 'workflow'].includes(toNode.role || '')) {
      trunkD = route.pathD;
    } else {
      const qPart = route.pathD.slice(route.pathD.indexOf('Q'));
      const sign = clusterName === 'Knowledge' ? -1 : 1;
      const cX12 = j2 ? (j1.position.x + j2.position.x) / 2 + 15 * Math.sin(sign * 3.1) : 0;
      const cY12 = j2 ? (j1.position.y + j2.position.y) / 2 + 15 * Math.cos(sign * 3.1) : 0;

    const cX23 = (j2 && j3) ? (j2.position.x + j3.position.x) / 2 - 15 * Math.sin(sign * 3.1) : 0;
    const cY23 = (j2 && j3) ? (j2.position.y + j3.position.y) / 2 - 15 * Math.cos(sign * 3.1) : 0;

    trunkD = toNode.ring === 'inner'
      ? `M ${cx + shiftX} ${cy + shiftY} L ${j1.position.x} ${j1.position.y} ${qPart}`
      : toNode.ring === 'middle' && j2
        ? `M ${cx + shiftX} ${cy + shiftY} L ${j1.position.x} ${j1.position.y} Q ${cX12} ${cY12} ${j2.position.x} ${j2.position.y} ${qPart}`
        : (j2 && j3)
          ? `M ${cx + shiftX} ${cy + shiftY} L ${j1.position.x} ${j1.position.y} Q ${cX12} ${cY12} ${j2.position.x} ${j2.position.y} Q ${cX23} ${cY23} ${j3.position.x} ${j3.position.y} ${qPart}`
          : route.pathD;
    }
  } else {
    trunkD = route.pathD;
  }


  const anchorR = 5.5;

  return (
    <g>
      {/* Glow bloom */}
      <path d={route.pathD} stroke={`rgba(${brR},${brG},${brB},${activeAlpha * 0.10})`} strokeWidth={isAgentActive ? 12 : 4} fill="none" strokeLinecap="round" />
      {/* Mid glow */}
      <path d={route.pathD} stroke={`rgba(${brR},${brG},${brB},${activeAlpha * 0.38})`} strokeWidth={isAgentActive ? 5 : 1.8} fill="none" strokeLinecap="round" />
      {/* Core line */}
      <path d={route.pathD} stroke={`rgba(${brR},${brG},${brB},${activeAlpha})`} strokeWidth={isAgentActive ? 2.2 : 1.1} fill="none" strokeLinecap="round" />
      {/* Inner white core */}
      <path d={route.pathD} stroke="rgba(255,255,255,0.85)" strokeWidth={isAgentActive ? 0.7 : 0.5} fill="none" strokeLinecap="round" />

      {/* Render anchor socket at the card boundary plug point */}
      {isAgent && (
        <g>
          <motion.circle
            cx={route.anchorX} cy={route.anchorY} r={anchorR + 4} fill="none"
            stroke={`rgba(${brR},${brG},${brB},${activeAlpha * 0.45})`} strokeWidth={1.5}
            animate={{ scale: [0.8, 1.4, 0.8], opacity: [0.2, 0.7, 0.2] }}
            transition={{ duration: 2.0, repeat: Infinity, ease: 'easeInOut', delay: idx * 0.15 }}
          />
          <circle cx={route.anchorX} cy={route.anchorY} r={anchorR + 2} fill={`rgba(${brR},${brG},${brB},${activeAlpha * 0.18})`} />
          <circle cx={route.anchorX} cy={route.anchorY} r={anchorR} fill="#020614" stroke={`rgba(${brR},${brG},${brB},${activeAlpha * 0.9})`} strokeWidth={1.4} />
          <circle cx={route.anchorX} cy={route.anchorY} r={anchorR * 0.38} fill={`rgba(${brR},${brG},${brB},${activeAlpha})`} />
        </g>
      )}

      {/* Active trace energy pulse */}
      {(isAgentActive || !isAgentActiveAny) && (
        <motion.path
          d={trunkD} stroke="#00E5FF" strokeWidth={2.0} fill="none" strokeLinecap="round" strokeDasharray="25 150"
          animate={{ strokeDashoffset: [0, -175] }}
          transition={{ duration: isAgentActive ? 1.4 : 3.5, repeat: Infinity, ease: "linear", delay: idx * 0.35 }}
        />
      )}

      {/* Particle Trails */}
      <motion.path
        d={trunkD} stroke="#FFFFFF" strokeWidth={0.8} fill="none" strokeLinecap="round" strokeDasharray="1.5 25"
        animate={{ strokeDashoffset: [0, -220] }}
        transition={{ duration: isAgentActive ? 2.0 : 4.2, repeat: Infinity, ease: "linear", delay: idx * 0.2 }}
      />
      <motion.path
        d={trunkD} stroke="#00E5FF" strokeWidth={0.6} fill="none" strokeLinecap="round" strokeDasharray="1 12"
        animate={{ strokeDashoffset: [0, -130] }}
        transition={{ duration: isAgentActive ? 1.1 : 2.6, repeat: Infinity, ease: "linear", delay: idx * 0.1 }}
      />
    </g>
  );
}
