import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Search,
  Code,
  BarChart3,
  Database,
  Wrench,
  GitBranch,
  CheckCircle2,
  Loader2,
  XCircle,
  Circle,
} from 'lucide-react';
import type { ActiveExecution } from '../../types/mission-control';
import { springs } from '../../styles/motion';

interface ExecutionGraphProps {
  execution: ActiveExecution | null;
  className?: string;
}

interface GraphNode {
  id: string;
  label: string;
  role: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'queued';
  dependencies: string[];
}

interface GraphEdge {
  from: string;
  to: string;
}

const ROLE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  planner: Brain,
  research: Search,
  coder: Code,
  analyst: BarChart3,
  memory: Database,
  tool: Wrench,
};

const ROLE_COLORS: Record<string, { node: string; line: string; glow: string }> = {
  planner: { node: 'border-purple-400/50 bg-purple-400/10', line: 'stroke-purple-400/40', glow: 'shadow-purple-400/20' },
  research: { node: 'border-cyan-400/50 bg-cyan-400/10', line: 'stroke-cyan-400/40', glow: 'shadow-cyan-400/20' },
  coder: { node: 'border-emerald-400/50 bg-emerald-400/10', line: 'stroke-emerald-400/40', glow: 'shadow-emerald-400/20' },
  analyst: { node: 'border-amber-400/50 bg-amber-400/10', line: 'stroke-amber-400/40', glow: 'shadow-amber-400/20' },
  memory: { node: 'border-blue-400/50 bg-blue-400/10', line: 'stroke-blue-400/40', glow: 'shadow-blue-400/20' },
  tool: { node: 'border-rose-400/50 bg-rose-400/10', line: 'stroke-rose-400/40', glow: 'shadow-rose-400/20' },
};

const DEFAULT_COLORS = { node: 'border-white/20 bg-white/5', line: 'stroke-white/20', glow: 'shadow-white/5' };

function getRoleColors(role: string) {
  return ROLE_COLORS[role] || DEFAULT_COLORS;
}

function getRoleIcon(role: string) {
  const Icon = ROLE_ICONS[role] || Circle;
  return Icon;
}

function StatusIndicator({ status }: { status: GraphNode['status'] }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="w-3 h-3 text-emerald-400" />;
    case 'running':
      return (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
        >
          <Loader2 className="w-3 h-3 text-cyan-400" />
        </motion.div>
      );
    case 'failed':
      return <XCircle className="w-3 h-3 text-red-400" />;
    case 'queued':
      return (
        <motion.div
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <Circle className="w-3 h-3 text-amber-400 fill-amber-400/30" />
        </motion.div>
      );
    default:
      return <Circle className="w-3 h-3 text-white/20" />;
  }
}

function GraphNodeCard({
  node,
  isActive,
}: {
  node: GraphNode;
  isActive: boolean;
}) {
  const colors = getRoleColors(node.role);
  const Icon = getRoleIcon(node.role);

  return (
    <motion.div
      className={`relative flex items-center gap-2 px-3 py-2 rounded-lg border ${colors.node} ${colors.glow} backdrop-blur-sm`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{
        opacity: 1,
        scale: isActive ? 1.03 : 1,
      }}
      transition={springs.gentle}
    >
      {/* Active pulse */}
      {isActive && (
        <motion.div
          className="absolute inset-0 rounded-lg"
          animate={{ opacity: [0.08, 0.2, 0.08] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            background:
              node.status === 'running'
                ? 'rgba(0, 229, 255, 0.3)'
                : 'rgba(168, 85, 247, 0.3)',
          }}
        />
      )}

      <div className="relative z-10 flex items-center gap-2 flex-1 min-w-0">
        <Icon className="w-3.5 h-3.5 text-white/60 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-mono text-white/80 truncate">{node.label}</div>
          <div className="text-[8px] font-mono text-white/30 uppercase">{node.role}</div>
        </div>
        <StatusIndicator status={node.status} />
      </div>
    </motion.div>
  );
}

function buildGraphFromExecution(execution: ActiveExecution): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  // Determine task statuses from execution data
  const completedSet = new Set(execution.completed_tasks || []);
  const runningSet = new Set(execution.running_tasks || []);
  const pendingSet = new Set(execution.pending_tasks || []);
  const failedSet = new Set(execution.failed_tasks || []);

  // Build nodes from all known tasks
  const allTaskIds = new Set([
    ...(execution.completed_tasks || []),
    ...(execution.running_tasks || []),
    ...(execution.pending_tasks || []),
    ...(execution.failed_tasks || []),
  ]);

  // If we have task details with roles, use them
  if (execution.task_details && execution.task_details.length > 0) {
    for (const task of execution.task_details) {
      const status: GraphNode['status'] = completedSet.has(task.id)
        ? 'completed'
        : runningSet.has(task.id)
        ? 'running'
        : failedSet.has(task.id)
        ? 'failed'
        : pendingSet.has(task.id)
        ? 'queued'
        : 'pending';

      nodes.push({
        id: task.id,
        label: task.label || task.id,
        role: task.role || 'unknown',
        status,
        dependencies: task.depends_on || [],
      });

      for (const dep of task.depends_on || []) {
        edges.push({ from: dep, to: task.id });
      }
    }
  } else if (allTaskIds.size > 0) {
    // Fallback: create nodes from task IDs without role info
    const taskList = Array.from(allTaskIds);
    // Assume sequential: planner → research → coder → analyst → synthesis
    const defaultRoles = ['planner', 'research', 'coder', 'analyst'];
    for (let i = 0; i < taskList.length; i++) {
      const id = taskList[i];
      const role = defaultRoles[i] || 'tool';
      const status: GraphNode['status'] = completedSet.has(id)
        ? 'completed'
        : runningSet.has(id)
        ? 'running'
        : failedSet.has(id)
        ? 'failed'
        : pendingSet.has(id)
        ? 'queued'
        : 'pending';

      nodes.push({
        id,
        label: id,
        role,
        status,
        dependencies: i > 0 ? [taskList[i - 1]] : [],
      });

      if (i > 0) {
        edges.push({ from: taskList[i - 1], to: id });
      }
    }
  }

  return { nodes, edges };
}

