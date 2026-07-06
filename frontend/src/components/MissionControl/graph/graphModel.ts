export type NodeType = 'core' | 'junction' | 'agent';

export interface Point {
  x: number;
  y: number;
}

export interface GraphNode {
  id: string;
  type: NodeType;
  position: Point;
  angle: number;
  // Specific data for agents
  role?: string;
  ring?: 'inner' | 'middle' | 'outer';
  branch?: number;
}

export interface GraphEdge {
  id: string;
  from: string; // Node ID
  to: string;   // Node ID
  type: 'trunk' | 'branch';
}

export interface Graph {
  nodes: Record<string, GraphNode>;
  edges: GraphEdge[];
}
