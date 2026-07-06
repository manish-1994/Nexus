import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Terminal, GitBranch, BrainCircuit } from 'lucide-react';
import { missionControlApi } from '../api/mission-control';
import type { ActiveExecution, AgentConfig, AgentStatus, ExecutionState } from '../types/mission-control';
import { NexusReactorCore } from '../components/Core/NexusReactorCore';
import { AgentProcessor } from '../components/MissionControl/AgentProcessor';
import { ExecutionGraph } from '../components/MissionControl/ExecutionGraph';
import { ExecutionTimeline } from '../components/MissionControl/ExecutionTimeline';

// ── Deterministic seeded value (stable across renders) ──
const seed = (a: number, b: number) => Math.abs(Math.sin(a * 127.1 + b * 311.7));

// ── Hex layout: 6 agents at 60° intervals ──
const AGENT_LAYOUT: Record<string, { angleDeg: number }> = {
  memory:   { angleDeg: 0   },
  planner:  { angleDeg: 60  },
  tool:     { angleDeg: 120 },
  coder:    { angleDeg: 180 },
  analyst:  { angleDeg: 240 },
  research: { angleDeg: 300 },
};
const AGENT_ROLES = Object.keys(AGENT_LAYOUT);
const BASE_ORBIT_RADIUS = 420;

// Secondary cortex mesh links (agent-to-agent)
const CORTEX_MESH = [
  ['memory','planner'], ['planner','tool'], ['tool','coder'],
  ['coder','analyst'], ['analyst','research'], ['research','memory'],
  ['planner','coder'], ['research','tool'],
];

// State → conduit color
const STATE_COLOR: Record<string, string> = {
  idle:'#00D4FF', thinking:'#A855F7', planning:'#3B82F6', researching:'#00D4FF',
  calling_provider:'#EC4899', streaming:'#38BDF8', completed:'#00FF95',
  failed:'#FF4D67', cancelled:'#94A3B8',
};

// ── Packet types (pre-seeded, stable) ──
interface Packet { phase: number; speed: number; size: number; alpha: number; dir: 1|-1; isBurst: boolean; }

// ── Bezier helpers ──
function qbp(t: number, p0x: number, p0y: number, p1x: number, p1y: number, p2x: number, p2y: number) {
  const m = 1 - t;
  return { x: m*m*p0x + 2*m*t*p1x + t*t*p2x, y: m*m*p0y + 2*m*t*p1y + t*t*p2y };
}
function hexRgb(hex: string) {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex);
  return m ? { r: parseInt(m[1],16), g: parseInt(m[2],16), b: parseInt(m[3],16) } : { r:0,g:212,b:255 };
}

// ── Depth: bottom nodes closer, top nodes farther ──
function depthScale(angleDeg: number) { return 0.925 - Math.cos((angleDeg*Math.PI)/180)*0.075; }
function depthBlur(angleDeg: number)  { return Math.max(0, Math.cos((angleDeg*Math.PI)/180) * 0.6); }

// ── Canvas drawing helpers (pure, outside component) ──

function drawVignette(ctx: CanvasRenderingContext2D, W: number, H: number) {
  const g = ctx.createRadialGradient(W/2,H/2,W*0.28,W/2,H/2,W*0.72);
  g.addColorStop(0,'rgba(0,0,0,0)');
  g.addColorStop(1,'rgba(0,0,0,0.65)');
  ctx.fillStyle = g;
  ctx.fillRect(0,0,W,H);
}

interface NeuralNode { bx:number; by:number; px:number; py:number; ampX:number; ampY:number; spd:number; ph:number; s:number; a:number; twinkle:boolean; }
interface Dust { bx:number; by:number; vx:number; vy:number; s:number; a:number; }

