import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MessageList from './MessageList'
import type { Message } from '../../types/chat'

const mockMessages: Message[] = [
  {
    id: 1,
    role: 'user',
    content: 'Hello, AI!',
    created_at: '2026-07-01T10:00:00',
    updated_at: '2026-07-01T10:00:00',
  },
  {
    id: 2,
    role: 'assistant',
    content: 'Hello! How can I help you?',
    created_at: '2026-07-01T10:00:01',
    updated_at: '2026-07-01T10:00:01',
    provider: 'openrouter',
    model: 'gpt-4',
    tokens_used: 50,
  },
]

describe('MessageList', () => {
  it('renders loading state', () => {
    render(<MessageList messages={[]} isLoading={true} streamingContent="" />)
    expect(screen.getByText('Loading messages...')).toBeDefined()
  })

  it('renders empty state', () => {
    render(<MessageList messages={[]} isLoading={false} streamingContent="" />)
    expect(screen.getByText('No messages yet')).toBeDefined()
    expect(screen.getByText('Send a message to start the conversation')).toBeDefined()
  })

  it('renders messages', () => {
    render(<MessageList messages={mockMessages} isLoading={false} streamingContent="" />)
    expect(screen.getByText('Hello, AI!')).toBeDefined()
    expect(screen.getByText('Hello! How can I help you?')).toBeDefined()
  })

  it('displays user and assistant labels', () => {
    render(<MessageList messages={mockMessages} isLoading={false} streamingContent="" />)
    expect(screen.getByText('You')).toBeDefined()
    expect(screen.getByText('Assistant')).toBeDefined()
  })

  it('displays token usage when available', () => {
    render(<MessageList messages={mockMessages} isLoading={false} streamingContent="" />)
    expect(screen.getByText('50 tokens')).toBeDefined()
  })

  it('renders streaming content', () => {
    render(
      <MessageList
        messages={mockMessages}
        isLoading={false}
        streamingContent="Streaming response..."
      />
    )
    expect(screen.getByText('Streaming response...')).toBeDefined()
  })

  it('aligns user messages to the right', () => {
    render(<MessageList messages={mockMessages} isLoading={false} streamingContent="" />)
    const userMessage = screen.getByText('Hello, AI!').closest('div')?.parentElement
    expect(userMessage?.className).toContain('justify-end')
  })

  it('aligns assistant messages to the left', () => {
    render(<MessageList messages={mockMessages} isLoading={false} streamingContent="" />)
    const assistantMessage = screen.getByText('Hello! How can I help you?').closest('div')?.parentElement
    expect(assistantMessage?.className).toContain('justify-start')
  })
})
