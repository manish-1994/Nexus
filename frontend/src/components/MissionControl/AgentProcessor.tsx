import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { AgentStatus, AgentConfig } from '../../types/mission-control';

// ── Holographic SVG Glyphs per role ──
function AgentGlyph({ role, color, size = 26 }: { role: string; color: string; size?: number }) {
  const s = { filter: `drop-shadow(0 0 5px ${color})`, width: size, height: size };
  const sw = 1.4;
  switch (role) {
    case 'planner':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} style={s}>
          <polygon points="12,2 21,7 21,17 12,22 3,17 3,7" fill={`${color}15`} />
          <line x1="12" y1="2" x2="12" y2="22" strokeDasharray="2,3" opacity="0.5" />
          <circle cx="12" cy="12" r="3" fill={`${color}30`} />
        </svg>
      );
    case 'research':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} style={s}>
          <circle cx="11" cy="11" r="7" strokeDasharray="3,2" />
          <circle cx="11" cy="11" r="4" />
          <line x1="16" y1="16" x2="21" y2="21" />
          <circle cx="11" cy="11" r="1.5" fill={color} />
        </svg>
      );
    case 'coder':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} style={s}>
          <path d="M8 7L4 12L8 17" />
          <path d="M16 7L20 12L16 17" />
          <line x1="12" y1="4" x2="12" y2="20" strokeDasharray="2,3" opacity="0.6" />
        </svg>
      );
    case 'memory':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} style={s}>
          <polygon points="12,2 20,7 12,12 4,7" fill={`${color}18`} />
          <polygon points="4,7 12,12 12,21 4,16" />
          <polygon points="12,12 20,7 20,16 12,21" />
        </svg>
      );
    case 'tool':
      return (
        <motion.svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} style={s}
          animate={{ rotate: 360 }} transition={{ duration: 7, repeat: Infinity, ease: 'linear' }}>
          <circle cx="12" cy="12" r="4" fill={`${color}15`} />
          <line x1="12" y1="2" x2="12" y2="5" />
          <line x1="12" y1="19" x2="12" y2="22" />
          <line x1="2" y1="12" x2="5" y2="12" />
          <line x1="19" y1="12" x2="22" y2="12" />
          <line x1="5.3" y1="5.3" x2="7.4" y2="7.4" />
          <line x1="16.6" y1="16.6" x2="18.7" y2="18.7" />
          <line x1="5.3" y1="18.7" x2="7.4" y2="16.6" />
          <line x1="16.6" y1="7.4" x2="18.7" y2="5.3" />
        </motion.svg>
      );
    case 'analyst':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} style={s}>
          <polyline points="2,16 6,10 10,13 14,7 18,11 22,8" />
          <circle cx="22" cy="8" r="1.5" fill={color} />
          <line x1="2" y1="20" x2="22" y2="20" opacity="0.35" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} style={s}>
          <circle cx="12" cy="12" r="4.5" fill={`${color}22`} />
          <line x1="12" y1="2" x2="12" y2="7" /><line x1="12" y1="17" x2="12" y2="22" />
          <line x1="2" y1="12" x2="7" y2="12" /><line x1="17" y1="12" x2="22" y2="12" />
        </svg>
      );
  }
}

interface NodeStyle { color: string; glowColor: string; label: string; pulse: boolean; spin: boolean; }
const STATUS: Record<AgentStatus, NodeStyle> = {
  idle:      { color: '#00D4FF', glowColor: 'rgba(0,212,255,0.20)',  label: 'STANDBY',   pulse: false, spin: false },
  thinking:  { color: '#A855F7', glowColor: 'rgba(168,85,247,0.55)', label: 'THINKING',  pulse: true,  spin: false },
  running:   { color: '#00D4FF', glowColor: 'rgba(0,212,255,0.55)',  label: 'RUNNING',   pulse: true,  spin: true  },
  streaming: { color: '#38BDF8', glowColor: 'rgba(56,189,248,0.60)', label: 'STREAMING', pulse: true,  spin: true  },
  completed: { color: '#00FF95', glowColor: 'rgba(0,255,149,0.45)',  label: 'DONE',      pulse: false, spin: false },
  failed:    { color: '#FF4D67', glowColor: 'rgba(255,77,103,0.55)', label: 'FAULT',     pulse: true,  spin: false },
  disabled:  { color: '#475569', glowColor: 'rgba(71,85,105,0.12)',  label: 'OFFLINE',   pulse: false, spin: false },
};

