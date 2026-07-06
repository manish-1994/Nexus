import { motion } from 'framer-motion';

export type AICoreState = 'idle' | 'thinking' | 'streaming' | 'executing' | 'error' | 'finished';

interface AICoreProps {
  state?: AICoreState;
}

export function AICore({ state = 'idle' }: AICoreProps) {
  // Define visual configurations based on state
  const stateConfigs = {
    idle: {
      color: 'rgba(56, 189, 248, 0.8)', // Cyan
      glow: 'rgba(56, 189, 248, 0.4)',
      pulseDuration: 4,
      rotationSpeed: 30,
      particleSpeed: 3,
    },
    thinking: {
      color: 'rgba(168, 85, 247, 0.8)', // Purple
      glow: 'rgba(168, 85, 247, 0.4)',
      pulseDuration: 1.5,
      rotationSpeed: 10,
      particleSpeed: 1.5,
    },
    streaming: {
      color: 'rgba(59, 130, 246, 0.8)', // Electric Blue
      glow: 'rgba(59, 130, 246, 0.4)',
      pulseDuration: 2,
      rotationSpeed: 15,
      particleSpeed: 2,
    },
    executing: {
      color: 'rgba(236, 72, 153, 0.8)', // Pink/Magenta
      glow: 'rgba(236, 72, 153, 0.4)',
      pulseDuration: 1,
      rotationSpeed: 8,
      particleSpeed: 1,
    },
    error: {
      color: 'rgba(239, 68, 68, 0.8)', // Red
      glow: 'rgba(239, 68, 68, 0.4)',
      pulseDuration: 0.8,
      rotationSpeed: 45,
      particleSpeed: 5,
    },
    finished: {
      color: 'rgba(34, 197, 94, 0.8)', // Green
      glow: 'rgba(34, 197, 94, 0.4)',
      pulseDuration: 3,
      rotationSpeed: 20,
      particleSpeed: 4,
    },
  };

  const config = stateConfigs[state] ?? stateConfigs.idle;

  return (
    <div className="relative w-80 h-80 flex items-center justify-center select-none pointer-events-none">
      {/* Outer Holographic HUD Elements */}
      <svg className="absolute w-full h-full overflow-visible" viewBox="0 0 200 200">
        <defs>
          <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Outer Tick Ring */}
        <motion.circle
          cx="100"
          cy="100"
          r="90"
          fill="none"
          stroke={config.color}
          strokeWidth="1"
          strokeDasharray="4, 8"
          opacity="0.3"
          animate={{ rotate: 360 }}
          transition={{ duration: config.rotationSpeed, repeat: Infinity, ease: "linear" }}
        />

        {/* Middle Segmented Ring */}
        <motion.circle
          cx="100"
          cy="100"
          r="75"
          fill="none"
          stroke={config.color}
          strokeWidth="1.5"
          strokeDasharray="40, 20, 10, 20"
          opacity="0.5"
          filter="url(#bloom)"
          animate={{ rotate: -360 }}
          transition={{ duration: config.rotationSpeed * 1.5, repeat: Infinity, ease: "linear" }}
        />

        {/* Interactive Pulse Waves */}
        <motion.circle
          cx="100"
          cy="100"
          r="50"
          fill="none"
          stroke={config.color}
          strokeWidth="2"
          opacity="0.8"
          filter="url(#bloom)"
          animate={{
            r: [50, 85, 50],
            opacity: [0.8, 0, 0.8],
          }}
          transition={{
            duration: config.pulseDuration,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        {/* Orbiting Tech Nodes */}
        <motion.g
          animate={{ rotate: 360 }}
          transition={{ duration: config.rotationSpeed * 0.8, repeat: Infinity, ease: "linear" }}
          style={{ transformOrigin: '100px 100px' }}
        >
          <circle cx="100" cy="25" r="3" fill={config.color} filter="url(#bloom)" />
          <line x1="100" y1="25" x2="100" y2="40" stroke={config.color} strokeWidth="1" opacity="0.5" />
          <circle cx="100" cy="175" r="3" fill={config.color} filter="url(#bloom)" />
          <line x1="100" y1="175" x2="100" y2="160" stroke={config.color} strokeWidth="1" opacity="0.5" />
        </motion.g>

        {/* Scanning Radar Line */}
        <motion.line
          x1="100"
          y1="100"
          x2="100"
          y2="35"
          stroke={config.color}
          strokeWidth="1.5"
          opacity="0.3"
          style={{ transformOrigin: '100px 100px' }}
          animate={{ rotate: 360 }}
          transition={{ duration: config.pulseDuration * 2, repeat: Infinity, ease: "linear" }}
        />

        {/* Inner Tech Ring with Hexagon pattern or dashes */}
        <motion.circle
          cx="100"
          cy="100"
          r="45"
          fill="none"
          stroke={config.color}
          strokeWidth="1"
          strokeDasharray="2, 4"
          opacity="0.6"
          animate={{ rotate: -360 }}
          transition={{ duration: config.rotationSpeed * 0.5, repeat: Infinity, ease: "linear" }}
        />
      </svg>

      {/* Center Volumetric Glow Core */}
      <motion.div
        className="w-24 h-24 rounded-full flex items-center justify-center relative z-10"
        style={{
          boxShadow: `inset 0 0 20px ${config.color}, 0 0 35px ${config.glow}`,
          background: `radial-gradient(circle, ${config.color} 0%, rgba(0,0,0,0.8) 70%)`,
        }}
        animate={{
          scale: [0.95, 1.05, 0.95],
        }}
        transition={{
          duration: config.pulseDuration,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        {/* Core Detail Rings */}
        <div className="w-16 h-16 rounded-full border border-dashed border-white/20 animate-spin" style={{ animationDuration: '8s' }} />
        <div className="absolute w-8 h-8 rounded-full bg-white/20 filter blur-[2px] animate-pulse" />
      </motion.div>
    </div>
  );
}