export function ExecutionGraph({ execution, className = '' }: ExecutionGraphProps) {
  const hasExecution = execution !== null;
  const { nodes, edges } = execution ? buildGraphFromExecution(execution) : { nodes: [], edges: [] };

  // Layout: horizontal flow left to right
  const nodeWidth = 160;
  const nodeGap = 40;
  const totalWidth = nodes.length * (nodeWidth + nodeGap) - nodeGap;

  return (
    <motion.div
      className={`flex flex-col gap-3 ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.4, ...springs.gentle }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-1">
        <GitBranch className="w-4 h-4 text-cyan-400" />
        <span className="text-xs font-mono uppercase tracking-[0.15em] text-cyan-400/80">
          Execution Graph
        </span>
        {hasExecution && (
          <span className="ml-auto text-[10px] font-mono text-white/30">
            {nodes.length} node{nodes.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Graph Visualization */}
      {nodes.length > 0 ? (
        <div className="relative overflow-x-auto pb-2">
          <div
            className="relative flex items-center gap-4 py-4 px-2"
            style={{ minWidth: Math.max(totalWidth, 300) }}
          >
            {/* SVG connection lines */}
            <svg
              className="absolute inset-0 pointer-events-none"
              style={{ width: '100%', height: '100%' }}
              preserveAspectRatio="none"
            >
              {edges.map((edge, i) => {
                const fromIdx = nodes.findIndex((n) => n.id === edge.from);
                const toIdx = nodes.findIndex((n) => n.id === edge.to);
                if (fromIdx === -1 || toIdx === -1) return null;

                const fromX = fromIdx * (nodeWidth + nodeGap) + nodeWidth + 16;
                const toX = toIdx * (nodeWidth + nodeGap) + 16;
                const y = 32; // center of nodes

                const fromNode = nodes[fromIdx];
                const toNode = nodes[toIdx];
                const colors = getRoleColors(toNode.role);

                const isActiveEdge =
                  fromNode.status === 'completed' && toNode.status === 'running';

                return (
                  <g key={`edge-${i}`}>
                    {/* Base line */}
                    <line
                      x1={fromX}
                      y1={y}
                      x2={toX}
                      y2={y}
                      className={colors.line}
                      strokeWidth={1.5}
                      strokeDasharray={fromNode.status === 'completed' ? 'none' : '4 4'}
                    />
                    {/* Arrow head */}
                    <polygon
                      points={`${toX - 6},${y - 4} ${toX},${y} ${toX - 6},${y + 4}`}
                      className={colors.line}
                      fill="currentColor"
                    />
                    {/* Energy pulse on active edge */}
                    {isActiveEdge && (
                      <motion.circle
                        r={3}
                        fill="rgba(0, 229, 255, 0.8)"
                        initial={{ cx: fromX }}
                        animate={{ cx: toX }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          ease: 'linear',
                        }}
                      />
                    )}
                  </g>
                );
              })}
            </svg>

            {/* Nodes */}
            <AnimatePresence>
              {nodes.map((node) => (
                <GraphNodeCard
                  key={node.id}
                  node={node}
                  isActive={
                    node.status === 'running' ||
                    node.id === execution?.current_task
                  }
                />
              ))}
            </AnimatePresence>
          </div>
        </div>
      ) : hasExecution ? (
        /* Has execution but no task details */
        <motion.div
          className="flex flex-col items-center justify-center py-6 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mb-2">
            <GitBranch className="w-4 h-4 text-white/20" />
          </div>
          <div className="text-xs font-mono text-white/30">No Task Graph Available</div>
          <div className="text-[10px] text-white/15 mt-1">
            Task details not yet populated
          </div>
        </motion.div>
      ) : (
        /* No execution at all */
        <motion.div
          className="flex flex-col items-center justify-center py-8 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
            <GitBranch className="w-5 h-5 text-white/20" />
          </div>
          <div className="text-xs font-mono text-white/30">Awaiting Execution</div>
          <div className="text-[10px] text-white/15 mt-1 max-w-[220px]">
            The task graph will appear here when an execution starts
          </div>
        </motion.div>
      )}

      {/* Legend */}
      {nodes.length > 0 && (
        <div className="flex items-center gap-3 px-1 text-[9px] font-mono text-white/30">
          <div className="flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>Completed</span>
          </div>
          <div className="flex items-center gap-1">
            <Loader2 className="w-3 h-3 text-cyan-400" />
            <span>Running</span>
          </div>
          <div className="flex items-center gap-1">
            <Circle className="w-3 h-3 text-amber-400 fill-amber-400/30" />
            <span>Queued</span>
          </div>
          <div className="flex items-center gap-1">
            <XCircle className="w-3 h-3 text-red-400" />
            <span>Failed</span>
          </div>
        </div>
      )}
    </motion.div>
  );
}

export default ExecutionGraph;