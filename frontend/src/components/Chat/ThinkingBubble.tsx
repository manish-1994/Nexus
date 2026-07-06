import { useState, useEffect } from 'react';

/**
 * Thinking placeholder shown for an assistant message before the first
 * streamed token arrives. Displays an animated Nexus-style icon, a
 * "Thinking..." label, bouncing dots, a pulsing border and a shimmer sweep.
 *
 * Purely presentational — no data fetching, no callbacks.
 */
export function ThinkingBubble() {
  const [phase, setPhase] = useState<'thinking' | 'analyzing'>('thinking');

  useEffect(() => {
    const t = setTimeout(() => setPhase('analyzing'), 1100);
    return () => clearTimeout(t);
  }, []);

  return (
    <div
      className="fade-scale-in thinking-pulse shimmer-sweep relative overflow-hidden rounded-bubble border border-accent/20 bg-white/[0.03] px-5 py-4 max-w-[75%]"
      role="status"
      aria-live="polite"
      aria-label="Assistant is thinking"
    >
      <div className="flex items-center gap-3">
        {/* Animated Nexus icon — rotating ring + pulsing core */}
        <div className="relative w-7 h-7 flex items-center justify-center shrink-0">
          <span
            className="nexus-spin absolute inset-0 rounded-full border-2 border-accent/30 border-t-accent"
            aria-hidden="true"
          />
          <span
            className="absolute w-2.5 h-2.5 rounded-full bg-accent"
            style={{ animation: 'thinking-pulse 1.4s ease-in-out infinite' }}
            aria-hidden="true"
          />
        </div>

        {/* Label + sub-status */}
        <div className="flex flex-col gap-1">
          <span className="text-[11px] font-heading font-bold tracking-[0.18em] uppercase text-text">
            {phase === 'thinking' ? 'Thinking...' : 'Analyzing request...'}
          </span>
          <span className="text-[9px] font-mono tracking-[0.16em] uppercase text-text-muted">
            SYSTEM NODE
          </span>
        </div>

        {/* Bouncing dots */}
        <div className="flex items-center gap-1 ml-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="thinking-dot w-1.5 h-1.5 rounded-full bg-accent"
              style={{ animationDelay: `${i * 0.18}s` }}
              aria-hidden="true"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
