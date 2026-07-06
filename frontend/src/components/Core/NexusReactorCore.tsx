import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import type { ExecutionState } from '../../types/mission-control';

interface NexusReactorCoreProps {
  state?: ExecutionState;
  activeExecutions?: number;
  reactorSize?: number;
}

interface Theme {
  r: number; g: number; b: number;
  primary: string;
  pulseHz: number;    // breathing cycles per second
  ringSpeed: number;  // ring rotation speed multiplier
  particleSpeed: number;
  plasmaDensity: number; // 1-8
  cogLabel: string;
  scanSpeed: number;  // radar sweep speed
}

const THEMES: Record<string, Theme> = {
  idle:             { r:0,   g:212, b:255, primary:'#00D4FF', pulseHz:0.28, ringSpeed:0.50, particleSpeed:0.50, plasmaDensity:2, cogLabel:'◆ STANDBY ◆ NEURAL IDLE ◆ DORMANT ◆ AWAITING INPUT ◆ NEXUS READY ◆', scanSpeed:0.4 },
  thinking:         { r:168, g:85,  b:247, primary:'#A855F7', pulseHz:0.90, ringSpeed:2.20, particleSpeed:2.50, plasmaDensity:5, cogLabel:'◆ NEURAL PROCESSING ◆ COGNITION ACTIVE ◆ THOUGHT SYNTHESIS ◆ DEEP COMPUTE ◆', scanSpeed:1.8 },
  planning:         { r:59,  g:130, b:246, primary:'#3B82F6', pulseHz:0.60, ringSpeed:1.50, particleSpeed:1.80, plasmaDensity:4, cogLabel:'◆ STRATEGIC PLANNING ◆ ROUTE OPTIMIZATION ◆ GOAL ALIGNMENT ◆ TASK MAPPING ◆', scanSpeed:1.2 },
  researching:      { r:0,   g:212, b:255, primary:'#00D4FF', pulseHz:0.80, ringSpeed:2.00, particleSpeed:2.20, plasmaDensity:5, cogLabel:'◆ DATA ACQUISITION ◆ KNOWLEDGE SYNTHESIS ◆ SCAN ACTIVE ◆ INDEXING ◆', scanSpeed:1.5 },
  calling_provider: { r:236, g:72,  b:153, primary:'#EC4899', pulseHz:1.20, ringSpeed:3.50, particleSpeed:3.20, plasmaDensity:7, cogLabel:'◆ INFERENCE ENGINE ◆ PROVIDER HANDSHAKE ◆ MODEL LINK ACTIVE ◆ TRANSMITTING ◆', scanSpeed:2.5 },
  streaming:        { r:56,  g:189, b:248, primary:'#38BDF8', pulseHz:1.60, ringSpeed:4.00, particleSpeed:3.80, plasmaDensity:8, cogLabel:'◆ RESPONSE SYNTHESIS ◆ TOKEN STREAM ACTIVE ◆ OUTPUT READY ◆ STREAMING ◆', scanSpeed:3.0 },
  completed:        { r:0,   g:255, b:149, primary:'#00FF95', pulseHz:0.35, ringSpeed:0.80, particleSpeed:0.80, plasmaDensity:3, cogLabel:'◆ TASK COMPLETE ◆ READY FOR NEXT ◆ NEURAL RESET ◆ STANDBY ◆', scanSpeed:0.6 },
  failed:           { r:255, g:77,  b:103, primary:'#FF4D67', pulseHz:1.80, ringSpeed:5.00, particleSpeed:5.00, plasmaDensity:9, cogLabel:'◆ EXECUTION ERROR ◆ FAULT DETECTED ◆ RECOVERY MODE ◆ ALERT ◆', scanSpeed:4.0 },
  cancelled:        { r:148, g:163, b:184, primary:'#94A3B8', pulseHz:0.20, ringSpeed:0.30, particleSpeed:0.30, plasmaDensity:1, cogLabel:'◆ CANCELLED ◆ STANDBY ◆ IDLE ◆', scanSpeed:0.3 },
};

