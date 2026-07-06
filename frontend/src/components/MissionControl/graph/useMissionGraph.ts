import { useMemo } from 'react';
import type { Graph, GraphNode } from './graphModel';
import { getAgentNodeLayout } from './graphLayout';

interface UseMissionGraphProps {
  dimensions: { width: number; height: number };
  agentRoles: string[];
}

export function useMissionGraph({
  dimensions,
  agentRoles
}: UseMissionGraphProps): Graph {
  return useMemo(() => {
    const cx = dimensions.width / 2;
    const cy = dimensions.height / 2;


    const nodes: Record<string, GraphNode> = {};

    // 1. Create Core centerpiece node
    nodes['core'] = {
      id: 'core',
      type: 'core',
      position: { x: cx, y: cy },
      angle: 0
    };

    // 2. Generate Agent circular positions stably
    agentRoles.forEach((role, index) => {
      const layout = getAgentNodeLayout(role, cx, cy, dimensions, index, agentRoles.length);

      nodes[role] = {
        id: role,
        type: 'agent',
        position: { x: layout.x, y: layout.y },
        angle: layout.angle,
        role,
        ring: layout.ring
      };
    });

    return { nodes, edges: [] };
  }, [dimensions, agentRoles]);
}
export default useMissionGraph;
