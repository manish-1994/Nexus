import type { Graph } from '../graph/graphModel';
import { ExecutionPath } from '../components/ExecutionPath';

const STATE_COLOR: Record<string, string> = {
  idle: '#00D4FF',
  thinking: '#A855F7',
  planning: '#3B82F6',
  researching: '#00D4FF',
  calling_provider: '#EC4899',
  streaming: '#38BDF8',
  completed: '#00FF95',
  failed: '#FF4D67',
  cancelled: '#94A3B8',
};

function hexRgb(hex: string) {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex);
  return m ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) } : { r: 0, g: 212, b: 255 };
}

interface GraphRendererProps {
  graph: Graph;
  coreState: string;
  activeExecution: { current_agent?: string | null; state: string } | null;
  agentStates: Record<string, { status: string }>;
  cx: number;
  cy: number;
  shiftX: number;
  shiftY: number;
}

export function GraphRenderer({
  graph,
  coreState,
  activeExecution,
  agentStates,
  cx,
  cy,
  shiftX,
  shiftY
}: GraphRendererProps) {
  const coreColor = STATE_COLOR[coreState] ?? '#00D4FF';
  const { r: crR, g: crG, b: crB } = hexRgb(coreColor);

  const activeAgentRole = activeExecution?.current_agent;
  
  // Find node coordinates of the active agent
  const activeNode = activeAgentRole ? graph.nodes[activeAgentRole] : null;

  // Responsive scaling
  const W = graph.nodes['core'] ? graph.nodes['core'].position.x * 2 : 1024;
  const H = graph.nodes['core'] ? graph.nodes['core'].position.y * 2 : 768;
  const scaleX = Math.max(0.65, Math.min(1.2, W / 1024));
  const scaleY = Math.max(0.65, Math.min(1.2, H / 768));

  // Calculate dynamic circular orbit guides from layout math
  const availableSize = Math.min(W, H);
  const orbitRadius = Math.max(180, Math.min(320, availableSize * 0.36));

  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none z-[4]">
      {/* Translate the entire SVG coordinate space together with parent shift parallax */}
      <g style={{ transform: `translate(${shiftX}px, ${shiftY}px)` }}>
        {/* ── Background AI Motherboard Circuit Guidelines ── */}
        <g opacity={0.14}>
          {/* Horizontal Bus */}
          <line
            x1={cx - orbitRadius - 40} y1={cy}
            x2={cx + orbitRadius + 40} y2={cy}
            stroke={`rgba(${crR},${crG},${crB},0.35)`} strokeWidth={1} strokeDasharray="6 8"
          />
          {/* Vertical Bus */}
          <line
            x1={cx} y1={cy - orbitRadius - 40}
            x2={cx} y2={cy + orbitRadius + 40}
            stroke={`rgba(${crR},${crG},${crB},0.35)`} strokeWidth={1} strokeDasharray="6 8"
          />
          {/* Inner Hub Ring (Reactor Border Guide) */}
          <ellipse
            cx={cx} cy={cy}
            rx={90 * scaleX} ry={90 * scaleY}
            fill="none" stroke={`rgba(${crR},${crG},${crB},0.3)`} strokeWidth={1} strokeDasharray="3 4"
          />
          {/* Outer Bounds Border Guide */}
          <ellipse
            cx={cx} cy={cy}
            rx={orbitRadius} ry={orbitRadius}
            fill="none" stroke={`rgba(${crR},${crG},${crB},0.2)`} strokeWidth={1.2} strokeDasharray="8 12"
          />
        </g>

        {/* ── Subtle Capability Zone Labels: Bound to actual node coordinates ── */}
        {(() => {
          const getGroupBounds = (roles: string[]) => {
            let minX = Infinity, maxX = -Infinity;
            let minY = Infinity, maxY = -Infinity;
            let count = 0;
            for (const role of roles) {
              const node = graph.nodes[role];
              if (node) {
                const x = node.position.x;
                const y = node.position.y;
                if (x < minX) minX = x;
                if (x > maxX) maxX = x;
                if (y < minY) minY = y;
                if (y > maxY) maxY = y;
                count++;
              }
            }
            return count > 0 ? { minX, maxX, minY, maxY, cx: (minX + maxX) / 2, cy: (minY + maxY) / 2 } : null;
          };

          const kBounds = getGroupBounds(['research', 'analyst', 'prediction']);
          const rBounds = getGroupBounds(['planner', 'coder', 'tool']);
          const eBounds = getGroupBounds(['automation', 'terminal', 'voice', 'workflow']);
          const pBounds = getGroupBounds(['vision', 'memory', 'browser']);

          const kX = kBounds ? kBounds.cx : cx;
          const kY = kBounds ? kBounds.minY - 48 - 32 : cy - orbitRadius - 40;

          const rX = rBounds ? rBounds.maxX + 40 + 45 : cx + orbitRadius + 50;
          const rY = rBounds ? rBounds.cy : cy + 3;

          const pX = pBounds ? pBounds.minX - 40 - 45 : cx - orbitRadius - 50;
          const pY = pBounds ? pBounds.cy : cy + 3;

          const eX = eBounds ? eBounds.cx : cx;
          const eY = eBounds ? eBounds.maxY + 48 + 32 : cy + orbitRadius + 50;

          return (
            <g opacity={0.35} className="font-mono text-[8.5px] tracking-[0.25em] font-bold select-none pointer-events-none fill-white/80">
              <text x={kX} y={kY} textAnchor="middle">KNOWLEDGE</text>
              <text x={rX} y={rY} textAnchor="start">REASONING</text>
              <text x={eX} y={eY} textAnchor="middle">EXECUTION</text>
              <text x={pX} y={pY} textAnchor="end">PERCEPTION</text>
            </g>
          );
        })()}

        {/* ── Active Execution Conduit Beam (Core -> Active Agent) ── */}
        {activeNode && activeAgentRole && (
          (() => {
            const agentSt = agentStates[activeAgentRole]?.status ?? 'idle';
            const isDone = agentSt === 'completed';
            const isFailed = agentSt === 'failed';
            const condColor = isDone ? '#00FF95' : isFailed ? '#FF4D67' : STATE_COLOR[coreState] ?? '#00D4FF';
            const { r: brR, g: brG, b: brB } = hexRgb(condColor);

            return (
              <ExecutionPath
                fromPos={{ x: cx, y: cy }}
                toPos={activeNode.position}
                role={activeAgentRole}
                brR={brR}
                brG={brG}
                brB={brB}
              />
            );
          })()
        )}
      </g>
    </svg>
  );
}
export default GraphRenderer;
