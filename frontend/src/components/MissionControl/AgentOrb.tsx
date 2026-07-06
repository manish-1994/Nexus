import { motion } from 'framer-motion';
import { springs } from '../../styles/motion';
import type { AgentStatus, AgentConfig } from '../../types/mission-control';

interface HolographicGlyphProps {
  role: string;
  color: string;
  glow: string;
}

function HolographicGlyph({ role, color, glow }: HolographicGlyphProps) {
  const glowStyle = { filter: `drop-shadow(0 0 5px ${glow})` };
  
  switch (role) {
    case 'planner':
      return (
        <svg className="w-5 h-5 relative z-10" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" style={glowStyle}>
          <polygon points="12,2 21,7 21,17 12,22 3,17 3,7" />
          <circle cx="12" cy="12" r="3.5" fill={`${color}22`} />
          <line x1="12" y1="2" x2="12" y2="22" strokeDasharray="2 2" />
        </svg>
      );
    case 'research':
      return (
        <svg className="w-5 h-5 relative z-10" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" style={glowStyle}>
          <circle cx="12" cy="12" r="8.5" strokeDasharray="3 3" />
          <circle cx="12" cy="12" r="4.5" />
          <circle cx="12" cy="12" r="1.5" fill={color} />
          <motion.circle
            cx="12" cy="12" r="8.5"
            animate={{ scale: [0.5, 1], opacity: [1, 0] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: 'easeOut' }}
          />
        </svg>
      );
    case 'coder':
      return (
        <svg className="w-5 h-5 relative z-10" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" style={glowStyle}>
          <path d="M7 8L3 12L7 16" />
          <path d="M17 8L21 12L17 16" />
          <line x1="12" y1="5" x2="12" y2="19" strokeDasharray="2 3" />
        </svg>
      );
    case 'memory':
      return (
        <svg className="w-5 h-5 relative z-10" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.2" style={glowStyle}>
          <polygon points="12,2 20,6.5 12,11 4,6.5" fill={`${color}15`} />
          <polygon points="4,6.5 12,11 12,20 4,15.5" />
          <polygon points="12,11 20,6.5 20,15.5 12,20" />
          <line x1="12" y1="11" x2="12" y2="20" strokeDasharray="2 2" />
        </svg>
      );
    case 'tool':
      return (
        <motion.svg
          className="w-5 h-5 relative z-10" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" style={glowStyle}
          animate={{ rotate: 360 }}
          transition={{ duration: 7, repeat: Infinity, ease: 'linear' }}
        >
          <path d="M12 2v3M12 19v3M3.5 12h3M17.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1" strokeLinecap="round" />
          <circle cx="12" cy="12" r="5" fill={`${color}22`} />
        </motion.svg>
      );
    case 'analyst':
      return (
        <svg className="w-5 h-5 relative z-10" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" style={glowStyle}>
          <path d="M2 12h3.5l1.8-6.5 3.2 13 2.8-9 2 4.5h6.7" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="10.5" cy="18.5" r="1" fill={color} />
        </svg>
      );
    default:
      return (
        <svg className="w-5 h-5 relative z-10" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" style={glowStyle}>
          <circle cx="12" cy="12" r="3" fill={color} />
          <path d="M12 2v4M12 18v4M2 12h4M18 12h4" strokeDasharray="2 2" />
        </svg>
      );
  }
}

interface OrbVisualConfig {
  color: string;
  glow: string;
  ringColor: string;
  pulse: boolean;
  rotate: boolean;
  shimmer: boolean;
}

const ORB_STATUS_CONFIGS: Record<AgentStatus, OrbVisualConfig> = {
  idle: {
    color: '#00D4FF',
    glow: 'rgba(0, 212, 255, 0.25)',
    ringColor: 'rgba(0, 212, 255, 0.35)',
    pulse: false,
    rotate: false,
    shimmer: false,
  },
  thinking: {
    color: '#A855F7',
    glow: 'rgba(168, 85, 247, 0.55)',
    ringColor: 'rgba(168, 85, 247, 0.65)',
    pulse: true,
    rotate: false,
    shimmer: true,
  },
  running: {
    color: '#00D4FF',
    glow: 'rgba(0, 212, 255, 0.6)',
    ringColor: 'rgba(0, 212, 255, 0.75)',
    pulse: true,
    rotate: true,
    shimmer: true,
  },
  streaming: {
    color: '#3B82F6',
    glow: 'rgba(59, 130, 246, 0.65)',
    ringColor: 'rgba(59, 130, 246, 0.8)',
    pulse: true,
    rotate: true,
    shimmer: true,
  },
  completed: {
    color: '#00FF95',
    glow: 'rgba(0, 255, 149, 0.55)',
    ringColor: 'rgba(0, 255, 149, 0.65)',
    pulse: false,
    rotate: false,
    shimmer: false,
  },
  failed: {
    color: '#FF4D67',
    glow: 'rgba(255, 77, 103, 0.55)',
    ringColor: 'rgba(255, 77, 103, 0.65)',
    pulse: true,
    rotate: false,
    shimmer: true,
  },
  disabled: {
    color: 'rgba(148, 163, 184, 0.45)',
    glow: 'rgba(148, 163, 184, 0.15)',
    ringColor: 'rgba(148, 163, 184, 0.2)',
    pulse: false,
    rotate: false,
    shimmer: false,
  },
};

