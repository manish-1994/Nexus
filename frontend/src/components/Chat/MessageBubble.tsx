import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion } from 'framer-motion';
import { Cpu, User, AlertTriangle, Zap, CheckCircle2, Clock, Activity } from 'lucide-react';
import type { Message, MessageStatus } from '../../types/chat';
import { ThinkingBubble } from './ThinkingBubble';
import { StreamingBubble } from './StreamingBubble';
import { ProviderIcon } from './ProviderIcon';
import { cn, springs } from '../common/Motion';

interface MessageBubbleProps {
  message: Message;
  onRetry?: () => void;
  onCancel?: () => void;
  ariaLabel?: string;
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'JUST NOW';
  if (diffMins < 60) return `${diffMins}M AGO`;
  if (diffHours < 24) return `${diffHours}H AGO`;
  if (diffDays < 7) return `${diffDays}D AGO`;
  return date.toLocaleDateString().toUpperCase();
}

/** Map a message status to a small status indicator shown beneath assistant responses. */
function StatusIndicator({ status, hasError }: { status?: MessageStatus; hasError: boolean }) {
  if (hasError) {
    return (
      <span className="chat-status chat-status--error mt-2">
        <span className="chat-status-dot" />
        Error
      </span>
    );
  }
  if (status === 'generating') {
    return (
      <span className="chat-status chat-status--streaming mt-2">
        <span className="chat-status-dot" />
        Streaming...
      </span>
    );
  }
  if (status === 'sending') {
    return (
      <span className="chat-status chat-status--thinking mt-2">
        <span className="chat-status-dot" />
        Sending...
      </span>
    );
  }
  if (status === 'completed' || status === 'sent') {
    return (
      <span className="chat-status chat-status--completed mt-2">
        <span className="chat-status-dot" />
        Completed
      </span>
    );
  }
  return null;
}

