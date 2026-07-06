import { memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Message } from '../../types/chat'
import { MessageBubble } from './MessageBubble'
import { ResponseTimeline } from './ResponseTimeline'
import { AIActivityLog } from './AIActivityLog'
import { useAutoScroll } from '../../pages/hooks/useAutoScroll'
import { useAIStatus } from '../../pages/hooks/useAIStatus'
import { springs } from '../common/Motion'

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
  onRetry?: () => void
  onCancel?: () => void
  conversationId: number | null
}

function MessageListInner({
  messages,
  isLoading,
  onRetry,
  onCancel,
  conversationId,
}: MessageListProps) {
  const {
    containerRef,
    bottomRef,
    handleScroll,
    showScrollButton,
    scrollToBottom,
  } = useAutoScroll([messages])

  const status = useAIStatus(conversationId)
  const displayMessages = messages
  const hasMessages = displayMessages.length > 0

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto relative"
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
      aria-atomic="false"
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={conversationId ?? 'empty'}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={springs.smooth}
        >
          {isLoading && !hasMessages ? (
            <div className="flex flex-col justify-center items-center h-full space-y-3 py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
              <div className="text-text-muted text-sm">Loading messages...</div>
            </div>
          ) : !hasMessages ? (
            <div className="flex flex-col justify-center items-center h-full space-y-2 py-20">
              <div className="text-4xl">💬</div>
              <div className="text-text-muted font-medium">No messages yet</div>
              <div className="text-text-dim text-sm">Send a message to start the conversation</div>
            </div>
          ) : (
            <div className="chat-column">
              {displayMessages.map((message) => {
                return (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    onRetry={message.streamError ? onRetry : undefined}
                    onCancel={message.streamError ? onCancel : undefined}
                    ariaLabel={`${message.role} message${message.status ? `, ${message.status}` : ''}`}
                  />
                );
              })}

              {/* Response Timeline + Activity Log — shown after the last message */}
              {status.phase !== 'idle' && (
                <div className="space-y-2 pt-2">
                  <ResponseTimeline status={status} />
                  <AIActivityLog status={status} />
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {showScrollButton && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-6 right-6 glass-elevated rounded-full p-2 shadow-glow-sm hover:bg-accent/20 transition-all duration-fast z-10"
          aria-label="Scroll to latest messages"
        >
          <svg className="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </button>
      )}
    </div>
  )
}

export const MessageList = memo(MessageListInner)