export interface AgentProcessorProps {
  role: string;
  config?: AgentConfig;
  status: AgentStatus;
  isActive: boolean;
  position: { x: number; y: number };
  dimmed?: boolean;
  depthScale?: number;
  depthBlur?: number;
  currentTask?: string | null;
  elapsedMs?: number;
  onClick?: () => void;
}

export function AgentProcessor({
  role, config, status, isActive, position, dimmed, depthScale = 1.0, depthBlur = 0,
  currentTask, elapsedMs, onClick,
}: AgentProcessorProps) {
  const [hovered, setHovered] = useState(false);
  const S = STATUS[status] ?? STATUS.idle;
  const agentName = config?.name ?? role;

  // Deterministic float timing per role (no Math.random in render)
  const floatDuration = 3.8 + (role.charCodeAt(0) % 5) * 0.5;
  const floatDelay   = (role.charCodeAt(1) ?? 0) % 4 * 0.6;
  const floatAmp     = isActive ? 2 : 4;

  // Deterministic glow pulse timing
  const glowDuration = 2.2 + (role.charCodeAt(2) ?? 0) % 3 * 0.4;

  const nodeScale = (isActive ? 1.14 : 1.0) * depthScale;

  return (
    <motion.div
      className="absolute pointer-events-none"
      style={{
        left: position.x,
        top: position.y,
        transform: 'translate(-50%, -50%)',
        zIndex: Math.round(depthScale * 20),
        filter: depthBlur > 0.1 ? `blur(${depthBlur.toFixed(1)}px)` : undefined,
      }}
      initial={{ opacity: 0, scale: 0.15 }}
      animate={{
        opacity: dimmed ? 0.25 : 1,
        scale: nodeScale,
        left: position.x,
        top: position.y,
      }}
      transition={{
        opacity: { duration: 0.5 },
        scale: { type: 'spring', stiffness: 55, damping: 18 },
        left: { type: 'spring', stiffness: 32, damping: 14 },
        top:  { type: 'spring', stiffness: 32, damping: 14 },
      }}
    >
      {/* Float oscillation */}
      <motion.div
        animate={{ y: [-floatAmp, floatAmp, -floatAmp] }}
        transition={{ duration: floatDuration, repeat: Infinity, ease: 'easeInOut', delay: floatDelay }}
        className="pointer-events-auto cursor-pointer"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onClick={onClick}
      >
        {/* ── Outer breathing ambient glow ── */}
        <motion.div
          className="absolute rounded-2xl pointer-events-none"
          style={{ inset: -16, background: `radial-gradient(ellipse, ${S.glowColor} 0%, transparent 70%)` }}
          animate={{ opacity: [0.35, 0.75, 0.35], scale: [0.95, 1.08, 0.95] }}
          transition={{ duration: glowDuration, repeat: Infinity, ease: 'easeInOut' }}
        />

        {/* ── Outer rotating dashed halo ── */}
        <motion.div
          className="absolute rounded-full border border-dashed"
          style={{ inset: -10, borderColor: S.glowColor, borderWidth: 1, opacity: isActive ? 0.95 : hovered ? 0.65 : 0.38 }}
          animate={S.spin ? { rotate: 360 } : hovered ? { rotate: 180 } : { rotate: 0 }}
          transition={S.spin ? { duration: 9, repeat: Infinity, ease: 'linear' } : hovered ? { duration: 18, repeat: Infinity, ease: 'linear' } : { duration: 0.6 }}
        />

        {/* ── Glass processor body ── */}
        <div
          className="relative flex flex-col items-center px-3 pt-3 pb-2 rounded-2xl border backdrop-blur-xl overflow-hidden"
          style={{
            background: isActive
              ? `radial-gradient(135deg, ${S.color}1C 0%, rgba(5,10,30,0.94) 100%)`
              : `radial-gradient(135deg, ${S.color}0E 0%, rgba(5,10,28,0.90) 100%)`,
            borderColor: isActive ? S.color : hovered ? `${S.color}60` : `${S.color}2A`,
            boxShadow: isActive
              ? `0 0 32px ${S.glowColor}, 0 0 70px ${S.glowColor.replace(',0.', ',0.25,')} , inset 0 0 16px ${S.color}16`
              : hovered
                ? `0 0 20px ${S.glowColor}, inset 0 0 10px ${S.color}10`
                : `0 0 10px ${S.glowColor.replace(',0.', ',0.08,')}`,
            minWidth: 78,
            transition: 'border-color 0.4s, box-shadow 0.4s',
          }}
        >
          {/* Horizontal scan line sweeping through the card */}
          <motion.div
            className="absolute inset-x-0 h-px pointer-events-none"
            style={{ background: `linear-gradient(90deg, transparent, ${S.color}70, transparent)`, opacity: 0.55, top: 0 }}
            animate={{ top: ['0%', '100%'] }}
            transition={{ duration: floatDuration * 0.75, repeat: Infinity, ease: 'linear', delay: floatDelay * 0.5, repeatDelay: 1.5 }}
          />

          {/* Corner calibration ticks */}
          <div className="absolute top-1 left-1 w-2 h-2 border-t border-l pointer-events-none" style={{ borderColor: `${S.color}50` }} />
          <div className="absolute top-1 right-1 w-2 h-2 border-t border-r pointer-events-none" style={{ borderColor: `${S.color}50` }} />
          <div className="absolute bottom-1 left-1 w-2 h-2 border-b border-l pointer-events-none" style={{ borderColor: `${S.color}50` }} />
          <div className="absolute bottom-1 right-1 w-2 h-2 border-b border-r pointer-events-none" style={{ borderColor: `${S.color}50` }} />

          {/* Glyph area */}
          <div className="relative w-12 h-12 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full" style={{ background: `radial-gradient(circle, ${S.color}1E 0%, transparent 72%)` }} />
            <AgentGlyph role={role} color={S.color} size={28} />
          </div>

          {/* Compact label */}
          <div className="mt-1.5 flex flex-col items-center gap-0.5">
            <span className="text-[8.5px] font-mono font-bold uppercase tracking-[0.14em] text-center" style={{ color: S.color, opacity: isActive ? 1 : 0.72 }}>
              {agentName}
            </span>
            <div className="flex items-center gap-1">
              <motion.span
                className="w-1 h-1 rounded-full"
                style={{ background: S.color }}
                animate={S.pulse ? { opacity: [0.2, 1, 0.2], scale: [0.7, 1.3, 0.7] } : { opacity: 0.65 }}
                transition={S.pulse ? { duration: 1.3, repeat: Infinity } : {}}
              />
              <span className="text-[6.5px] font-mono uppercase tracking-widest text-white/28">{S.label}</span>
            </div>
          </div>
        </div>

        {/* ── Hover expanded info card ── */}
        <AnimatePresence>
          {hovered && (
            <motion.div
              className="absolute z-50 rounded-xl border backdrop-blur-2xl px-3.5 py-2.5 pointer-events-none"
              style={{
                top: '110%', left: '50%', x: '-50%', minWidth: 185,
                background: 'rgba(2,6,20,0.96)',
                borderColor: `${S.color}38`,
                boxShadow: `0 24px 64px rgba(0,0,0,0.75), 0 0 32px ${S.glowColor}`,
              }}
              initial={{ opacity: 0, y: -10, scale: 0.88 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.9 }}
              transition={{ duration: 0.16, ease: 'easeOut' }}
            >
              <div className="flex items-center gap-2 mb-2 pb-1.5 border-b" style={{ borderColor: `${S.color}20` }}>
                <AgentGlyph role={role} color={S.color} size={15} />
                <div>
                  <p className="text-[9px] font-mono font-bold uppercase tracking-widest" style={{ color: S.color }}>{agentName}</p>
                  <p className="text-[7px] font-mono text-white/32 uppercase">COGNITIVE PROCESSOR</p>
                </div>
              </div>
              <div className="space-y-1.5">
                <HoverRow label="STATUS" value={S.label} color={S.color} />
                <HoverRow label="ROLE" value={role.toUpperCase()} color="rgba(255,255,255,0.48)" />
                {currentTask && <HoverRow label="TASK" value={currentTask.slice(0, 30) + (currentTask.length > 30 ? '…' : '')} color="rgba(255,255,255,0.48)" />}
                {elapsedMs != null && elapsedMs > 0 && <HoverRow label="ELAPSED" value={`${(elapsedMs / 1000).toFixed(1)}s`} color="rgba(255,255,255,0.48)" />}
                {config?.preferred_model && <HoverRow label="MODEL" value={config.preferred_model} color="rgba(255,255,255,0.48)" />}
                {config?.tools && config.tools.length > 0 && <HoverRow label="TOOLS" value={`${config.tools.length} available`} color="rgba(255,255,255,0.48)" />}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
}

function HoverRow({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-[7px] font-mono uppercase tracking-widest text-white/22 shrink-0">{label}</span>
      <span className="text-[7.5px] font-mono text-right truncate max-w-[115px]" style={{ color }}>{value}</span>
    </div>
  );
}