export const MessageBubble = memo(function MessageBubble({
  message,
  onRetry,
  onCancel,
  ariaLabel,
}: MessageBubbleProps) {
  const isThinking = message.isThinking;
  const hasError = !!message.streamError;
  const isUser = message.role === 'user';
  const isStreaming = message.status === 'generating';

  return (
    <motion.div
      // User messages slide from the right; assistant messages fade+scale in.
      initial={isUser ? { opacity: 0, x: 24 } : { opacity: 0, scale: 0.97 }}
      animate={isUser ? { opacity: 1, x: 0 } : { opacity: 1, scale: 1 }}
      transition={springs.smooth}
      className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}
      aria-label={ariaLabel}
      role="article"
    >
      <motion.div
        className={cn(
          'rounded-bubble backdrop-blur-md border relative overflow-hidden',
          isUser
            ? 'bg-accent/15 border-accent/30 text-text rounded-tr-none max-w-[65%]'
            : hasError
            ? 'bg-danger/10 border-danger/30 text-text rounded-tl-none max-w-[75%]'
            : 'glass-surface text-text rounded-tl-none max-w-[75%]'
        )}
        style={{ padding: '20px' }}
        whileHover={{
          boxShadow: '0 0 24px rgba(0,229,255,0.18), 0 4px 20px rgba(0,0,0,0.12)',
        }}
      >
        {/* Glow indicator bar on the side */}
        <div
          className={cn(
            'absolute left-0 top-0 bottom-0 w-[3px]',
            isUser ? 'bg-accent' : hasError ? 'bg-danger' : 'bg-accent/40'
          )}
        />

        {/* Header: avatar + role + timestamp (compact) */}
        <div className="flex items-center gap-2 mb-2 pl-1">
          <div
            className={cn(
              'w-6 h-6 rounded-button flex items-center justify-center border',
              isUser
                ? 'bg-accent/20 border-accent/40 text-accent'
                : hasError
                ? 'bg-danger/20 border-danger/40 text-danger'
                : 'bg-white/5 text-accent'
            )}
            style={
              !isUser && !hasError
                ? { borderColor: 'rgba(255,255,255,0.08)' }
                : undefined
            }
          >
            {isUser ? (
              <User className="w-3.5 h-3.5" />
            ) : hasError ? (
              <AlertTriangle className="w-3.5 h-3.5" />
            ) : (
              <Cpu className="w-3.5 h-3.5" />
            )}
          </div>

          <div className="flex items-center gap-2 min-w-0">
            <span className="text-[9px] font-heading font-bold tracking-widest uppercase text-text whitespace-nowrap">
              {isUser ? 'OPERATOR' : hasError ? 'LINK FAILURE' : 'SYSTEM NODE'}
            </span>
            <span className="text-[8px] font-label font-medium tracking-wider text-text-muted uppercase whitespace-nowrap">
              {formatTime(message.created_at)}
            </span>
          </div>

          {!isUser && !hasError && (
            <div className="ml-auto flex items-center gap-1.5">
              <span className="px-1.5 py-0.5 rounded-button text-[7px] font-bold uppercase tracking-widest bg-accent/10 text-accent-light border border-accent/20 flex items-center gap-0.5">
                <CheckCircle2 className="w-2 h-2" />
                ACTIVE
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="message-body prose prose-invert max-w-none pl-1 prose-p:leading-relaxed prose-pre:bg-background prose-pre:border prose-pre:border-white/5 prose-pre:rounded-card">
          {isThinking ? (
            <ThinkingBubble />
          ) : isStreaming ? (
            <StreamingBubble content={message.content} />
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>

        {/* Status indicator beneath assistant responses */}
        {!isUser && (
          <div className="pl-1">
            <StatusIndicator status={message.status} hasError={hasError} />
          </div>
        )}

        {/* Error actions */}
        {hasError && (
          <div className="flex gap-2 mt-2 pt-2 border-t border-white/5">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={springs.instant}
              onClick={onRetry}
              className="px-3 py-1.5 bg-danger/20 text-text border border-danger/30 text-[9px] font-bold tracking-widest uppercase rounded-button hover:bg-danger/35 transition-all duration-normal focus-visible:ring-2 focus-visible:ring-danger/30 focus-visible:outline-none"
            >
              Re-establish sequence
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={springs.instant}
              onClick={onCancel}
              className="px-3 py-1.5 bg-surface border text-text-muted text-[9px] font-bold tracking-widest uppercase rounded-button hover:bg-surface-elevated transition-all duration-normal focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
              style={{ borderColor: 'rgba(255,255,255,0.08)' }}
            >
              Abort Link
            </motion.button>
          </div>
        )}

        {/* Model info pills — provider icon, model, tokens, gen time */}
        {!isUser && !hasError && !isThinking && (message.model || message.provider || message.tokens_used) && (
          <div className="flex items-center gap-1.5 mt-2.5 pt-2.5 border-t border-white/5 flex-wrap">
            {message.provider && (
              <InfoPill
                icon={<ProviderIcon name={message.provider} className="w-2.5 h-2.5 text-primary-light" />}
                label={message.provider}
                tone="primary"
              />
            )}
            {message.model && (
              <InfoPill
                icon={<Activity className="w-2.5 h-2.5 text-accent" />}
                label={message.model}
                tone="accent"
              />
            )}
            {message.tokens_used != null && message.tokens_used > 0 && (
              <InfoPill
                icon={<Zap className="w-2.5 h-2.5 text-warning" />}
                label={`${message.tokens_used} tok`}
                tone="warning"
              />
            )}
            {!isStreaming && message.status === 'completed' && (
              <InfoPill
                icon={<Clock className="w-2.5 h-2.5 text-text-muted" />}
                label={formatTime(message.created_at)}
                tone="muted"
              />
            )}
          </div>
        )}
      </motion.div>
    </motion.div>
  );
});

/** Compact info pill shown beneath assistant messages. */
const InfoPill = memo(function InfoPill({
  icon,
  label,
  tone,
}: {
  icon: React.ReactNode
  label: string
  tone: 'accent' | 'primary' | 'warning' | 'muted'
}) {
  const toneClass = {
    accent: 'bg-accent/10 text-accent-light border-accent/20',
    primary: 'bg-primary/10 text-primary-light border-primary/20',
    warning: 'bg-warning/10 text-warning border-warning/20',
    muted: 'bg-white/[0.03] text-text-muted border-white/10',
  }[tone]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-1.5 py-0.5 rounded-button text-[8px] font-bold uppercase tracking-widest border whitespace-nowrap',
        toneClass
      )}
    >
      {icon}
      <span className="truncate max-w-[120px]">{label}</span>
    </span>
  )
})
