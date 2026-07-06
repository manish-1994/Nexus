import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Terminal, BrainCircuit } from 'lucide-react';
import { missionControlApi } from '../api/mission-control';
import type { ActiveExecution, AgentConfig, AgentStatus, ExecutionState } from '../types/mission-control';
import { ExecutionTimeline } from '../components/MissionControl/ExecutionTimeline';
import { useMissionGraph } from '../components/MissionControl/graph/useMissionGraph';
import { GraphRenderer } from '../components/MissionControl/graph/graphRenderer';
import { ReactorCore } from '../components/MissionControl/components/ReactorCore';
import { AgentNode } from '../components/MissionControl/components/AgentNode';








// ── Deterministic seeded value (stable across renders) ──
const seed = (a: number, b: number) => Math.abs(Math.sin(a * 127.1 + b * 311.7));

// ── Sort roles stably: known order first, custom ones last ──
const KNOWN_ROLE_ORDER = ['memory', 'planner', 'tool', 'coder', 'analyst', 'research'];
function sortRoles(roles: string[]): string[] {
  const known: string[] = [];
  const unknown: string[] = [];
  for (const r of roles) {
    if (KNOWN_ROLE_ORDER.includes(r)) known.push(r);
    else unknown.push(r);
  }
  known.sort((a, b) => KNOWN_ROLE_ORDER.indexOf(a) - KNOWN_ROLE_ORDER.indexOf(b));
  unknown.sort();
  return [...known, ...unknown];
}


// State → conduit color
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

// ── Depth indicators ──
function depthScale(angleDeg: number) { return 0.925 - Math.cos((angleDeg * Math.PI) / 180) * 0.075; }
function depthBlur(angleDeg: number) { return Math.max(0, Math.cos((angleDeg * Math.PI) / 180) * 0.6); }

