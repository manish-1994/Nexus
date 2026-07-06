import { motion } from 'framer-motion';
import type { Point } from '../graph/graphModel';
import { resolveAnchor } from '../graph/anchorResolver';

interface ExecutionPathProps {
  fromPos: Point; // Core position
  toPos: Point;   // Agent position
  role: string;
  brR: number;
  brG: number;
  brB: number;
}

export function ExecutionPath({ fromPos, toPos, role, brR, brG, brB }: ExecutionPathProps) {
  // Resolve the visual plug socket position on the border of the card
  const { position: anchorPos } = resolveAnchor(toPos, fromPos);


  const dx = toPos.x - fromPos.x;
  const dy = toPos.y - fromPos.y;
  const dist = Math.hypot(dx, dy);

  // Perpendicular unit vector (rotate 90°) for organic curvature
  const perpX = dist > 0 ? -dy / dist : 0;
  const perpY = dist > 0 ?  dx / dist : 0;

  // Bow the curve slightly outward to look like a clean solar flare
  const r = role.toLowerCase();
  const bowDir = (r === 'analyst' || r === 'planner' || r === 'research') ? -1 : 1;
  const bow = Math.min(dist * 0.22, 45) * bowDir;
  
  const qcx = (fromPos.x + toPos.x) / 2 + perpX * bow;
  const qcy = (fromPos.y + toPos.y) / 2 + perpY * bow;

  // Path terminates at the card center (toPos.x/y) so it is hidden behind the card.
  // The anchor socket is rendered at the border (anchorPos.x/y) to look plugged in.
  const pathD = `M ${fromPos.x} ${fromPos.y} Q ${qcx} ${qcy} ${toPos.x} ${toPos.y}`;
  const anchorR = 5.5;

  return (
    <g>
      {/* ── Glowing Conduit Line ── */}
      <path d={pathD} stroke={`rgba(${brR},${brG},${brB},0.15)`} strokeWidth={12} fill="none" strokeLinecap="round" />
      <path d={pathD} stroke={`rgba(${brR},${brG},${brB},0.48)`} strokeWidth={4} fill="none" strokeLinecap="round" />
      <path d={pathD} stroke="#FFFFFF" strokeWidth={1.5} fill="none" strokeLinecap="round" />

      {/* ── Active connection socket ring at card boundary ── */}
      <motion.circle
        cx={anchorPos.x} cy={anchorPos.y} r={anchorR + 6} fill="none"
        stroke={`rgba(${brR},${brG},${brB},0.75)`} strokeWidth={1.5}
        animate={{ scale: [0.9, 1.5, 0.9], opacity: [0.3, 0.9, 0.3] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
      />
      <circle cx={anchorPos.x} cy={anchorPos.y} r={anchorR + 2} fill={`rgba(${brR},${brG},${brB},0.22)`} />
      <circle cx={anchorPos.x} cy={anchorPos.y} r={anchorR} fill="#020614" stroke={`rgba(${brR},${brG},${brB},0.95)`} strokeWidth={1.5} />
      <circle cx={anchorPos.x} cy={anchorPos.y} r={anchorR * 0.45} fill={`rgba(${brR},${brG},${brB},1.0)`} />

      {/* ── Energy pulse flowing Core -> Agent -> Core ── */}
      <motion.path
        d={pathD} stroke="#FFFFFF" strokeWidth={2.2} fill="none" strokeLinecap="round" strokeDasharray="30 150"
        animate={{ strokeDashoffset: [0, -180] }}
        transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
      />
      <motion.path
        d={pathD} stroke={`rgba(${brR},${brG},${brB},0.8)`} strokeWidth={1.5} fill="none" strokeLinecap="round" strokeDasharray="10 60"
        animate={{ strokeDashoffset: [0, -140] }}
        transition={{ duration: 0.9, repeat: Infinity, ease: "linear", delay: 0.2 }}
      />
    </g>
  );
}
export default ExecutionPath;
