import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import MessageInput from './MessageInput'

describe('MessageInput', () => {
  it('renders input and send button', () => {
    render(<MessageInput onSend={vi.fn()} isLoading={false} isStreaming={false} />)
    expect(screen.getByPlaceholderText('Type your message...')).toBeDefined()
    expect(screen.getByText('Send')).toBeDefined()
  })

  it('calls onSend when form is submitted', () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} isLoading={false} isStreaming={false} />)

    const input = screen.getByPlaceholderText('Type your message...')
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(screen.getByText('Send'))

    expect(onSend).toHaveBeenCalledWith('Test message')
  })

  it('clears input after sending', () => {
    render(<MessageInput onSend={vi.fn()} isLoading={false} isStreaming={false} />)
    const input = screen.getByPlaceholderText('Type your message...') as HTMLTextAreaElement
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.click(screen.getByText('Send'))
    expect(input.value).toBe('')
  })

  it('disables input and button when loading', () => {
    render(<MessageInput onSend={vi.fn()} isLoading={true} isStreaming={false} />)
    const input = screen.getByPlaceholderText('Type your message...')
    const button = screen.getByText('Sending...')
    expect(input).toBeDisabled()
    expect(button).toBeDefined()
  })

  it('does not send empty messages', () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} isLoading={false} isStreaming={false} />)
    fireEvent.click(screen.getByText('Send'))
    expect(onSend).not.toHaveBeenCalled()
  })

  it('does not send whitespace-only messages', () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} isLoading={false} isStreaming={false} />)
    const input = screen.getByPlaceholderText('Type your message...')
    fireEvent.change(input, { target: { value: '   ' } })
    fireEvent.click(screen.getByText('Send'))
    expect(onSend).not.toHaveBeenCalled()
  })
})
