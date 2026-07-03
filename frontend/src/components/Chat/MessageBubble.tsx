import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion } from 'framer-motion';
import { Cpu, User, AlertTriangle, Zap, CheckCircle2, Server, Clock } from 'lucide-react';
import type { Message } from '../../types/chat';
import { ThinkingBubble } from './ThinkingBubble';
import { StreamingBubble } from './StreamingBubble';
import { cn } from '../common/Motion';

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

export const MessageBubble = memo(function MessageBubble({
  message,
  onRetry,
  onCancel,
  ariaLabel
}: MessageBubbleProps) {
  const isThinking = message.isThinking;
  const hasError = !!message.streamError;
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 20 }}
      className={cn("flex w-full mb-6", isUser ? "justify-end" : "justify-start")}
      aria-label={ariaLabel}
      role="article"
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl p-6 backdrop-blur-md border shadow-lg relative overflow-hidden",
          isUser 
            ? "bg-accent/15 border-accent/30 text-white rounded-tr-none ml-12 shadow-[0_0_20px_rgba(59,130,246,0.15)]" 
            : hasError 
            ? "bg-danger/10 border-danger/30 text-red-100 rounded-tl-none mr-12" 
            : "bg-surface/40 border-white/5 text-text rounded-tl-none mr-12 shadow-[0_4px_30px_rgba(0,0,0,0.2)]"
        )}
      >
        {/* Glow indicator bar on the side */}
        <div className={cn(
          "absolute left-0 top-0 bottom-0 w-1",
          isUser ? "bg-accent" : hasError ? "bg-danger" : "bg-accent-light/40"
        )} />

        <div className="flex items-center gap-3 mb-4 pl-1">
          <div
            className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center border",
              isUser 
                ? "bg-accent/20 border-accent/40 text-accent-light" 
                : hasError 
                ? "bg-danger/20 border-danger/40 text-danger" 
                : "bg-white/5 border-white/10 text-accent-light"
            )}
          >
            {isUser ? <User className="w-4.5 h-4.5" /> : hasError ? <AlertTriangle className="w-4.5 h-4.5" /> : <Cpu className="w-4.5 h-4.5" />}
          </div>
          
          <div className="flex flex-col">
            <span className="text-[10px] font-heading font-bold tracking-widest uppercase text-white">
              {isUser ? 'OPERATOR' : hasError ? 'LINK FAILURE' : 'SYSTEM NODE'}
            </span>
            <span className="text-[9px] font-label font-medium tracking-wider text-text-muted">
              {formatTime(message.created_at)}
            </span>
          </div>
 
          {!isUser && !hasError && (
            <div className="ml-auto flex items-center space-x-2">
              <span className="flex items-center space-x-1 px-2 py-0.5 rounded-md border border-accent/20 bg-accent/10 text-[9px] font-bold text-accent-light tracking-wider uppercase">
                <Server className="w-3 h-3" />
                <span>CLAUDE-3</span>
              </span>
              <span className="flex items-center space-x-1 px-2 py-0.5 rounded-md border border-success/20 bg-success/10 text-[9px] font-bold text-success tracking-wider uppercase">
                <CheckCircle2 className="w-3 h-3" />
                <span>ACTIVE-AGENT</span>
              </span>
            </div>
          )}
        </div>

        <div className="text-sm leading-relaxed prose prose-invert max-w-none pl-1 prose-p:leading-relaxed prose-pre:bg-[#090b10] prose-pre:border prose-pre:border-white/5 prose-pre:rounded-xl">
          {isThinking ? (
            <ThinkingBubble />
          ) : message.status === 'generating' ? (
            <StreamingBubble content={message.content} />
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>

        {hasError && (
          <div className="flex gap-3 mt-4 pt-4 border-t border-white/5">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onRetry}
              className="px-4 py-2 bg-danger/20 text-red-200 border border-danger/30 text-[10px] font-bold tracking-widest uppercase rounded-xl hover:bg-danger/35 transition-all"
            >
              Re-establish sequence
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onCancel}
              className="px-4 py-2 bg-surface border border-white/5 text-text-muted text-[10px] font-bold tracking-widest uppercase rounded-xl hover:bg-elevated transition-all"
            >
              Abort Link
            </motion.button>
          </div>
        )}

        {message.tokens_used && !hasError && (
          <div className="flex items-center space-x-4 mt-4 pt-4 border-t border-white/5 text-[9px] font-bold tracking-widest text-text-muted">
            <span className="flex items-center space-x-1">
              <Zap className="w-3 h-3 text-accent" />
              <span>{message.tokens_used} TOKENS</span>
            </span>
            <span className="flex items-center space-x-1">
              <Clock className="w-3 h-3 text-warning" />
              <span>1.2s LATENCY</span>
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
});
