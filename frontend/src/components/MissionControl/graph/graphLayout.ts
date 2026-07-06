export interface GraphNodePosition {
  x: number;
  y: number;
  angle: number;
  ring: 'inner' | 'middle' | 'outer';
  anchorDir: 'top' | 'right' | 'bottom' | 'left';
  clusterName: 'Knowledge' | 'Reasoning' | 'Execution' | 'Perception';
}

const ROLE_CLUSTERS: Record<string, 'Knowledge' | 'Reasoning' | 'Execution' | 'Perception'> = {
  research: 'Knowledge',
  analyst: 'Knowledge',
  prediction: 'Knowledge',
  planner: 'Reasoning',
  coder: 'Reasoning',
  tool: 'Reasoning',
  automation: 'Execution',
  terminal: 'Execution',
  voice: 'Execution',
  workflow: 'Execution',
  vision: 'Perception',
  memory: 'Perception',
  browser: 'Perception'
};

/**
 * Calculates responsive orbital layout positions for the agents distributed
 * uniformly all around the Reactor Core centerpiece.
 */
export function getAgentNodeLayout(
  role: string,
  cx: number,
  cy: number,
  dimensions: { width: number; height: number },
  index: number,
  total: number
): GraphNodePosition {
  const r = role.toLowerCase();
  const cluster = ROLE_CLUSTERS[r] ?? 'Knowledge';

  // 1. Calculate responsive circular orbit radius from the smaller dimension
  const availableSize = Math.min(dimensions.width, dimensions.height);
  const orbitRadius = Math.max(180, Math.min(320, availableSize * 0.36));

  // 2. Uniform angular distribution starting at top (-Math.PI / 2)
  const angleStep = (Math.PI * 2) / total;
  const startAngle = -Math.PI / 2;
  const angle = startAngle + index * angleStep;

  // 3. Compute static coordinate offsets
  const dx = Math.cos(angle) * orbitRadius;
  const dy = Math.sin(angle) * orbitRadius;

  // 4. Resolve anchor direction pointing directly to the center core
  let anchorDir: 'top' | 'right' | 'bottom' | 'left' = 'top';
  if (Math.abs(dx) > Math.abs(dy)) {
    anchorDir = dx > 0 ? 'left' : 'right';
  } else {
    anchorDir = dy > 0 ? 'top' : 'bottom';
  }

  return {
    x: cx + dx,
    y: cy + dy,
    angle: (angle * 180) / Math.PI,
    ring: 'outer',
    anchorDir,
    clusterName: cluster
  };
}
export default getAgentNodeLayout;
