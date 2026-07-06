import type { Point } from './graphModel';
import { resolveAnchor } from './anchorResolver';

export interface RouteResult {
  pathD: string;
  anchorX: number;
  anchorY: number;
  anchorDirection: 'top' | 'right' | 'bottom' | 'left';
}

/**
 * Custom routing engine that generates clean, S-curve-free paths.
 * Generates straight lines for horizontal pathways and step-bends for bottom row modules.
 */
export function routeEdge(
  fromPos: Point,
  toPos: Point,
  toIsAgent: boolean,
  role?: string
): RouteResult {
  const { direction, position: anchorPos } = resolveAnchor(toPos, fromPos);

  if (!toIsAgent) {
    // Normal trunk - simple curve
    const qcx = (fromPos.x + toPos.x) / 2;
    const qcy = (fromPos.y + toPos.y) / 2;
    return {
      pathD: `M ${fromPos.x} ${fromPos.y} Q ${qcx} ${qcy} ${toPos.x} ${toPos.y}`,
      anchorX: toPos.x,
      anchorY: toPos.y,
      anchorDirection: 'left'
    };
  }

  const r = role ? role.toLowerCase() : '';

  // Bottom row step-routing (Browser, Tool, Voice, Workflow)
  if (['browser', 'tool', 'voice', 'workflow'].includes(r)) {
    // Draw vertical step down from the bottom-distributor junction, horizontal run, then vertical down to card top anchor
    const midY = (fromPos.y + anchorPos.y) / 2 - 10;
    const pathD = `M ${fromPos.x} ${fromPos.y} L ${fromPos.x} ${midY} L ${anchorPos.x} ${midY} L ${toPos.x} ${toPos.y}`;
    return {
      pathD,
      anchorX: anchorPos.x,
      anchorY: anchorPos.y,
      anchorDirection: 'top'
    };
  }

  // Exact horizontal straight line connections for Vision and Automation
  if (['vision', 'automation'].includes(r)) {
    const pathD = `M ${fromPos.x} ${fromPos.y} L ${toPos.x} ${toPos.y}`;
    return {
      pathD,
      anchorX: anchorPos.x,
      anchorY: anchorPos.y,
      anchorDirection: direction
    };
  }

  // For diagonal agents, use a clean bowed quadratic curve to card center (with 25px offset check to prevent S-curves)
  const dx = toPos.x - fromPos.x;
  const dy = toPos.y - fromPos.y;
  const dist = Math.hypot(dx, dy);

  const perpX = dist > 0 ? -dy / dist : 0;
  const perpY = dist > 0 ?  dx / dist : 0;

  // Bow the curve outward organic-style
  const bowDir = (r === 'analyst' || r === 'planner') ? -1 : 1;
  const bow = Math.min(dist * 0.18, 30) * bowDir;
  
  const qcx = (fromPos.x + toPos.x) / 2 + perpX * bow;
  const qcy = (fromPos.y + toPos.y) / 2 + perpY * bow;

  const pathD = `M ${fromPos.x} ${fromPos.y} Q ${qcx} ${qcy} ${toPos.x} ${toPos.y}`;

  return {
    pathD,
    anchorX: anchorPos.x,
    anchorY: anchorPos.y,
    anchorDirection: direction
  };
}
