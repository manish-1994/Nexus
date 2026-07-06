import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import type { ExecutionState } from '../../types/mission-control';

interface MissionControlCoreProps {
  state: ExecutionState;
  providerName?: string | null;
  model?: string | null;
  elapsedMs?: number;
  tokenCount?: number;
  activeExecutions?: number;
}

interface CoreStateTheme {
  color: string;
  glow: string;
  speedMultiplier: number;
  plasmaDensity: number;
  particleCount: number;
  mode: 'idle' | 'listening' | 'thinking' | 'speaking';
}

const THEMES: Record<string, CoreStateTheme> = {
  idle: {
    color: '#00D4FF',
    glow: 'rgba(0, 212, 255, 0.55)',
    speedMultiplier: 0.5,
    plasmaDensity: 3,
    particleCount: 25,
    mode: 'idle',
  },
  thinking: {
    color: '#A855F7',
    glow: 'rgba(168, 85, 247, 0.75)',
    speedMultiplier: 2.8,
    plasmaDensity: 5,
    particleCount: 45,
    mode: 'thinking',
  },
  planning: {
    color: '#3B82F6',
    glow: 'rgba(59, 130, 246, 0.65)',
    speedMultiplier: 1.6,
    plasmaDensity: 4,
    particleCount: 30,
    mode: 'thinking',
  },
  researching: {
    color: '#00D4FF',
    glow: 'rgba(0, 212, 255, 0.7)',
    speedMultiplier: 2.2,
    plasmaDensity: 4.5,
    particleCount: 35,
    mode: 'thinking',
  },
  calling_provider: {
    color: '#EC4899',
    glow: 'rgba(236, 72, 153, 0.8)',
    speedMultiplier: 3.0,
    plasmaDensity: 6,
    particleCount: 50,
    mode: 'speaking', // accelerates heartbeat
  },
  streaming: {
    color: '#3B82F6',
    glow: 'rgba(59, 130, 246, 0.85)',
    speedMultiplier: 3.8,
    plasmaDensity: 7,
    particleCount: 55,
    mode: 'speaking',
  },
  completed: {
    color: '#00FF95',
    glow: 'rgba(0, 255, 149, 0.8)',
    speedMultiplier: 0.8,
    plasmaDensity: 3,
    particleCount: 25,
    mode: 'listening', // gentle sonar expand
  },
  failed: {
    color: '#FF4D67',
    glow: 'rgba(255, 77, 103, 0.8)',
    speedMultiplier: 4.2,
    plasmaDensity: 8,
    particleCount: 60,
    mode: 'speaking',
  },
  cancelled: {
    color: '#94A3B8',
    glow: 'rgba(148, 163, 184, 0.45)',
    speedMultiplier: 0.4,
    plasmaDensity: 2,
    particleCount: 15,
    mode: 'idle',
  },
};

