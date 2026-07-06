import { memo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Sparkles,
  Code2,
  PenLine,
  Lightbulb,
  Search,
  Plus,
  MessageSquare,
  ArrowRight,
} from 'lucide-react'
import type { Conversation } from '../../types/chat'
import { springs } from '../common/Motion'

interface EmptyStateProps {
  onNewConversation: () => void
  onSelectConversation?: (id: number) => void
  onSuggestionSelect?: (prompt: string) => void
  conversations?: Conversation[]
}

interface Suggestion {
  id: string
  icon: React.ReactNode
  title: string
  prompt: string
  tone: 'accent' | 'primary' | 'warning' | 'success'
}

const SUGGESTIONS: Suggestion[] = [
  {
    id: 'code',
    icon: <Code2 className="w-4 h-4" />,
    title: 'Write Code',
    prompt: 'Help me write a function that...',
    tone: 'accent',
  },
  {
    id: 'brainstorm',
    icon: <Lightbulb className="w-4 h-4" />,
    title: 'Brainstorm Ideas',
    prompt: 'Brainstorm ideas for a new project about...',
    tone: 'warning',
  },
  {
    id: 'write',
    icon: <PenLine className="w-4 h-4" />,
    title: 'Draft Content',
    prompt: 'Draft a document explaining...',
    tone: 'primary',
  },
  {
    id: 'research',
    icon: <Search className="w-4 h-4" />,
    title: 'Research Topic',
    prompt: 'Research and summarize the topic of...',
    tone: 'success',
  },
]

const toneClasses = {
  accent: 'border-accent/30 bg-accent/5 hover:bg-accent/10 text-accent',
  primary: 'border-primary/30 bg-primary/5 hover:bg-primary/10 text-primary-light',
  warning: 'border-warning/30 bg-warning/5 hover:bg-warning/10 text-warning',
  success: 'border-success/30 bg-success/5 hover:bg-success/10 text-success',
}

function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

export const EmptyState = memo(function EmptyState({
  onNewConversation,
  onSelectConversation,
  onSuggestionSelect,
  conversations = [],
}: EmptyStateProps) {
  const [hoveredSuggestion, setHoveredSuggestion] = useState<string | null>(null)
  const recentConversations = conversations.slice(0, 4)

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="min-h-full flex flex-col items-center justify-center px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={springs.smooth}
          className="w-full max-w-2xl"
        >
          {/* Hero */}
          <div className="text-center mb-10">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ ...springs.smooth, delay: 0.1 }}
              className="inline-flex items-center justify-center w-16 h-16 rounded-panel bg-accent/10 border border-accent/30 mb-4 shadow-glow-sm"
            >
              <Sparkles className="w-7 h-7 text-accent" />
            </motion.div>
            <h1 className="text-2xl font-heading font-bold text-text tracking-tight mb-2">
              NEXUS Command Center
            </h1>
            <p className="text-sm text-text-muted leading-relaxed max-w-md mx-auto">
              Your AI operating system is ready. Start a new conversation or pick up where you left off.
            </p>
          </div>

          {/* New conversation CTA */}
          <motion.button
            onClick={onNewConversation}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            transition={springs.instant}
            className="w-full glass-surface rounded-panel border border-accent/30 hover:border-accent/50 px-5 py-4 flex items-center justify-between mb-8 group transition-all duration-normal focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-button bg-accent/15 border border-accent/30 flex items-center justify-center">
                <Plus className="w-5 h-5 text-accent" />
              </div>
              <div className="text-left">
                <div className="text-sm font-bold text-text">Start New Conversation</div>
                <div className="text-[11px] text-text-muted">Begin a fresh AI session</div>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-accent opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-normal" />
          </motion.button>

          {/* Suggested prompts */}
          <div className="mb-8">
            <div className="text-[9px] font-heading font-bold tracking-widest uppercase text-text-muted mb-3 px-1">
              Suggested Prompts
            </div>
            <div className="grid grid-cols-2 gap-2.5">
              {SUGGESTIONS.map((s, i) => (
                <motion.button
                  key={s.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ ...springs.smooth, delay: 0.15 + i * 0.05 }}
                  onClick={() => onSuggestionSelect?.(s.prompt) || onNewConversation()}
                  onMouseEnter={() => setHoveredSuggestion(s.id)}
                  onMouseLeave={() => setHoveredSuggestion(null)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`rounded-panel border px-4 py-3 flex items-start gap-3 text-left transition-all duration-normal focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none ${toneClasses[s.tone]}`}
                >
                  <div className="flex-shrink-0 mt-0.5">{s.icon}</div>
                  <div className="min-w-0">
                    <div className="text-xs font-bold text-text mb-0.5">{s.title}</div>
                    <div className="text-[10px] text-text-muted leading-snug truncate">
                      {hoveredSuggestion === s.id ? s.prompt : `"${s.prompt.slice(0, 32)}..."`}
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Recent conversations */}
          {recentConversations.length > 0 && (
            <div>
              <div className="text-[9px] font-heading font-bold tracking-widest uppercase text-text-muted mb-3 px-1">
                Recent Conversations
              </div>
              <div className="space-y-1.5">
                {recentConversations.map((conv, i) => (
                  <motion.button
                    key={conv.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ ...springs.smooth, delay: 0.3 + i * 0.04 }}
                    onClick={() => onSelectConversation?.(conv.id)}
                    whileHover={{ x: 4 }}
                    className="w-full glass-surface rounded-button border border-white/5 hover:border-accent/30 px-3 py-2.5 flex items-center gap-3 text-left transition-all duration-normal focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
                  >
                    <MessageSquare className="w-3.5 h-3.5 text-text-muted flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-medium text-text truncate">{conv.title}</div>
                    </div>
                    <span className="text-[9px] font-bold uppercase tracking-widest text-text-muted/60 flex-shrink-0">
                      {formatRelativeTime(conv.updated_at || conv.created_at)}
                    </span>
                  </motion.button>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
})