function drawBackground(
  ctx: CanvasRenderingContext2D, W: number, H: number, t: number,
  nodes: NeuralNode[], dust: Dust[], r: number, g: number, b: number,
) {
  // Holographic rotating circles (very large, very faint)
  [0.72, 0.86].forEach((rFrac, i) => {
    ctx.save();
    ctx.translate(W/2, H/2);
    ctx.rotate(t * (i === 0 ? 0.006 : -0.004));
    const cr = Math.min(W,H) * rFrac;
    ctx.beginPath();
    ctx.arc(0, 0, cr, 0, Math.PI*2);
    ctx.setLineDash([60, 120]);
    ctx.strokeStyle = `rgba(${r},${g},${b},0.04)`;
    ctx.lineWidth = 0.8;
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  });

  // Neural mesh connections (nearby nodes)
  const MESH_DIST_SQ = 180 * 180;
  for (let i = 0; i < nodes.length - 1; i++) {
    const nx = nodes[i].bx*W + Math.sin(t*nodes[i].spd + nodes[i].ph)*nodes[i].ampX*W;
    const ny = nodes[i].by*H + Math.cos(t*nodes[i].spd*0.7 + nodes[i].ph)*nodes[i].ampY*H;
    for (let j = i+1; j < nodes.length; j++) {
      const mx = nodes[j].bx*W + Math.sin(t*nodes[j].spd + nodes[j].ph)*nodes[j].ampX*W;
      const my = nodes[j].by*H + Math.cos(t*nodes[j].spd*0.7 + nodes[j].ph)*nodes[j].ampY*H;
      const dsq = (nx-mx)*(nx-mx)+(ny-my)*(ny-my);
      if (dsq < MESH_DIST_SQ) {
        const alpha = (1 - dsq/MESH_DIST_SQ) * 0.055;
        ctx.beginPath();
        ctx.moveTo(nx,ny); ctx.lineTo(mx,my);
        ctx.strokeStyle = `rgba(${r},${g},${b},${alpha})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }
    }
    // Draw the node dot
    const twinkle = nodes[i].twinkle ? 0.5 + 0.5*Math.sin(t*1.8 + nodes[i].ph) : 1;
    ctx.beginPath();
    ctx.arc(nx, ny, nodes[i].s, 0, Math.PI*2);
    ctx.fillStyle = `rgba(${r},${g},${b},${nodes[i].a * twinkle})`;
    ctx.fill();
  }

  // Dust particles (very slow drift)
  dust.forEach(d => {
    const px = ((d.bx + t * d.vx) % 1 + 1) % 1 * W;
    const py = ((d.by + t * d.vy) % 1 + 1) % 1 * H;
    ctx.beginPath();
    ctx.arc(px, py, d.s, 0, Math.PI*2);
    ctx.fillStyle = `rgba(140,200,255,${d.a})`;
    ctx.fill();
  });

  // Scan line (very faint, slowly moving horizontal band)
  const sl = ((t * 18) % H + H) % H;
  ctx.fillStyle = `rgba(${r},${g},${b},0.022)`;
  ctx.fillRect(0, sl, W, 1.5);
  ctx.fillStyle = `rgba(${r},${g},${b},0.012)`;
  ctx.fillRect(0, (sl + H*0.5) % H, W, 1.5);
}

function drawOrbitalRail(
  ctx: CanvasRenderingContext2D, cx: number, cy: number, r: number, t: number,
  crR: number, crG: number, crB: number,
) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(t * 0.0014); // extremely slow rotation
  // Rail base ring
  ctx.beginPath();
  ctx.arc(0, 0, r, 0, Math.PI*2);
  ctx.setLineDash([4, 12]);
  ctx.strokeStyle = `rgba(${crR},${crG},${crB},0.10)`;
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.setLineDash([]);
  // Rail tick marks at every 30° (12 positions)
  for (let i = 0; i < 12; i++) {
    const a = (i/12)*Math.PI*2;
    const major = i % 3 === 0;
    ctx.beginPath();
    ctx.moveTo(Math.cos(a)*(r-4), Math.sin(a)*(r-4));
    ctx.lineTo(Math.cos(a)*(r+4), Math.sin(a)*(r+4));
    ctx.strokeStyle = `rgba(${crR},${crG},${crB},${major ? 0.35 : 0.12})`;
    ctx.lineWidth = major ? 1.2 : 0.6;
    ctx.stroke();
  }
  ctx.restore();
}

function drawCortexMesh(
  ctx: CanvasRenderingContext2D,
  positions: Record<string, {x:number;y:number}>,
  r: number, g: number, b: number,
) {
  CORTEX_MESH.forEach(([from, to]) => {
    const sp = positions[from], ep = positions[to];
    if (!sp || !ep) return;
    ctx.beginPath();
    ctx.moveTo(sp.x, sp.y);
    ctx.lineTo(ep.x, ep.y);
    ctx.setLineDash([2, 9]);
    ctx.strokeStyle = `rgba(${r},${g},${b},0.06)`;
    ctx.lineWidth = 0.65;
    ctx.stroke();
    ctx.setLineDash([]);
  });
}

function drawConduit(
  ctx: CanvasRenderingContext2D,
  cx: number, cy: number,
  pos: {x:number;y:number},
  packets: Packet[],
  t: number,
  coreColor: string,
  isAgentActive: boolean,
  histFade: number,
  isAnyActive: boolean,
  agentStatus: string,
) {
  const isDone   = agentStatus === 'completed';
  const isFailed = agentStatus === 'failed';
  const condColor = isDone ? '#00FF95' : isFailed ? '#FF4D67' : coreColor;
  const { r, g, b } = hexRgb(condColor);

  const isLit = isAgentActive || isDone || isFailed || histFade > 0.01;
  const baseDim = isAnyActive && !isAgentActive && !isDone && histFade < 0.01;
  if (baseDim && !isLit) return; // skip fully dimmed idle conduits in active mode

  // Bezier control point (curve off radial axis for organic shape)
  const dx = pos.x - cx, dy = pos.y - cy;
  const dist = Math.sqrt(dx*dx + dy*dy) || 1;
  const nx = -dy/dist, ny = dx/dist;
  const bend = dist*0.20 + Math.sin(t*0.6 + Math.atan2(dy,dx)*2)*9;
  const cpx = (cx+pos.x)/2 + nx*bend;
  const cpy = (cy+pos.y)/2 + ny*bend;

  const activeAlpha = isAgentActive ? 1.0 : isDone ? 0.6 : histFade > 0.01 ? histFade * 0.55 : 0.14;

  // Pass 1: Thick outer glow tube
  ctx.save();
  ctx.beginPath(); ctx.moveTo(cx,cy); ctx.quadraticCurveTo(cpx,cpy,pos.x,pos.y);
  ctx.strokeStyle = `rgba(${r},${g},${b},${activeAlpha * 0.45})`;
  ctx.lineWidth = isAgentActive ? 16 : isDone ? 7 : histFade > 0.01 ? 6 : 4;
  ctx.shadowColor = condColor; ctx.shadowBlur = isAgentActive ? 20 : 6;
  ctx.globalAlpha = 0.3;
  ctx.stroke();
  ctx.restore();

  // Pass 2: Mid beam
  ctx.save();
  ctx.beginPath(); ctx.moveTo(cx,cy); ctx.quadraticCurveTo(cpx,cpy,pos.x,pos.y);
  ctx.strokeStyle = `rgba(${r},${g},${b},${activeAlpha})`;
  ctx.lineWidth = isAgentActive ? 3.8 : isDone ? 2.0 : histFade > 0.01 ? 1.8 : 1.2;
  ctx.shadowColor = condColor; ctx.shadowBlur = isAgentActive ? 14 : 4;
  ctx.stroke();
  ctx.restore();

  // Pass 3: Inner bright white filament
  ctx.save();
  ctx.beginPath(); ctx.moveTo(cx,cy); ctx.quadraticCurveTo(cpx,cpy,pos.x,pos.y);
  ctx.strokeStyle = `rgba(255,255,255,${activeAlpha * 0.72})`;
  ctx.lineWidth = isAgentActive ? 1.2 : 0.5;
  ctx.stroke();
  ctx.restore();

  // Energy packets
  packets.forEach(pkt => {
    // Determine if this packet type should be visible in current state
    const showIdle   = !isAnyActive;
    const showActive = isAgentActive;
    const showReturn = isAgentActive && pkt.dir === -1;
    const showHistory = histFade > 0.01 && !isAgentActive;

    if (!showIdle && !showActive && !showReturn && !showHistory && !isDone) return;

    const speedMult  = isAgentActive ? (pkt.isBurst ? 2.2 : 1.8) : isDone ? 0.9 : histFade > 0.01 ? 0.7 : 0.35;
    const alphaMult  = isAgentActive ? 1.0 : isDone ? 0.65 : histFade > 0.01 ? histFade * 0.75 : 0.55;
    const sizeMult   = isAgentActive ? 1.4 : 1.0;

    const rawT = ((t * pkt.speed * speedMult + pkt.phase) % 1 + 1) % 1;
    const paramT = pkt.dir === 1 ? rawT : 1 - rawT;
    const { x: px, y: py } = qbp(paramT, cx, cy, cpx, cpy, pos.x, pos.y);

    // Only draw if within canvas bounds
    ctx.save();
    const pSize = pkt.size * sizeMult;
    ctx.beginPath();
    ctx.arc(px, py, pSize, 0, Math.PI*2);
    ctx.fillStyle = pkt.isBurst ? '#FFFFFF' : condColor;
    ctx.shadowColor = condColor;
    ctx.shadowBlur = pkt.isBurst ? 24 : isAgentActive ? 18 : 8;
    ctx.globalAlpha = pkt.alpha * alphaMult;
    ctx.fill();
    // Inner white core for big packets
    if (pkt.isBurst || pSize > 4) {
      ctx.beginPath();
      ctx.arc(px, py, pSize * 0.38, 0, Math.PI*2);
      ctx.fillStyle = '#FFFFFF';
      ctx.globalAlpha = pkt.alpha * alphaMult * 0.9;
      ctx.fill();
    }
    ctx.restore();
  });
}

// ── Component ──────────────────────────────────────────────────────────────

interface AgentOrbState { role: string; status: AgentStatus; }

export default function DashboardPage() {
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

  // Conduit execution history (role → animTime when agent became inactive)
  const conduitHistoryRef  = useRef<Record<string, number>>({});
  const prevActiveAgentRef = useRef<string | null>(null);

  // ── Pre-seeded stable data ──

  const packetPool = useMemo((): Record<string, Packet[]> => {
    const pool: Record<string, Packet[]> = {};
    AGENT_ROLES.forEach((role, ri) => {
      const pkts: Packet[] = [];
      // 3 idle packets (slow, dim, core→agent)
      for (let i = 0; i < 3; i++) {
        pkts.push({ phase: i/3, speed: 0.038 + seed(ri,i)*0.025, size: 2.0 + seed(ri,i+10)*1.2, alpha: 0.17 + seed(ri,i+20)*0.10, dir: 1, isBurst: false });
      }
      // 5 active packets (fast, bright, core→agent)
      for (let i = 0; i < 5; i++) {
        pkts.push({ phase: i/5 + 0.1, speed: 0.28 + seed(ri,i+30)*0.30, size: 3.2 + seed(ri,i+40)*2.4, alpha: 0.68 + seed(ri,i+50)*0.32, dir: 1, isBurst: false });
      }
      // 3 return packets (agent→core)
      for (let i = 0; i < 3; i++) {
        pkts.push({ phase: i/3 + 0.5, speed: 0.18 + seed(ri,i+60)*0.14, size: 2.4 + seed(ri,i+70)*1.4, alpha: 0.38 + seed(ri,i+80)*0.22, dir: -1, isBurst: false });
      }
      // 1 burst (large, fast, rare phase)
      pkts.push({ phase: seed(ri,90), speed: 0.95, size: 9.5, alpha: 1.0, dir: 1, isBurst: true });
      pool[role] = pkts;
    });
    return pool;
  }, []);

  const neuralNodes = useMemo((): NeuralNode[] =>
    Array.from({ length: 44 }, (_, i) => ({
      bx: seed(i,0), by: seed(i,1),
      px: 0, py: 0,
      ampX: 0.025 + seed(i,2)*0.035, ampY: 0.025 + seed(i,3)*0.035,
      spd: 0.006 + seed(i,4)*0.008, ph: seed(i,5)*Math.PI*2,
      s: 0.8 + seed(i,6)*2.0, a: 0.055 + seed(i,7)*0.11,
      twinkle: seed(i,8) > 0.68,
    })), []);

  const dustParticles = useMemo((): Dust[] =>
    Array.from({ length: 68 }, (_, i) => ({
      bx: seed(i,10), by: seed(i,11),
      vx: (seed(i,12)-0.5)*0.000022, vy: (seed(i,13)-0.5)*0.000022,
      s: 0.45 + seed(i,14)*1.15, a: 0.035 + seed(i,15)*0.09,
    })), []);

  // Measure workspace
  useEffect(() => {
    const measure = () => {
      if (workspaceRef.current) {
        setDimensions({ width: workspaceRef.current.clientWidth, height: workspaceRef.current.clientHeight });
      }
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (workspaceRef.current) ro.observe(workspaceRef.current);
    return () => ro.disconnect();
  }, []);

  // Reactive reactor size
  const reactorSize = useMemo(() => {
    const t = Math.min(dimensions.width * 0.52, dimensions.height * 0.78);
    return Math.max(340, Math.min(520, Math.round(t)));
  }, [dimensions]);

  const cx = dimensions.width / 2;
  const cy = dimensions.height / 2;

  const orbitScale = useMemo(() => {
    const avail = Math.min(dimensions.width * 0.44, dimensions.height * 0.44);
    return Math.min(0.88, avail / BASE_ORBIT_RADIUS);
  }, [dimensions]);

  const scaledOrbit = BASE_ORBIT_RADIUS * orbitScale;

  // API poll
  const { data: summary } = useQuery({
    queryKey: ['mission-control-summary'],
    queryFn: missionControlApi.getSummary,
    refetchInterval: 2000,
  });

  const allAgents: AgentConfig[] = useMemo(
    () => (summary ? Object.values({ ...summary.agents.builtin, ...summary.agents.custom }) : []),
    [summary],
  );

  // State sync + history tracking
  useEffect(() => {
    if (!summary) return;
    setLastUpdate(new Date());

    const stateMap: Record<string,ExecutionState> = {
      idle:'idle',thinking:'thinking',planning:'planning',researching:'researching',
      calling_provider:'calling_provider',streaming:'streaming',completed:'completed',
      failed:'failed',cancelled:'cancelled',
    };
    setCoreState(stateMap[summary.orchestrator?.status||'idle']??'idle');

    const execs = summary.active_executions || [];
    const exec = execs.length > 0
      ? [...execs].sort((a,b) => new Date(b.started_at||0).getTime()-new Date(a.started_at||0).getTime())[0]
      : null;

    // Track execution history
    const currentAgent = exec?.current_agent ?? null;
    if (prevActiveAgentRef.current && prevActiveAgentRef.current !== currentAgent) {
      conduitHistoryRef.current[prevActiveAgentRef.current] = animTimeRef.current;
    }
    prevActiveAgentRef.current = currentAgent;

    setActiveExecution(exec);

    const allMap = { ...summary.agents.builtin, ...summary.agents.custom };
    const ns: Record<string,AgentOrbState> = {};
    Object.keys(allMap).forEach(role => { ns[role] = { role, status: 'idle' }; });
    if (exec?.current_agent && ns[exec.current_agent]) {
      const sMap: Record<string,AgentStatus> = {
        idle:'idle',thinking:'thinking',planning:'thinking',researching:'running',
        calling_provider:'running',streaming:'streaming',completed:'completed',failed:'failed',cancelled:'failed',
      };
      ns[exec.current_agent] = { role: exec.current_agent, status: sMap[exec.state]??'running' };
    }
    setAgentStates(ns);
  }, [summary]);

  // Compute node position: fixed angle + slow orbital drift + hover oscillation
  const getNodePos = useCallback((role: string): { x: number; y: number } => {
    const layout = AGENT_LAYOUT[role];
    const angleDeg = layout?.angleDeg ?? 0;
    const orbitDriftDeg = animTimeRef.current * 0.22; // ~1.3°/min drift
    const rad = ((angleDeg - 90 + orbitDriftDeg) * Math.PI) / 180;
    const hover = Math.sin(animTimeRef.current * 0.55 + angleDeg * 0.055) * 5;
    return {
      x: cx + (scaledOrbit + hover) * Math.cos(rad),
      y: cy + (scaledOrbit + hover) * Math.sin(rad),
    };
  }, [cx, cy, scaledOrbit]);

  // Canvas render
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
    const isAnyActive = activeExecution != null;
    const activeRole  = activeExecution?.current_agent ?? null;

    // Build current node positions for cortex mesh
    const nodePositions: Record<string,{x:number;y:number}> = {};
    AGENT_ROLES.forEach(role => { nodePositions[role] = getNodePos(role); });

    // ── Background layers ──
    drawBackground(ctx, W, H, t, neuralNodes, dustParticles, r, g, b);

    // ── Orbital rail ──
    drawOrbitalRail(ctx, cx, cy, scaledOrbit, t, r, g, b);

    // ── Cortex mesh ──
    drawCortexMesh(ctx, nodePositions, r, g, b);

    // ── Core → Agent conduits ──
    AGENT_ROLES.forEach(role => {
      const pos = nodePositions[role];
      if (!pos) return;
      const isAgentActive = activeRole === role;
      const agentSt = agentStates[role]?.status ?? 'idle';

      // Compute history fade
      const histTime = conduitHistoryRef.current[role];
      const histFade = histTime ? Math.max(0, 1 - (t - histTime) / 5) : 0;

      const pkts = packetPool[role] ?? [];
      drawConduit(ctx, cx, cy, pos, pkts, t, coreColor, isAgentActive, histFade, isAnyActive, agentSt);
    });

    // ── Vignette (final overlay) ──
    drawVignette(ctx, W, H);
  }, [neuralNodes, dustParticles, cx, cy, scaledOrbit, coreState, agentStates, activeExecution, getNodePos, packetPool]);

  // Single rAF loop
  useEffect(() => {
    const loop = () => {
      animTimeRef.current += 0.022;
      drawCanvas();
      forceRender(n => n + 1);
      animFrameRef.current = requestAnimationFrame(loop);
    };
    animFrameRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [drawCanvas]);

  // Telemetry
  const elapsedSec     = activeExecution?.elapsed_ms ? (activeExecution.elapsed_ms/1000).toFixed(1) : '0.0';
  const tokenCount     = activeExecution?.total_tokens ?? 0;
  const tokensFormatted = tokenCount >= 1000 ? `${(tokenCount/1000).toFixed(1)}K` : String(tokenCount);
  const isActive       = activeExecution != null;

  return (
    <div className="h-screen w-screen bg-background overflow-hidden relative select-none flex flex-col font-sans">

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
            <motion.span className="w-1.5 h-1.5 rounded-full bg-accent" animate={{ opacity:[0.35,1,0.35] }} transition={{ duration:1.6, repeat:Infinity }} />
            <span className="text-[8px] font-mono font-bold text-accent/85 tracking-[0.18em] uppercase">Core Armed</span>
          </div>
          <span className="text-[8px] font-mono text-white/22 hidden lg:block">{lastUpdate.toLocaleTimeString()}</span>
        </div>
      </header>

      {/* ── Main Workspace ── */}
      <div className="flex-1 flex overflow-hidden relative z-10">

        {/* Center Visualization */}
        <div ref={workspaceRef} className="flex-[65] relative min-w-0 h-full overflow-hidden">

          {/* Conduit + background canvas */}
          <canvas
            ref={conduitCanvasRef}
            width={dimensions.width}
            height={dimensions.height}
            className="absolute inset-0 w-full h-full pointer-events-none z-0"
          />

          {/* Nexus Reactor Core */}
          <div
            className="absolute z-10 pointer-events-none"
            style={{ left: cx, top: cy, transform: 'translate(-50%,-50%)' }}
          >
            <NexusReactorCore
              state={coreState}
              activeExecutions={summary?.orchestrator?.active_executions}
              reactorSize={reactorSize}
            />
          </div>

          {/* Agent Processor docks */}
          {allAgents.map(agent => {
            const role = agent.role;
            const layout = AGENT_LAYOUT[role];
            if (!layout) return null;
            const pos = getNodePos(role);
            const agentIsActive = activeExecution?.current_agent === role;
            const dScale = depthScale(layout.angleDeg);
            const dBlur  = depthBlur(layout.angleDeg);

            return (
              <AgentProcessor
                key={role}
                role={role}
                config={agent}
                status={agentStates[role]?.status ?? 'idle'}
                isActive={agentIsActive}
                position={pos}
                dimmed={isActive && !agentIsActive}
                depthScale={dScale}
                depthBlur={dBlur}
                currentTask={agentIsActive ? activeExecution?.current_task : null}
                elapsedMs={agentIsActive ? activeExecution?.elapsed_ms : undefined}
              />
            );
          })}
        </div>

        {/* Right: Event Timeline */}
        <aside className="flex-[35] flex flex-col bg-surface/18 border-l border-white/[0.05] backdrop-blur-md z-10 overflow-hidden min-w-[300px] max-w-[420px]">
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/[0.05] bg-white/[0.03] shrink-0">
            <Terminal size={14} className="text-warning" />
            <span className="text-[9px] font-mono font-bold uppercase tracking-[0.18em] text-warning/85">Event Timeline</span>
          </div>
          <div className="flex-1 overflow-hidden p-3">
            <ExecutionTimeline events={summary?.recent_events ?? []} maxItems={50} />
          </div>
        </aside>
      </div>

      {/* Bottom: Execution Graph */}
      <footer className="h-48 bg-surface/18 border-t border-white/[0.05] backdrop-blur-md z-10 flex flex-col overflow-hidden shrink-0">
        <div className="flex items-center gap-2 px-5 py-2 border-b border-white/[0.05] bg-white/[0.03] shrink-0">
          <GitBranch size={13} className="text-success" />
          <span className="text-[9px] font-mono font-bold uppercase tracking-[0.18em] text-success/85">Execution Graph</span>
        </div>
        <div className="flex-1 overflow-auto p-3">
          <ExecutionGraph execution={activeExecution} />
        </div>
      </footer>
    </div>
  );
}