import { useState, useRef, useEffect, useCallback, memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Square, Paperclip, Mic, Slash, Zap } from 'lucide-react'
import { springs } from '../common/Motion'

interface MessageComposerProps {
  onSend: (content: string) => void
  isLoading: boolean
  isStreaming: boolean
  onStopStreaming?: () => void
  canSend?: boolean
  /** Max character count for the input. */
  maxLength?: number
}

interface SlashCommand {
  id: string
  label: string
  description: string
  prompt: string
}

const SLASH_COMMANDS: SlashCommand[] = [
  { id: 'summarize', label: '/summarize', description: 'Summarize the conversation', prompt: 'Summarize our conversation so far.' },
  { id: 'explain', label: '/explain', description: 'Explain a concept', prompt: 'Explain the concept of ' },
  { id: 'code', label: '/code', description: 'Generate code', prompt: 'Write code that ' },
  { id: 'translate', label: '/translate', description: 'Translate text', prompt: 'Translate the following text: ' },
  { id: 'improve', label: '/improve', description: 'Improve writing', prompt: 'Improve the following text: ' },
  { id: 'brainstorm', label: '/brainstorm', description: 'Brainstorm ideas', prompt: 'Brainstorm ideas for ' },
]

const MAX_CHARS = 4000

export const MessageComposer = memo(function MessageComposer({
  onSend,
  isLoading,
  isStreaming,
  onStopStreaming,
  canSend = true,
  maxLength = MAX_CHARS,
}: MessageComposerProps) {
  const [content, setContent] = useState('')
  const [showSlashMenu, setShowSlashMenu] = useState(false)
  const [slashFilter, setSlashFilter] = useState('')
  const [selectedSlashIdx, setSelectedSlashIdx] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const charCount = content.length
  const isOverLimit = charCount > maxLength
  const isNearLimit = charCount > maxLength * 0.9

  const filteredCommands = SLASH_COMMANDS.filter((c) =>
    c.label.toLowerCase().includes(slashFilter.toLowerCase())
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (content.trim() && !isLoading && !isOverLimit) {
      onSend(content.trim())
      setContent('')
      setShowSlashMenu(false)
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Slash command navigation
    if (showSlashMenu) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedSlashIdx((i) => Math.min(i + 1, filteredCommands.length - 1))
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedSlashIdx((i) => Math.max(i - 1, 0))
        return
      }
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        const cmd = filteredCommands[selectedSlashIdx]
        if (cmd) {
          setContent(cmd.prompt)
          setShowSlashMenu(false)
          setSlashFilter('')
          setTimeout(() => textareaRef.current?.focus(), 0)
        }
        return
      }
      if (e.key === 'Escape') {
        e.preventDefault()
        setShowSlashMenu(false)
        setSlashFilter('')
        return
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setContent(value)

    // Detect slash command trigger
    if (value.startsWith('/') && !value.includes(' ')) {
      setShowSlashMenu(true)
      setSlashFilter(value)
      setSelectedSlashIdx(0)
    } else if (showSlashMenu) {
      setShowSlashMenu(false)
      setSlashFilter('')
    }

    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }

  const handleStop = useCallback(() => {
    onStopStreaming?.()
    textareaRef.current?.focus()
  }, [onStopStreaming])

  const selectCommand = (cmd: SlashCommand) => {
    setContent(cmd.prompt)
    setShowSlashMenu(false)
    setSlashFilter('')
    setTimeout(() => textareaRef.current?.focus(), 0)
  }

  useEffect(() => {
    if (textareaRef.current && !isStreaming) {
      textareaRef.current.focus()
    }
  }, [isStreaming])

  return (
    <div className="sticky bottom-0 z-20 bg-gradient-to-t from-background via-background/95 to-transparent pt-8 pb-4 px-4">
      <form onSubmit={handleSubmit} className="max-w-[900px] mx-auto relative">
        {/* Slash command menu */}
        <AnimatePresence>
          {showSlashMenu && filteredCommands.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.98 }}
              transition={springs.instant}
              className="absolute bottom-full left-0 right-0 mb-2 glass-surface rounded-panel border border-accent/20 overflow-hidden shadow-glow"
            >
              <div className="px-3 py-2 border-b border-white/5 flex items-center gap-2">
                <Slash className="w-3 h-3 text-accent" />
                <span className="text-[9px] font-heading font-bold tracking-widest uppercase text-text-muted">
                  Slash Commands
                </span>
              </div>
              <div className="max-h-48 overflow-y-auto py-1">
                {filteredCommands.map((cmd, i) => (
                  <button
                    key={cmd.id}
                    type="button"
                    onClick={() => selectCommand(cmd)}
                    onMouseEnter={() => setSelectedSlashIdx(i)}
                    className={`w-full px-3 py-2 flex items-center justify-between text-left transition-colors duration-fast ${
                      i === selectedSlashIdx ? 'bg-accent/10' : 'hover:bg-white/[0.03]'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-xs font-bold text-accent font-mono">{cmd.label}</span>
                      <span className="text-[10px] text-text-muted truncate">{cmd.description}</span>
                    </div>
                    {i === selectedSlashIdx && (
                      <span className="text-[8px] font-bold uppercase tracking-widest text-text-muted/60 flex-shrink-0">
                        ↵
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Enhanced Floating Dock */}
        <div className="floating-dock-chat">
          <div className="flex items-end gap-2">
            {/* Attachment placeholder */}
            <button
              type="button"
              className="flex-shrink-0 p-2 text-text-muted hover:text-accent transition-colors duration-normal rounded-button hover:bg-white/[0.03] focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
              aria-label="Attach file (placeholder)"
              title="Attach file"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            <textarea
              ref={textareaRef}
              value={content}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              placeholder="Type your message... (Enter to send, Shift+Enter for new line, / for commands)"
              className="flex-1 bg-transparent text-text placeholder-text-muted/60 caret-accent selection:bg-accent/30 border-none resize-none focus:outline-none px-1 py-2 chat-input"
              rows={1}
              disabled={isLoading}
              style={{ minHeight: '44px', maxHeight: '200px' }}
              aria-label="Message input"
              aria-placeholder="Type your message"
              role="textbox"
              aria-multiline="true"
            />

            {/* Voice placeholder */}
            <button
              type="button"
              className="flex-shrink-0 p-2 text-text-muted hover:text-accent transition-colors duration-normal rounded-button hover:bg-white/[0.03] focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
              aria-label="Voice input (placeholder)"
              title="Voice input"
            >
              <Mic className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-1.5 pb-0.5">
              {isStreaming && onStopStreaming && (
                <motion.button
                  type="button"
                  onClick={handleStop}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  transition={springs.instant}
                  className="bg-danger/20 hover:bg-danger/30 text-danger border border-danger/30 rounded-button p-2 transition-all duration-normal focus-visible:ring-2 focus-visible:ring-danger/30 focus-visible:outline-none"
                  aria-label="Stop streaming"
                >
                  <Square className="w-4 h-4" />
                </motion.button>
              )}
              <motion.button
                type="submit"
                disabled={!content.trim() || isLoading || !canSend || isOverLimit}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                transition={springs.instant}
                className="bg-gradient-to-br from-accent to-accent-dark hover:from-accent-light hover:to-accent disabled:from-white/5 disabled:to-white/5 disabled:text-text-muted/40 disabled:cursor-not-allowed text-white rounded-button p-2 transition-all duration-normal focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none shadow-glow-sm hover:shadow-glow relative overflow-hidden"
                aria-label="Send message"
              >
                <Send className="w-4 h-4 relative z-10" />
                {/* Animated glow on hover when enabled */}
                {content.trim() && !isLoading && canSend && !isOverLimit && (
                  <motion.span
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                    initial={{ x: '-100%' }}
                    whileHover={{ x: '100%' }}
                    transition={{ duration: 0.6 }}
                  />
                )}
              </motion.button>
            </div>
          </div>

          {/* Footer row: char counter + hints */}
          <div className="flex items-center justify-between mt-1.5 px-1">
            <div className="flex items-center gap-2 text-[8px] font-bold uppercase tracking-widest text-text-muted/50">
              <span className="flex items-center gap-1">
                <Zap className="w-2 h-2" />
                Enter to send
              </span>
              <span className="hidden sm:inline">·</span>
              <span className="hidden sm:inline">Shift+Enter for new line</span>
              <span className="hidden md:inline">·</span>
              <span className="hidden md:inline">/ for commands</span>
            </div>
            <div
              className={`text-[8px] font-bold tabular-nums tracking-widest transition-colors duration-normal ${
                isOverLimit
                  ? 'text-danger'
                  : isNearLimit
                  ? 'text-warning'
                  : 'text-text-muted/50'
              }`}
            >
              {charCount}/{maxLength}
            </div>
          </div>
        </div>
      </form>
    </div>
  )
})
