import type { Message } from '../../types/chat'
import { MessageBubble } from './MessageBubble'
import { useAutoScroll } from '../../pages/hooks/useAutoScroll'

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
  onRetry?: () => void
  onCancel?: () => void
}

function MessageList({ messages, isLoading, onRetry, onCancel }: MessageListProps) {
  const {
    containerRef,
    bottomRef,
    handleScroll,
    showScrollButton,
    scrollToBottom
  } = useAutoScroll([messages])

  const displayMessages = messages

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto p-4 space-y-4 relative"
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
      aria-atomic="false"
    >
      {isLoading && messages.length === 0 ? (
        <div className="flex flex-col justify-center items-center h-full space-y-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <div className="text-gray-500 text-sm">Loading messages...</div>
        </div>
      ) : displayMessages.length === 0 ? (
        <div className="flex flex-col justify-center items-center h-full space-y-2">
          <div className="text-4xl">💬</div>
          <div className="text-gray-500 font-medium">No messages yet</div>
          <div className="text-gray-400 text-sm">Send a message to start the conversation</div>
        </div>
      ) : isLoading ? (
        <div className="space-y-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}>
              <div className="max-w-[75%] rounded-2xl px-4 py-3 space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
                  <div className="h-3 w-12 bg-gray-200 rounded animate-pulse" />
                </div>
                <div className="space-y-2">
                  <div className="h-3 w-48 bg-gray-200 rounded animate-pulse" />
                  <div className="h-3 w-64 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {displayMessages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onRetry={message.streamError ? onRetry : undefined}
              onCancel={message.streamError ? onCancel : undefined}
              ariaLabel={`${message.role} message${message.status ? `, ${message.status}` : ''}`}
            />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
      {showScrollButton && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 bg-white border border-gray-200 rounded-full p-2 shadow-lg hover:bg-gray-50 transition-colors"
          aria-label="Scroll to latest messages"
        >
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </button>
      )}
    </div>
  )
}

export default MessageList
