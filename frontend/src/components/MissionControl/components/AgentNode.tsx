import { AgentProcessor } from '../AgentProcessor';
import { resolveAnchor } from '../graph/anchorResolver';
import type { GraphNode } from '../graph/graphModel';

interface AgentNodeProps {
  agent: { role: string; name?: string };
  node: GraphNode;
  agentStates: Record<string, { status: string }>;
  activeExecution: { current_agent?: string | null; current_task?: string | null; elapsed_ms?: number } | null;
  dimmed: boolean;
  depthScale: number;
  depthBlur: number;
  cx: number;
  cy: number;
  junctionNode?: GraphNode;
}

export function AgentNode({
  agent,
  node,
  agentStates,
  activeExecution,
  dimmed,
  depthScale,
  depthBlur,
  cx,
  cy,
  junctionNode
}: AgentNodeProps) {

  const role = agent.role;
  const agentIsActive = activeExecution?.current_agent === role;
  
  // Resolve anchor direction metadata dynamically
  const portInfo = resolveAnchor(node.position, junctionNode ? junctionNode.position : { x: cx, y: cy });

  return (
    <AgentProcessor
      role={role}
      config={agent as any}
      status={(agentStates[role]?.status ?? 'idle') as any}
      isActive={agentIsActive}
      position={node.position}
      dimmed={dimmed}
      depthScale={depthScale}
      depthBlur={depthBlur}
      currentTask={agentIsActive ? activeExecution?.current_task : null}
      elapsedMs={agentIsActive ? activeExecution?.elapsed_ms : undefined}
      disableFloat={true}
      connectionAnchor={portInfo.direction}
    />
  );
}