export function MissionControlCore({
  state = 'idle',
  activeExecutions,
}: MissionControlCoreProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const theme = THEMES[state] ?? THEMES.idle;

  const [burstScale, setBurstScale] = useState(1);
  const prevStateRef = useRef<ExecutionState>(state);

  useEffect(() => {
    if (state === 'completed' && prevStateRef.current !== 'completed') {
      setBurstScale(1.85);
      setTimeout(() => setBurstScale(1), 800);
    }
    prevStateRef.current = state;
  }, [state]);

  // Plasma swirl and volumetric particle field loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let time = 0;

    const particles: Array<{
      angle: number;
      distance: number;
      speed: number;
      size: number;
      alpha: number;
      direction: 'in' | 'out';
    }> = [];

    const init = () => {
      particles.length = 0;
      for (let i = 0; i < theme.particleCount; i++) {
        particles.push({
          angle: Math.random() * Math.PI * 2,
          distance: Math.random() * 100 + 15,
          speed: Math.random() * 0.95 + 0.45,
          size: Math.random() * 2.2 + 0.8,
          alpha: Math.random() * 0.85 + 0.15,
          direction: Math.random() > 0.45 ? 'in' : 'out',
        });
      }
    };
    init();

    const draw = () => {
      const w = canvas.width;
      const h = canvas.height;
      const cx = w / 2;
      const cy = h / 2;

      ctx.clearRect(0, 0, w, h);
      time += 0.035 * theme.speedMultiplier;

      // ── Layer: Plasma Chamber Gradient Fill ──
      const radius = 95;
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.clip();

      const layers = theme.plasmaDensity;
      for (let l = 0; l < layers; l++) {
        const angleOffset = time * (0.55 + l * 0.22);
        const shiftX = Math.cos(angleOffset) * 16;
        const shiftY = Math.sin(angleOffset) * 16;

        const grad = ctx.createRadialGradient(
          cx + shiftX, cy + shiftY, 5,
          cx, cy, radius - (l * 8)
        );
        grad.addColorStop(0, theme.color);
        grad.addColorStop(0.35, `${theme.color}45`);
        grad.addColorStop(1, 'rgba(0,0,0,0.92)');

        ctx.fillStyle = grad;
        ctx.globalCompositeOperation = 'screen';
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();

      // ── Layer: Volume Shimmer Micro Particles ──
      ctx.globalCompositeOperation = 'screen';
      particles.forEach((p) => {
        const travel = p.speed * theme.speedMultiplier;
        if (p.direction === 'in') {
          p.distance -= travel;
          if (p.distance < 10) {
            p.distance = 100 + Math.random() * 15;
            p.angle = Math.random() * Math.PI * 2;
          }
        } else {
          p.distance += travel;
          if (p.distance > 105) {
            p.distance = 12 + Math.random() * 12;
            p.angle = Math.random() * Math.PI * 2;
          }
        }

        p.angle += 0.006 * theme.speedMultiplier;

        const x = cx + p.distance * Math.cos(p.angle);
        const y = cy + p.distance * Math.sin(p.angle);

        ctx.beginPath();
        ctx.arc(x, y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = theme.color;
        ctx.shadowColor = theme.color;
        ctx.shadowBlur = 8;
        ctx.globalAlpha = p.alpha * (1 - p.distance / 110);
        ctx.fill();
        ctx.shadowBlur = 0;
      });
      ctx.globalAlpha = 1.0;

      animId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [theme, state]);

  // Breathing state multipliers (precise sci-fi timing curves)
  // Idle: slow pulse every 3s. Speaking: rapid heartbeat. Listening: sonar expand rings.
  const isSpeaking = theme.mode === 'speaking';
  const isListening = theme.mode === 'listening';
  const isThinking = theme.mode === 'thinking';

  const pulseScale = 
    isSpeaking ? [1.02, 1.18, 1.02] :
    isThinking ? [1.01, 1.13, 1.01] :
    [1.0, 1.06, 1.0];

  const duration =
    isSpeaking ? 0.55 :
    isThinking ? 0.75 :
    3.0; // Idle slow breathing every 3.0 seconds

  return (
    <div className="relative w-[500px] h-[500px] flex items-center justify-center select-none">
      
      {/* SVG Outer Reactor Layers */}
      <svg className="absolute w-full h-full overflow-visible" viewBox="0 0 200 200">
        <defs>
          <filter id="mc-reactor-bloom" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="9" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Layer 1: Outer Scanner Ring (Clockwise, segmented ticks) */}
        <motion.circle
          cx="100" cy="100" r="95"
          fill="none"
          stroke={theme.color}
          strokeWidth="0.8"
          strokeDasharray="4, 16, 8, 16"
          opacity="0.22"
          animate={{ rotate: 360 }}
          transition={{ duration: 45 / theme.speedMultiplier, repeat: Infinity, ease: 'linear' }}
          style={{ transformOrigin: '100px 100px' }}
        />

        {/* Layer 2: Rotating Segmented Ring (Counter-Clockwise Drive) */}
        <motion.circle
          cx="100" cy="100" r="85"
          fill="none"
          stroke={theme.color}
          strokeWidth="1.4"
          strokeDasharray="70, 20, 15, 25"
          opacity="0.35"
          filter="url(#mc-reactor-bloom)"
          animate={{ rotate: -360 }}
          transition={{ duration: 25 / theme.speedMultiplier, repeat: Infinity, ease: 'linear' }}
          style={{ transformOrigin: '100px 100px' }}
        />

        {/* Layer 3: Energy ring (Clockwise glow ring) */}
        <motion.circle
          cx="100" cy="100" r="76"
          fill="none"
          stroke={theme.color}
          strokeWidth="1.8"
          strokeDasharray="140, 30"
          opacity="0.5"
          filter="url(#mc-reactor-bloom)"
          animate={{ rotate: 360 }}
          transition={{ duration: 15 / theme.speedMultiplier, repeat: Infinity, ease: 'linear' }}
          style={{ transformOrigin: '100px 100px' }}
        />

        {/* Layer 4: Hexagonal Hologram frame (Counter-Clockwise Shield) */}
        <motion.polygon
          points="100,38 154,69 154,131 100,162 46,131 46,69"
          fill="none"
          stroke={theme.color}
          strokeWidth="1.2"
          opacity="0.25"
          animate={{ rotate: -360 }}
          transition={{ duration: 20 / theme.speedMultiplier, repeat: Infinity, ease: 'linear' }}
          style={{ transformOrigin: '100px 100px' }}
        />

        {/* Layer: Gentle expanding sonar rings during LISTENING mode */}
        {isListening && (
          <motion.circle
            cx="100" cy="100" r="42"
            fill="none"
            stroke={theme.color}
            strokeWidth="1.5"
            opacity="0.7"
            filter="url(#mc-reactor-bloom)"
            animate={{
              r: [42, 98, 42],
              opacity: [0.7, 0, 0.7],
            }}
            transition={{
              duration: 2.2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )}

        {/* Calibration node ticks */}
        <g stroke={theme.color} strokeWidth="1" opacity="0.4">
          <line x1="100" y1="6" x2="100" y2="16" />
          <line x1="100" y1="194" x2="100" y2="184" />
          <line x1="6" y1="100" x2="16" y2="100" />
          <line x1="194" y1="100" x2="184" y2="100" />
        </g>
      </svg>

      {/* Layer: Glass Inner Reactor Chamber + Nucleus (breathing scale anims) */}
      <motion.div
        className="w-[190px] h-[190px] rounded-full flex items-center justify-center relative z-10 border overflow-hidden"
        style={{
          boxShadow: `inset 0 0 50px ${theme.color}, 0 0 85px ${theme.glow}, 0 0 120px ${theme.glow}`,
          background: `radial-gradient(circle at 45% 45%, ${theme.color}35 0%, rgba(0,0,0,0.85) 85%)`,
          borderColor: theme.color,
          borderWidth: 1.5,
        }}
        animate={{
          scale: [pulseScale[0] * burstScale, pulseScale[1] * burstScale, pulseScale[2] * burstScale],
        }}
        transition={{
          duration,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        {/* Swirling Plasma Canvas */}
        <canvas
          ref={canvasRef}
          width={220}
          height={220}
          className="absolute inset-0 w-full h-full rounded-full pointer-events-none"
        />

        {/* Bright White Energy Nucleus */}
        <div
          className="absolute w-6 h-6 rounded-full z-20"
          style={{
            background: '#FFFFFF',
            boxShadow: `0 0 22px ${theme.color}, 0 0 45px ${theme.color}, 0 0 70px ${theme.color}`,
          }}
        />
      </motion.div>

      {/* Core status labeling */}
      <div className="absolute bottom-1.5 left-1/2 -translate-x-1/2 text-center space-y-0.5 z-25 font-mono">
        <motion.h3
          className="text-[10px] uppercase tracking-[0.3em] font-bold drop-shadow-md"
          style={{ color: theme.color }}
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration, repeat: Infinity, ease: 'easeInOut' }}
        >
          NEXUS REACTOR CORE
        </motion.h3>
        <motion.p
          className="text-[8px] uppercase tracking-widest font-bold font-label"
          style={{ color: theme.color, opacity: 0.5 }}
          key={state}
          initial={{ opacity: 0, y: 3 }}
          animate={{ opacity: 0.5, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          MODE: {theme.mode.toUpperCase()}
        </motion.p>
      </div>

      {activeExecutions != null && activeExecutions > 0 && (
        <div className="absolute top-1/2 -translate-y-1/2 right-[18px] flex items-center gap-1.5 px-2 py-0.5 bg-success/15 border border-success/30 rounded text-[8px] font-bold text-success uppercase tracking-widest font-mono">
          <span className="w-1 h-1 rounded-full bg-success animate-pulse" />
          <span>{activeExecutions} ACTIVE</span>
        </div>
      )}
    </div>
  );
}