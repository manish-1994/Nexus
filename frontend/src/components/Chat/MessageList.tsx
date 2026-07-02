import { useRef, useEffect, useMemo, memo } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Message } from '../../types/chat'

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
  streamingContent: string
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

const MessageBubble = memo(function MessageBubble({ message }: { message: Message }) {
  return (
    <div
      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 shadow-sm ${
          message.role === 'user'
            ? 'bg-blue-600 text-white rounded-br-sm'
            : message.role === 'assistant'
            ? 'bg-white text-gray-900 border border-gray-200 rounded-bl-sm'
            : 'bg-gray-100 text-gray-700 rounded-lg'
        }`}
      >
        <div className="flex items-center gap-2 mb-1">
          <div
            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              message.role === 'user'
                ? 'bg-blue-500 text-white'
                : message.role === 'assistant'
                ? 'bg-emerald-500 text-white'
                : 'bg-gray-400 text-white'
            }`}
          >
            {message.role === 'user' ? 'U' : message.role === 'assistant' ? 'AI' : 'S'}
          </div>
          <div className="text-xs font-semibold">
            {message.role === 'user' ? 'You' : message.role === 'assistant' ? 'Assistant' : 'System'}
          </div>
          <div className={`text-xs ${message.role === 'user' ? 'text-blue-100' : 'text-gray-500'}`}>
            {formatTime(message.created_at)}
          </div>
        </div>
        <div className="whitespace-pre-wrap break-words leading-relaxed prose prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {message.tokens_used && (
          <div className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-100' : 'text-gray-500'}`}>
            {message.tokens_used} tokens
          </div>
        )}
      </div>
    </div>
  )
})

function MessageList({ messages, isLoading, streamingContent }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const userHasScrolledUp = useRef(false)

  const handleScroll = () => {
    const el = containerRef.current
    if (!el) return
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    userHasScrolledUp.current = distanceFromBottom > 150
  }

  useEffect(() => {
    if (!userHasScrolledUp.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, streamingContent])

  const displayMessages = useMemo(() => {
    if (streamingContent) {
      const hasRealAssistant = messages.some((m) => m.role === 'assistant')
      if (hasRealAssistant) {
        const next = [...messages]
        const lastIdx = next.map((m) => m.role).lastIndexOf('assistant')
        if (lastIdx >= 0) {
          next[lastIdx] = { ...next[lastIdx], content: streamingContent }
        }
        return next
      }
      return [
        ...messages,
        { id: -1, role: 'assistant', content: streamingContent, created_at: new Date().toISOString() } as Message,
      ]
    }
    return messages
  }, [messages, streamingContent])

  return (
    <div ref={containerRef} onScroll={handleScroll} className="flex-1 overflow-y-auto p-4 space-y-4">
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
            <MessageBubble key={message.id} message={message} />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  )
}

export default MessageList