// ── Helpers ──
function lerp(a: number, b: number, t: number): number { return a + (b - a) * t; }

function drawArcText(
  ctx: CanvasRenderingContext2D,
  text: string, cx: number, cy: number, r: number,
  startAngle: number, color: string, alpha: number, fontSize: number,
) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.font = `bold ${fontSize}px "Courier New", monospace`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const spacing = 0.085;
  const half = (text.length * spacing) / 2;
  for (let i = 0; i < text.length; i++) {
    const a = startAngle + i * spacing - half;
    ctx.save();
    ctx.translate(cx + r * Math.cos(a), cy + r * Math.sin(a));
    ctx.rotate(a + Math.PI / 2);
    ctx.fillText(text[i], 0, 0);
    ctx.restore();
  }
  ctx.restore();
}

interface Particle {
  a: number; d: number; speed: number; size: number; alpha: number; dir: 1 | -1;
}

function makeParticles(n: number): Particle[] {
  return Array.from({ length: n }, () => ({
    a: Math.random() * Math.PI * 2,
    d: Math.random() * 115 + 8,
    speed: Math.random() * 1.4 + 0.4,
    size: Math.random() * 2.2 + 0.5,
    alpha: Math.random() * 0.85 + 0.15,
    dir: Math.random() > 0.45 ? -1 : 1,
  }));
}

interface Star { x: number; y: number; s: number; a: number; baseAngle: number; r: number; }

function makeStars(n: number, cx: number, cy: number, minR: number, maxR: number): Star[] {
  return Array.from({ length: n }, () => {
    const angle = Math.random() * Math.PI * 2;
    const r = minR + Math.random() * (maxR - minR);
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle), s: Math.random() * 2 + 0.5, a: Math.random() * 0.7 + 0.1, baseAngle: angle, r };
  });
}