// ── Canvas background helpers (faint stars, dust, neural back mesh) ──
function drawVignette(ctx: CanvasRenderingContext2D, W: number, H: number) {
  const g = ctx.createRadialGradient(W / 2, H / 2, W * 0.28, W / 2, H / 2, W * 0.72);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, 'rgba(0,0,0,0.65)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}

interface NeuralNode { bx: number; by: number; px: number; py: number; ampX: number; ampY: number; spd: number; ph: number; s: number; a: number; twinkle: boolean; }
interface Dust { bx: number; by: number; vx: number; vy: number; s: number; a: number; }

function drawBackground(
  ctx: CanvasRenderingContext2D, W: number, H: number, t: number,
  nodes: NeuralNode[], dust: Dust[], r: number, g: number, b: number,
  mouseX: number, mouseY: number,
) {
  const shiftX = mouseX * -28;
  const shiftY = mouseY * -28;

  // Neural mesh connections (nearby nodes)
  const MESH_DIST_SQ = 180 * 180;
  for (let i = 0; i < nodes.length - 1; i++) {
    const nx = nodes[i].bx * W + Math.sin(t * nodes[i].spd + nodes[i].ph) * nodes[i].ampX * W + shiftX;
    const ny = nodes[i].by * H + Math.cos(t * nodes[i].spd * 0.7 + nodes[i].ph) * nodes[i].ampY * H + shiftY;
    for (let j = i + 1; j < nodes.length; j++) {
      const mx = nodes[j].bx * W + Math.sin(t * nodes[j].spd + nodes[j].ph) * nodes[j].ampX * W + shiftX;
      const my = nodes[j].by * H + Math.cos(t * nodes[j].spd * 0.7 + nodes[j].ph) * nodes[j].ampY * H + shiftY;
      const dsq = (nx - mx) * (nx - mx) + (ny - my) * (ny - my);
      if (dsq < MESH_DIST_SQ) {
        const alpha = (1 - dsq / MESH_DIST_SQ) * 0.055;
        ctx.beginPath();
        ctx.moveTo(nx, ny); ctx.lineTo(mx, my);
        ctx.strokeStyle = `rgba(${r},${g},${b},${alpha})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }
    }
    // Draw the node dot
    const twinkle = nodes[i].twinkle ? 0.5 + 0.5 * Math.sin(t * 1.8 + nodes[i].ph) : 1;
    ctx.beginPath();
    ctx.arc(nx, ny, nodes[i].s, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${r},${g},${b},${nodes[i].a * twinkle})`;
    ctx.fill();
  }

  // Dust particles (very slow drift)
  dust.forEach(d => {
    const px = (((d.bx + t * d.vx) % 1 + 1) % 1 * W) + shiftX * 0.6;
    const py = (((d.by + t * d.vy) % 1 + 1) % 1 * H) + shiftY * 0.6;
    ctx.beginPath();
    ctx.arc(px, py, d.s, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(140,200,255,${d.a})`;
    ctx.fill();
  });

  // Scan line (very faint, slowly moving horizontal band)
  const sl = ((t * 18) % H + H) % H;
  ctx.fillStyle = `rgba(${r},${g},${b},0.022)`;
  ctx.fillRect(0, sl, W, 1.5);
  ctx.fillStyle = `rgba(${r},${g},${b},0.012)`;
  ctx.fillRect(0, (sl + H * 0.5) % H, W, 1.5);
}

// ── Additional mock agents to simulate a complete OS ──
const ADDITIONAL_MOCK_AGENTS: AgentConfig[] = [
  { role: 'browser', name: 'Browser', preferred_model: 'gemini-1.5-pro', preferred_provider: 'google', description: 'Web browsing agent', capabilities: ['Web Scraping', 'Dynamic Interaction'], system_prompt: '', temperature: 0.2, tools: ['navigate', 'click', 'extract'], memory_access: false, parallelizable: true, requires_plan: false, permissions: [] },
  { role: 'terminal', name: 'Terminal', preferred_model: 'gemini-1.5-pro', preferred_provider: 'google', description: 'Terminal command agent', capabilities: ['CLI execution', 'Scripting'], system_prompt: '', temperature: 0.1, tools: ['run_command', 'check_env'], memory_access: false, parallelizable: false, requires_plan: false, permissions: [] },
  { role: 'vision', name: 'Vision', preferred_model: 'gemini-1.5-flash', preferred_provider: 'google', description: 'Computer vision agent', capabilities: ['Image Processing', 'Visual Understanding'], system_prompt: '', temperature: 0.3, tools: ['analyze_image', 'detect_objects'], memory_access: false, parallelizable: true, requires_plan: false, permissions: [] },
  { role: 'voice', name: 'Voice', preferred_model: 'gemini-1.5-flash', preferred_provider: 'google', description: 'Voice audio agent', capabilities: ['TTS / STT conversion', 'Audio extraction'], system_prompt: '', temperature: 0.3, tools: ['speak', 'listen'], memory_access: false, parallelizable: true, requires_plan: false, permissions: [] },
  { role: 'workflow', name: 'Workflow', preferred_model: 'gemini-1.5-pro', preferred_provider: 'google', description: 'Workflow orchestrator agent', capabilities: ['Process orchestration', 'Parallel execution'], system_prompt: '', temperature: 0.1, tools: ['trigger_step', 'monitor_flow'], memory_access: true, parallelizable: true, requires_plan: true, permissions: [] },
  { role: 'prediction', name: 'Prediction', preferred_model: 'gemini-1.5-pro', preferred_provider: 'google', description: 'Predictive inference agent', capabilities: ['Time-series prediction', 'Inference'], system_prompt: '', temperature: 0.2, tools: ['forecast', 'regression'], memory_access: false, parallelizable: true, requires_plan: false, permissions: [] },
  { role: 'automation', name: 'Automation', preferred_model: 'gemini-1.5-pro', preferred_provider: 'google', description: 'Process automation agent', capabilities: ['Cron scheduling', 'Task automation'], system_prompt: '', temperature: 0.1, tools: ['schedule_job', 'run_trigger'], memory_access: false, parallelizable: true, requires_plan: false, permissions: [] }
];

// ── Component ──────────────────────────────────────────────────────────────

interface AgentOrbState { role: string; status: AgentStatus; }

export default function DashboardPage() {
  const queryClient = useQueryClient();

  const [coreState, setCoreState] = useState<ExecutionState>('idle');
  const [activeExecution, setActiveExecution] = useState<ActiveExecution | null>(null);
  const [agentStates, setAgentStates] = useState<Record<string, AgentOrbState>>({});
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const conduitCanvasRef = useRef<HTMLCanvasElement>(null);
  const workspaceRef     = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 900, height: 700 });

  const animTimeRef  = useRef(0);
  const animFrameRef = useRef<number>(0);
  const [, forceRender] = useState(0);

  // Parallax tracking refs
  const targetMouseXRef = useRef(0);
  const targetMouseYRef = useRef(0);
  const curMouseXRef = useRef(0);
  const curMouseYRef = useRef(0);

  // Background stable seeds
  const neuralNodes = useMemo((): NeuralNode[] =>
    Array.from({ length: 44 }, (_, i) => ({
      bx: seed(i, 0), by: seed(i, 1),
      px: 0, py: 0,
      ampX: 0.025 + seed(i, 2) * 0.035, ampY: 0.025 + seed(i, 3) * 0.035,
      spd: 0.006 + seed(i, 4) * 0.008, ph: seed(i, 5) * Math.PI * 2,
      s: 0.8 + seed(i, 6) * 2.0, a: 0.055 + seed(i, 7) * 0.11,
      twinkle: seed(i, 8) > 0.68,
    })), []);

  const dustParticles = useMemo((): Dust[] =>
    Array.from({ length: 68 }, (_, i) => ({
      bx: seed(i, 10), by: seed(i, 11),
      vx: (seed(i, 12) - 0.5) * 0.000022, vy: (seed(i, 13) - 0.5) * 0.000022,
      s: 0.45 + seed(i, 14) * 1.15, a: 0.035 + seed(i, 15) * 0.09,
    })), []);

  // Measure workspace & sync canvas drawing buffer
  useEffect(() => {
    const measure = () => {
      if (workspaceRef.current) {
        const w = workspaceRef.current.clientWidth;
        const h = workspaceRef.current.clientHeight;
        setDimensions({ width: w, height: h });
        // Sync canvas drawing buffer to CSS size
        if (conduitCanvasRef.current) {
          const canvas = conduitCanvasRef.current;
          const dpr = window.devicePixelRatio || 1;
          canvas.width = Math.round(w * dpr);
          canvas.height = Math.round(h * dpr);
          const ctx = canvas.getContext('2d');
          if (ctx) ctx.scale(dpr, dpr);
        }
      }
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (workspaceRef.current) ro.observe(workspaceRef.current);
    return () => ro.disconnect();
  }, []);

  // Initial fetch and summary state query
  const { data: summary } = useQuery({
    queryKey: ['mission-control-summary'],
    queryFn: missionControlApi.getSummary,
    refetchInterval: 30000,
  });

  // Real-time event-driven EventSource subscription
  useEffect(() => {
    const url = `${window.location.origin}/api/mission-control/events/stream`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'connected' || data.type === 'heartbeat') return;
        queryClient.invalidateQueries({ queryKey: ['mission-control-summary'] });
      } catch (err) {
        console.error("Error processing SSE message:", err);
      }
    };

    return () => eventSource.close();
  }, [queryClient]);

  // Merge backend agents and mock agents seamlessly
  const allAgents: AgentConfig[] = useMemo(() => {
    const fromBackend = summary ? Object.values({ ...summary.agents.builtin, ...summary.agents.custom }) : [];
    const merged = [...fromBackend];
    ADDITIONAL_MOCK_AGENTS.forEach(mock => {
      if (!merged.some(a => a.role === mock.role)) {
        merged.push(mock);
      }
    });
    return merged;
  }, [summary]);

  // Dynamic agent roles sorted stably
  const agentRoles = useMemo(() => sortRoles(allAgents.map(a => a.role)), [allAgents]);

  // State sync
  useEffect(() => {
    if (!summary) return;
    setLastUpdate(new Date());

    const stateMap: Record<string, ExecutionState> = {
      idle: 'idle', thinking: 'thinking', planning: 'planning', researching: 'researching',
      calling_provider: 'calling_provider', streaming: 'streaming', completed: 'completed',
      failed: 'failed', cancelled: 'cancelled',
    };
    setCoreState(stateMap[summary.orchestrator?.status || 'idle'] ?? 'idle');

    const execs = summary.active_executions || [];
    const exec = execs.length > 0
      ? [...execs].sort((a, b) => new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime())[0]
      : null;

    setActiveExecution(exec);

    const ns: Record<string, AgentOrbState> = {};
    // Seed states for all agents, including our mocks
    allAgents.forEach(a => { ns[a.role] = { role: a.role, status: 'idle' }; });
    if (exec?.current_agent && ns[exec.current_agent]) {
      const sMap: Record<string, AgentStatus> = {
        idle: 'idle', thinking: 'thinking', planning: 'thinking', researching: 'running',
        calling_provider: 'running', streaming: 'streaming', completed: 'completed', failed: 'failed', cancelled: 'failed',
      };
      ns[exec.current_agent] = { role: exec.current_agent, status: sMap[exec.state] ?? 'running' };
    }
    setAgentStates(ns);
  }, [summary, allAgents]);

  // ── Reactor size ──
  const reactorSize = useMemo(() => {
    const w = dimensions.width;
    const h = dimensions.height;
    const target = Math.min(w * 0.20, h * 0.23);
    return Math.max(140, Math.min(210, Math.round(target)));
  }, [dimensions]);

  const cx = dimensions.width / 2;
  const cy = dimensions.height / 2;

  // ── True graph model generator ──
  const graph = useMissionGraph({
    dimensions,
    agentRoles
  });


  // Mouse Move tracking handlers for parallax
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!workspaceRef.current) return;
    const rect = workspaceRef.current.getBoundingClientRect();
    targetMouseXRef.current = (e.clientX - rect.left) / rect.width - 0.5;
    targetMouseYRef.current = (e.clientY - rect.top) / rect.height - 0.5;
  };

  const handleMouseLeave = () => {
    targetMouseXRef.current = 0;
    targetMouseYRef.current = 0;
  };


  // Canvas background scene rendering
  const drawCanvas = useCallback(() => {
    const canvas = conduitCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const t = animTimeRef.current;
    const coreColor = STATE_COLOR[coreState] ?? '#00D4FF';
    const { r, g, b } = hexRgb(coreColor);

    drawBackground(ctx, W, H, t, neuralNodes, dustParticles, r, g, b, curMouseXRef.current, curMouseYRef.current);
    drawVignette(ctx, W, H);
  }, [neuralNodes, dustParticles, coreState]);

  // Animation render loop
  useEffect(() => {
    const loop = () => {
      animTimeRef.current += 0.022;
      curMouseXRef.current += (targetMouseXRef.current - curMouseXRef.current) * 0.08;
      curMouseYRef.current += (targetMouseYRef.current - curMouseYRef.current) * 0.08;

      drawCanvas();
      forceRender(n => n + 1);
      animFrameRef.current = requestAnimationFrame(loop);
    };
    animFrameRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [drawCanvas]);

  // Telemetry metrics
  const elapsedSec = activeExecution?.elapsed_ms ? (activeExecution.elapsed_ms / 1000).toFixed(1) : '0.0';
  const tokenCount = activeExecution?.total_tokens ?? 0;
  const tokensFormatted = tokenCount >= 1000 ? `${(tokenCount / 1000).toFixed(1)}K` : String(tokenCount);
  const isActive = activeExecution != null;

  const coreBreathScale = 1.0 + Math.sin(animTimeRef.current * 0.8) * 0.02;

  // Calculate mouse shift offsets
  const shiftX = curMouseXRef.current * 6;
  const shiftY = curMouseYRef.current * 6;

  return (
    <div className="flex-1 flex flex-col bg-background relative select-none font-sans min-h-0">

      {/* ── Top HUD ── */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-white/[0.06] bg-surface/25 backdrop-blur-sm z-20 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent/12 border border-accent/28 flex items-center justify-center">
            <BrainCircuit size={17} className="text-accent" />
          </div>
          <div>
            <h1 className="text-[11px] font-mono font-bold text-white tracking-[0.25em] uppercase">Mission Control</h1>
            <p className="text-[8px] font-mono text-accent/55 uppercase tracking-[0.18em]">Nexus AI Core — Neural Network Visualizer</p>
          </div>
        </div>
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-4 text-[8.5px] font-mono">
            <span className="text-white/25">T: <span className="text-accent">{elapsedSec}s</span></span>
            <span className="text-white/25">TOKENS: <span className="text-success">{tokensFormatted}</span></span>
            {activeExecution?.provider_name && (
              <span className="text-white/25">VIA: <span className="text-warning">{activeExecution.provider_name.toUpperCase()}</span></span>
            )}
            {activeExecution?.model && (
              <span className="text-white/25 hidden xl:inline">MODEL: <span className="text-secondary-light truncate max-w-[90px] inline-block">{activeExecution.model}</span></span>
            )}
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-accent/12 border border-accent/28 rounded-lg">
            <motion.span className="w-1.5 h-1.5 rounded-full bg-accent" animate={{ opacity: [0.35, 1, 0.35] }} transition={{ duration: 1.6, repeat: Infinity }} />
            <span className="text-[8px] font-mono font-bold text-accent/85 tracking-[0.18em] uppercase">Core Armed</span>
          </div>
          <span className="text-[8px] font-mono text-white/22 hidden lg:block">{lastUpdate.toLocaleTimeString()}</span>
        </div>
      </header>

      {/* ── Main Workspace — Reactor is the hero ── */}
      <div
        className="flex-1 grid grid-cols-[1fr_320px] lg:grid-cols-[1fr_280px] md:grid-cols-1 relative z-10 min-w-0 min-h-0"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ minHeight: 0 }}
      >

        {/* Center Visualization — full height, reactor is hero */}
        <div ref={workspaceRef} className="relative min-w-0 min-h-0 overflow-hidden md:order-1">

          {/* ── True Graph Neural network Renderer ── */}
          <GraphRenderer
            graph={graph}
            coreState={coreState}
            activeExecution={activeExecution}
            agentStates={agentStates}
            cx={cx}
            cy={cy}
            shiftX={shiftX}
            shiftY={shiftY}
          />

          {/* Nexus Reactor Core centerpiece component */}
          <ReactorCore
            cx={cx}
            cy={cy}
            shiftX={shiftX}
            shiftY={shiftY}
            reactorSize={reactorSize}
            coreState={coreState}
            activeExecutions={summary?.orchestrator?.active_executions}
            coreBreathScale={coreBreathScale}
          />

          {/* Agent Processor Nodes — organized in cognitive clusters */}
          {allAgents.map(agent => {
            const role = agent.role;
            const node = graph.nodes[role];
            if (!node) return null;

            const agentIsActive = activeExecution?.current_agent === role;
            const dScale = depthScale(node.angle);
            const dBlur  = depthBlur(node.angle);

            // Shift positions uniformly by the mouse parallax vector
            const nodeWithParallax = {
              ...node,
              position: {
                x: node.position.x + shiftX,
                y: node.position.y + shiftY
              }
            };

            const coreWithParallax = graph.nodes['core'] ? {
              ...graph.nodes['core'],
              position: {
                x: graph.nodes['core'].position.x + shiftX,
                y: graph.nodes['core'].position.y + shiftY
              }
            } : undefined;

            return (
              <AgentNode
                key={role}
                agent={agent}
                node={nodeWithParallax}
                agentStates={agentStates}
                activeExecution={activeExecution}
                dimmed={isActive && !agentIsActive}
                depthScale={dScale}
                depthBlur={dBlur}
                cx={cx}
                cy={cy}
                junctionNode={coreWithParallax}
              />
            );
          })}



        </div>

        {/* Right: Event Timeline */}
        <aside className="flex flex-col bg-surface/18 border-l border-white/[0.05] backdrop-blur-md z-10 overflow-hidden w-[320px] lg:w-[280px] md:w-full md:order-2 shrink-0 min-w-0">
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/[0.05] bg-white/[0.03] shrink-0">
            <Terminal size={14} className="text-warning" />
            <span className="text-[9px] font-mono font-bold uppercase tracking-[0.18em] text-warning/85">Event Timeline</span>
          </div>
          <div className="flex-1 overflow-hidden p-3 min-h-0">
            <ExecutionTimeline events={summary?.recent_events ?? []} maxItems={50} />
          </div>
        </aside>
      </div>
    </div>
  );
}