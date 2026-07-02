import { useState, useRef, useEffect } from 'react'

interface MessageInputProps {
  onSend: (content: string) => void
  isLoading: boolean
  isStreaming: boolean
  onStopStreaming?: () => void
  canSend?: boolean
}

function MessageInput({ onSend, isLoading, isStreaming, onStopStreaming, canSend = true }: MessageInputProps) {
  const [content, setContent] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault()
  console.log('[MessageInput] handleSubmit content=', content.trim(), 'isLoading=', isLoading, 'isStreaming=', isStreaming)
  if (content.trim() && !isLoading) {
  onSend(content.trim())
  setContent('')
  if (textareaRef.current) {
  textareaRef.current.style.height = 'auto'
  }
  } else {
  console.log('[MessageInput] submit blocked')
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
    // Auto-grow textarea
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [isStreaming])

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <form onSubmit={handleSubmit} className="space-y-2">
        <div className="flex items-end space-x-2">
          <textarea
            ref={textareaRef}
            value={content}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            rows={1}
            disabled={isLoading}
            style={{ minHeight: '44px', maxHeight: '200px' }}
          />
          <div className="flex items-center space-x-2">
            <button
              type="submit"
              disabled={!content.trim() || isLoading || !canSend}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg px-5 py-2 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
            {isStreaming && onStopStreaming && (
              <button
                type="button"
                onClick={onStopStreaming}
                className="bg-red-600 hover:bg-red-700 text-white rounded-lg px-5 py-2 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
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

export default MessageInput