export function NexusReactorCore({ state = 'idle', activeExecutions, reactorSize = 460 }: NexusReactorCoreProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const themeRef = useRef<Theme>(THEMES[state] ?? THEMES.idle);
  const stateRef = useRef<ExecutionState>(state);

  useEffect(() => {
    stateRef.current = state;
    themeRef.current = THEMES[state] ?? THEMES.idle;
  }, [state]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const cx = W / 2, cy = H / 2;

    // Pre-built objects
    const particles = makeParticles(110);
    const stars = makeStars(65, cx, cy, 185, cx - 4);

    let t = 0;
    let animId: number;

    // ── Lightning arc state ──
    interface Arc { pts: { x: number; y: number }[]; alpha: number; }
    const arcs: Arc[] = [];
    let nextArcTime = 2.5;

    const frame = () => {
      t += 0.018;
      const T = themeRef.current;
      const { r, g, b } = T;
      ctx.clearRect(0, 0, W, H);

      // ── L0: Outer Atmospheric Bloom ──
      const atmo = ctx.createRadialGradient(cx, cy, 0, cx, cy, cx * 0.45);
      atmo.addColorStop(0,   `rgba(${r},${g},${b},0.09)`);
      atmo.addColorStop(0.45,`rgba(${r},${g},${b},0.04)`);
      atmo.addColorStop(0.75,`rgba(${r},${g},${b},0.015)`);
      atmo.addColorStop(1,   'rgba(0,0,0,0)');
      ctx.fillStyle = atmo;
      ctx.fillRect(0, 0, W, H);

      // ── L1: Constellation ring (slowly rotating dots) ──
      const starAngleOffset = t * 0.018;
      stars.forEach(star => {
        const sa = star.baseAngle + starAngleOffset;
        const sx = cx + star.r * Math.cos(sa);
        const sy = cy + star.r * Math.sin(sa);
        ctx.beginPath();
        ctx.arc(sx, sy, star.s, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r},${g},${b},${star.a * 0.7})`;
        ctx.fill();
      });
      // Connect close neighbours with faint lines
      for (let i = 0; i < stars.length - 1; i += 3) {
        const sa1 = stars[i].baseAngle + starAngleOffset;
        const sa2 = stars[i + 1].baseAngle + starAngleOffset;
        ctx.beginPath();
        ctx.moveTo(cx + stars[i].r * Math.cos(sa1), cy + stars[i].r * Math.sin(sa1));
        ctx.lineTo(cx + stars[i + 1].r * Math.cos(sa2), cy + stars[i + 1].r * Math.sin(sa2));
        ctx.strokeStyle = `rgba(${r},${g},${b},0.04)`;
        ctx.lineWidth = 0.6;
        ctx.stroke();
      }

      // ── L2: Radar scan sweep ──
      const sweepAngle = t * T.scanSpeed * 0.9;
      // Draw arc sector for sweep
      ctx.save();
      ctx.translate(cx, cy);
      const sweepArc = ctx.createRadialGradient(0, 0, 0, 0, 0, 165);
      sweepArc.addColorStop(0,    `rgba(${r},${g},${b},0.22)`);
      sweepArc.addColorStop(0.65, `rgba(${r},${g},${b},0.08)`);
      sweepArc.addColorStop(1,    'rgba(0,0,0,0)');
      ctx.fillStyle = sweepArc;
      ctx.globalAlpha = 0.55;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, 165, sweepAngle - 0.45, sweepAngle, false);
      ctx.closePath();
      ctx.fill();
      // Bright leading edge
      ctx.globalAlpha = 1;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(Math.cos(sweepAngle) * 165, Math.sin(sweepAngle) * 165);
      ctx.strokeStyle = `rgba(${r},${g},${b},0.7)`;
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.restore();

      // ── L3: Outer halo ring ──
      ctx.beginPath();
      ctx.arc(cx, cy, 165, 0, Math.PI * 2);
      const haloGrad = ctx.createRadialGradient(cx, cy, 160, cx, cy, 170);
      haloGrad.addColorStop(0, `rgba(${r},${g},${b},0.0)`);
      haloGrad.addColorStop(0.5, `rgba(${r},${g},${b},0.5)`);
      haloGrad.addColorStop(1, `rgba(${r},${g},${b},0.0)`);
      ctx.strokeStyle = `rgba(${r},${g},${b},0.45)`;
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // ── L4: Scanner ticks (rotating clockwise) ──
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(t * 0.35 * T.ringSpeed);
      for (let i = 0; i < 32; i++) {
        const a = (i / 32) * Math.PI * 2;
        const major = i % 4 === 0;
        const r0 = 158, r1 = major ? 174 : 165;
        ctx.beginPath();
        ctx.moveTo(Math.cos(a) * r0, Math.sin(a) * r0);
        ctx.lineTo(Math.cos(a) * r1, Math.sin(a) * r1);
        ctx.strokeStyle = `rgba(${r},${g},${b},${major ? 0.65 : 0.22})`;
        ctx.lineWidth = major ? 1.8 : 0.9;
        ctx.stroke();
      }
      ctx.restore();

      // ── L5: Segmented ring A (rotating CW) ──
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(t * 0.12 * T.ringSpeed);
      ctx.beginPath();
      ctx.arc(0, 0, 145, 0, Math.PI * 2);
      ctx.setLineDash([55, 14, 8, 14]);
      ctx.strokeStyle = `rgba(${r},${g},${b},0.5)`;
      ctx.lineWidth = 2.0;
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();

      // ── L6: Segmented ring B (counter-rotating) ──
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(-t * 0.09 * T.ringSpeed);
      ctx.beginPath();
      ctx.arc(0, 0, 128, 0, Math.PI * 2);
      ctx.setLineDash([7, 22]);
      ctx.strokeStyle = `rgba(${r},${g},${b},0.32)`;
      ctx.lineWidth = 1.4;
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();

      // ── L7: Energy pulse ring (breathing) ──
      const breathAlpha = 0.30 + 0.38 * (0.5 + 0.5 * Math.sin(t * T.pulseHz * Math.PI * 2));
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, 110, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(${r},${g},${b},${breathAlpha})`;
      ctx.lineWidth = 2.8;
      ctx.shadowColor = T.primary;
      ctx.shadowBlur = 12;
      ctx.stroke();
      ctx.shadowBlur = 0;
      ctx.restore();

      // ── L8: Hexagonal lattice (dual-hex, rotating) ──
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(t * 0.06 * T.ringSpeed);
      // Outer hex
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const a = (i / 6) * Math.PI * 2 - Math.PI / 6;
        if (i === 0) ctx.moveTo(Math.cos(a) * 92, Math.sin(a) * 92);
        else ctx.lineTo(Math.cos(a) * 92, Math.sin(a) * 92);
      }
      ctx.closePath();
      ctx.strokeStyle = `rgba(${r},${g},${b},0.22)`;
      ctx.lineWidth = 1.2;
      ctx.stroke();
      // Spokes
      for (let i = 0; i < 6; i++) {
        const a = (i / 6) * Math.PI * 2 - Math.PI / 6;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(Math.cos(a) * 92, Math.sin(a) * 92);
        ctx.strokeStyle = `rgba(${r},${g},${b},0.08)`;
        ctx.lineWidth = 0.7;
        ctx.stroke();
      }
      // Inner hex (counter-rotate)
      ctx.rotate(-t * 0.11 * T.ringSpeed);
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const a = (i / 6) * Math.PI * 2;
        if (i === 0) ctx.moveTo(Math.cos(a) * 68, Math.sin(a) * 68);
        else ctx.lineTo(Math.cos(a) * 68, Math.sin(a) * 68);
      }
      ctx.closePath();
      ctx.strokeStyle = `rgba(${r},${g},${b},0.15)`;
      ctx.lineWidth = 0.9;
      ctx.stroke();
      ctx.restore();

      // ── L9: Plasma chamber (clipped) ──
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, 80, 0, Math.PI * 2);
      ctx.clip();
      ctx.globalCompositeOperation = 'screen';
      const density = Math.min(8, T.plasmaDensity);
      for (let l = 0; l < density; l++) {
        const ao = t * (0.55 + l * 0.18) + l;
        const ox = Math.cos(ao) * 16;
        const oy = Math.sin(ao) * 16;
        const plasma = ctx.createRadialGradient(cx + ox, cy + oy, 3, cx, cy, 78 - l * 5);
        plasma.addColorStop(0, T.primary);
        plasma.addColorStop(0.35, `rgba(${r},${g},${b},0.35)`);
        plasma.addColorStop(1, 'rgba(0,0,0,0.92)');
        ctx.fillStyle = plasma;
        ctx.beginPath();
        ctx.arc(cx, cy, 80, 0, Math.PI * 2);
        ctx.fill();
      }
      // Energy rotation streaks inside plasma
      for (let sk = 0; sk < 3; sk++) {
        const sa = t * (0.4 + sk * 0.3) + sk * 2.1;
        ctx.beginPath();
        ctx.arc(0, 0, 0, sa, sa + 0.65);
        ctx.arc(cx, cy, 60 - sk * 10, sa, sa + 0.65);
        ctx.strokeStyle = `rgba(${r},${g},${b},${0.15 + sk * 0.05})`;
        ctx.lineWidth = 2.5 - sk * 0.5;
        ctx.stroke();
      }
      ctx.globalCompositeOperation = 'source-over';
      ctx.restore();

      // ── L9b: Heat shimmer (oscillating bands inside plasma) ──
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, 80, 0, Math.PI * 2);
      ctx.clip();
      for (let row = 0; row < 5; row++) {
        const yOff = Math.sin(t * 2.2 + row * 1.4) * 5;
        const sy = cy - 70 + row * 32 + yOff;
        const shimmer = ctx.createLinearGradient(cx - 80, sy, cx + 80, sy + 6);
        shimmer.addColorStop(0, 'rgba(255,255,255,0)');
        shimmer.addColorStop(0.4, `rgba(${r},${g},${b},0.07)`);
        shimmer.addColorStop(0.6, `rgba(${r},${g},${b},0.04)`);
        shimmer.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = shimmer;
        ctx.fillRect(cx - 80, sy, 160, 6);
      }
      ctx.restore();

      // ── L9c: Lightning arcs (occasional, inside plasma) ──
      if (t > nextArcTime) {
        nextArcTime = t + 1.5 / Math.max(1, T.plasmaDensity * 0.5) + Math.random() * 2.5;
        const sa2 = Math.random() * Math.PI * 2;
        const arcPts: { x: number; y: number }[] = [];
        for (let i = 0; i < 7; i++) {
          const aa = sa2 + (i / 6) * (0.7 + Math.random() * 1.0);
          const rr = 12 + Math.random() * 58;
          arcPts.push({ x: Math.cos(aa) * (rr + (Math.random() - 0.5) * 10), y: Math.sin(aa) * (rr + (Math.random() - 0.5) * 10) });
        }
        arcs.push({ pts: arcPts, alpha: 0.88 });
      }
      arcs.forEach(arc => { arc.alpha -= 0.03; });
      while (arcs.length > 0 && arcs[0].alpha <= 0.01) arcs.shift();
      if (arcs.length > 0) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.beginPath();
        ctx.arc(0, 0, 80, 0, Math.PI * 2);
        ctx.clip();
        arcs.forEach(arc => {
          ctx.beginPath();
          ctx.moveTo(arc.pts[0].x, arc.pts[0].y);
          arc.pts.slice(1).forEach(pt => ctx.lineTo(pt.x, pt.y));
          ctx.strokeStyle = `rgba(220,235,255,${arc.alpha * 0.85})`;
          ctx.lineWidth = 0.65 + arc.alpha * 0.45;
          ctx.shadowColor = '#FFFFFF';
          ctx.shadowBlur = 5;
          ctx.stroke();
          ctx.shadowBlur = 0;
        });
        ctx.restore();
      }

      // ── L10: Particle turbulence ──
      ctx.globalCompositeOperation = 'screen';
      particles.forEach(p => {
        p.a += 0.007 * T.particleSpeed * (p.dir === 1 ? 1.1 : 0.9);
        p.d += p.dir * p.speed * T.particleSpeed * 0.35;
        if (p.d < 8)  { p.d = 125; p.a = Math.random() * Math.PI * 2; }
        if (p.d > 130) { p.d = 8;  p.a = Math.random() * Math.PI * 2; }
        const px = cx + p.d * Math.cos(p.a);
        const py = cy + p.d * Math.sin(p.a);
        ctx.beginPath();
        ctx.arc(px, py, p.size, 0, Math.PI * 2);
        ctx.fillStyle = T.primary;
        ctx.shadowColor = T.primary;
        ctx.shadowBlur = 6;
        ctx.globalAlpha = p.alpha * lerp(1, 0.1, p.d / 132);
        ctx.fill();
        ctx.shadowBlur = 0;
      });
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'source-over';

      // ── L11: Cognitive state ring (arc text) ──
      const textAngle = -t * 0.18 * T.scanSpeed - Math.PI / 2;
      drawArcText(ctx, T.cogLabel, cx, cy, 178, textAngle, T.primary, 0.42, 7.5);

      // Heuristically detect speaking / streaming
      let speakerMod = 0;
      if (stateRef.current === 'streaming' || stateRef.current === 'calling_provider') {
        speakerMod = Math.max(0, Math.sin(t * 12) * Math.cos(t * 5.5) * 6 + Math.sin(t * 26) * 3);
      }

      // ── L12: Energy nucleus ──
      const nucSize = 20 + 3 * Math.sin(t * T.pulseHz * Math.PI * 2) + speakerMod;
      const nucGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, nucSize * 1.8);
      nucGlow.addColorStop(0, '#FFFFFF');
      nucGlow.addColorStop(0.2, T.primary);
      nucGlow.addColorStop(0.6, `rgba(${r},${g},${b},0.25)`);
      nucGlow.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = nucGlow;
      ctx.shadowColor = '#FFFFFF';
      ctx.shadowBlur = 22;
      ctx.beginPath();
      ctx.arc(cx, cy, nucSize, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      // ── L13: Sonar pulse wave (state-driven) ──
      const pulsePhase = (t * T.pulseHz) % 1;
      const pulseR = 60 + pulsePhase * 110 + speakerMod * 1.5;
      const pulseAlpha = (1 - pulsePhase) * 0.55;
      if (pulseAlpha > 0.02) {
        ctx.beginPath();
        ctx.arc(cx, cy, pulseR, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${r},${g},${b},${pulseAlpha})`;
        ctx.lineWidth = 1.8;
        ctx.stroke();
      }

      // ── L14: Volumetric core bloom (final overlay) ──
      ctx.globalCompositeOperation = 'screen';
      const bloom = ctx.createRadialGradient(cx, cy, 0, cx, cy, 35);
      bloom.addColorStop(0, `rgba(${r},${g},${b},0.55)`);
      bloom.addColorStop(0.4, `rgba(${r},${g},${b},0.18)`);
      bloom.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = bloom;
      ctx.beginPath();
      ctx.arc(cx, cy, 35, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalCompositeOperation = 'source-over';

      animId = requestAnimationFrame(frame);
    };

    frame();
    return () => cancelAnimationFrame(animId);
  }, [reactorSize]);

  const T = THEMES[state] ?? THEMES.idle;
  const sz = reactorSize;

  return (
    <div className="relative flex items-center justify-center select-none" style={{ width: sz, height: sz }}>
      {/* Outer glass shell */}
      <motion.div
        className="relative rounded-full border overflow-hidden"
        style={{
          width: sz, height: sz,
          borderColor: `${T.primary}40`,
          background: 'radial-gradient(circle at 42% 38%, rgba(0,35,55,0.45) 0%, rgba(0,0,15,0.92) 80%)',
        }}
        animate={{
          boxShadow: [
            `0 0 24px ${T.primary}28, 0 0 50px ${T.primary}12, inset 0 0 16px ${T.primary}0A`,
            `0 0 36px ${T.primary}45, 0 0 70px ${T.primary}20, inset 0 0 24px ${T.primary}15`,
            `0 0 24px ${T.primary}28, 0 0 50px ${T.primary}12, inset 0 0 16px ${T.primary}0A`,
          ],
        }}
        transition={{ boxShadow: { duration: 1 / (T.pulseHz || 0.28), repeat: Infinity, ease: 'easeInOut' } }}
      >
        <canvas ref={canvasRef} width={sz} height={sz} className="absolute inset-0 w-full h-full" />
      </motion.div>

      {/* Bottom label */}
      <div className="absolute pointer-events-none" style={{ bottom: -36, left: '50%', transform: 'translateX(-50%)', whiteSpace: 'nowrap' }}>
        <motion.p
          className="text-[9px] font-mono font-bold uppercase tracking-[0.32em] text-center"
          style={{ color: T.primary }}
          animate={{ opacity: [0.5, 0.95, 0.5] }}
          transition={{ duration: 1 / (T.pulseHz || 0.28), repeat: Infinity, ease: 'easeInOut' }}
        >
          NEXUS REACTOR CORE
        </motion.p>
        {activeExecutions != null && activeExecutions > 0 && (
          <div className="flex items-center justify-center gap-1.5 mt-1">
            <motion.span className="w-1.5 h-1.5 rounded-full bg-success" animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity }} />
            <span className="text-[7.5px] font-mono text-success/75 uppercase tracking-widest">{activeExecutions} EXEC ACTIVE</span>
          </div>
        )}
      </div>
    </div>
  );
}
