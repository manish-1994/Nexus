import { useState, useRef, useEffect, useCallback } from 'react'

interface MessageComposerProps {
  onSend: (content: string) => void
  isLoading: boolean
  isStreaming: boolean
  onStopStreaming?: () => void
  canSend?: boolean
}

export function MessageComposer({
  onSend,
  isLoading,
  isStreaming,
  onStopStreaming,
  canSend = true
}: MessageComposerProps) {
  const [content, setContent] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (content.trim() && !isLoading) {
      onSend(content.trim())
      setContent('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }

  const handleStop = useCallback(() => {
    onStopStreaming?.()
    textareaRef.current?.focus()
  }, [onStopStreaming])

  useEffect(() => {
    if (textareaRef.current && !isStreaming) {
      textareaRef.current.focus()
    }
  }, [isStreaming])

  return (
    <div className="border-t border-white/5 bg-surface/30 backdrop-blur-md p-4">
      <form onSubmit={handleSubmit} className="space-y-2 max-w-4xl mx-auto">
        <div className="flex items-end space-x-3">
          <textarea
            ref={textareaRef}
            value={content}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            className="flex-1 bg-elevated/40 text-text placeholder-text-muted/50 caret-accent selection:bg-accent/30 border border-white/10 rounded-xl px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent-light/50 transition-all text-sm leading-relaxed"
            rows={1}
            disabled={isLoading}
            style={{ minHeight: '46px', maxHeight: '200px' }}
            aria-label="Message input"
            aria-placeholder="Type your message"
            role="textbox"
            aria-multiline="true"
          />
          <div className="flex items-center space-x-2">
            <button
              type="submit"
              disabled={!content.trim() || isLoading || !canSend}
              className="bg-accent hover:bg-accent-light disabled:bg-white/5 disabled:text-text-muted/40 disabled:cursor-not-allowed text-white rounded-xl px-5 py-3 text-xs font-bold tracking-wider uppercase transition-all focus:outline-none focus:ring-2 focus:ring-accent/30 shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_20px_rgba(59,130,246,0.5)] active:scale-95"
            >
              {isStreaming ? 'Generating' : isLoading ? 'Sending' : 'Send'}
            </button>
            {isStreaming && onStopStreaming && (
              <button
                type="button"
                onClick={handleStop}
                className="bg-danger hover:bg-danger/80 text-white rounded-xl px-5 py-3 text-xs font-bold tracking-wider uppercase transition-all focus:outline-none focus:ring-2 focus:ring-danger/30 shadow-[0_0_15px_rgba(239,68,68,0.3)] hover:shadow-[0_0_20px_rgba(239,68,68,0.5)] active:scale-95"
              >
                Stop
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  )
}