interface AgentOrbProps {
  role: string;
  config?: AgentConfig;
  status: AgentStatus;
  progress?: number;
  isActive: boolean;
  position: { x: number; y: number };
  onClick?: () => void;
}

export function AgentOrb({
  role,
  config,
  status,
  isActive,
  position,
  onClick,
}: AgentOrbProps) {
  const visual = ORB_STATUS_CONFIGS[status] ?? ORB_STATUS_CONFIGS.idle;
  const label = config?.name ?? role;

  return (
    <motion.div
      className="absolute flex flex-col items-center cursor-pointer select-none"
      initial={{ opacity: 0, scale: 0, left: position.x, top: position.y }}
      animate={{ 
        opacity: 1, 
        scale: isActive ? 1.25 : 1.0,
        left: position.x,
        top: position.y 
      }}
      style={{
        transform: 'translate(-50%, -50%)',
      }}
      transition={{ 
        left: { type: 'spring', stiffness: 35, damping: 10 },
        top: { type: 'spring', stiffness: 35, damping: 10 },
        scale: springs.gentle,
        opacity: { duration: 0.2 }
      }}
      whileHover={{ scale: 1.15 }}
      onClick={onClick}
    >
      {/* ── Mini AI Reactor Glass Holographic Dock ── */}
      <motion.div
        className="relative w-16 h-16 rounded-xl flex items-center justify-center border backdrop-blur-md"
        style={{
          background: `radial-gradient(circle at 35% 35%, ${visual.color}18 0%, rgba(10,15,30,0.85) 90%)`,
          boxShadow: `0 0 25px ${visual.glow}, inset 0 0 12px ${visual.color}25`,
          borderColor: isActive ? visual.color : 'rgba(255,255,255,0.08)',
        }}
        animate={
          visual.pulse
            ? { scale: [1, 1.05, 1], borderColor: [visual.color, 'rgba(255,255,255,0.08)', visual.color] }
            : { scale: 1 }
        }
        transition={
          visual.pulse
            ? { duration: 2.0, repeat: Infinity, ease: 'easeInOut' }
            : {}
        }
      >
        {/* Shimmer boundary */}
        {visual.shimmer && (
          <motion.div
            className="absolute inset-[-4px] rounded-xl border border-white/5 opacity-40 pointer-events-none"
            animate={{ scale: [1, 1.12, 1], opacity: [0.15, 0.4, 0.15] }}
            transition={{ duration: 2.0, repeat: Infinity }}
          />
        )}

        {/* Outer Rotating Dash Frame */}
        <motion.div
          className="absolute inset-[-2px] rounded-xl border border-dashed"
          style={{
            borderColor: visual.ringColor,
            opacity: isActive ? 0.95 : 0.4,
          }}
          animate={visual.rotate ? { rotate: 360 } : { rotate: 0 }}
          transition={visual.rotate ? { duration: 9, repeat: Infinity, ease: 'linear' } : {}}
        />

        {/* Dynamic Micro energy particle spark */}
        <div
          className="absolute w-2 h-2 rounded-full pointer-events-none"
          style={{
            background: visual.color,
            boxShadow: `0 0 10px ${visual.color}`,
            bottom: 4,
            right: 4,
          }}
        />

        {/* Glyph projected from the energy core */}
        <HolographicGlyph role={role} color={visual.color} glow={visual.glow} />
      </motion.div>

      {/* Label */}
      <span
        className="text-[9px] uppercase tracking-widest font-bold mt-2.5 text-center leading-tight font-heading"
        style={{
          color: isActive ? visual.color : 'rgba(148, 163, 184, 0.7)',
          textShadow: isActive ? `0 0 8px ${visual.glow}` : 'none',
        }}
      >
        {label}
      </span>

      {/* Status LED */}
      <motion.div
        className="w-1.5 h-1.5 rounded-full mt-1.5"
        style={{ background: visual.color, boxShadow: `0 0 5px ${visual.glow}` }}
        animate={visual.pulse ? { opacity: [0.35, 1, 0.35] } : { opacity: 0.65 }}
        transition={visual.pulse ? { duration: 2.0, repeat: Infinity, ease: 'easeInOut' } : {}}
      />
    </motion.div>
  );
}