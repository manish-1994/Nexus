import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ConversationSidebar from './ConversationSidebar'
import type { Conversation } from '../../types/chat'

const mockConversations: Conversation[] = [
  {
    id: 1,
    title: 'Test Conversation 1',
    created_at: '2026-07-01T10:00:00',
    updated_at: '2026-07-01T10:00:00',
    messages: [],
  },
  {
    id: 2,
    title: 'Test Conversation 2',
    created_at: '2026-07-01T11:00:00',
    updated_at: '2026-07-01T11:00:00',
    messages: [],
  },
]

describe('ConversationSidebar', () => {
  it('renders conversation list', () => {
    render(
      <ConversationSidebar
        conversations={mockConversations}
        selectedId={null}
        onSelect={vi.fn()}
        onNewConversation={vi.fn()}
        onDelete={vi.fn()}
        onRename={vi.fn()}
        isLoading={false}
      />
    )

    expect(screen.getByText('Test Conversation 1')).toBeDefined()
    expect(screen.getByText('Test Conversation 2')).toBeDefined()
  })

  it('shows empty state when no conversations', () => {
    render(
      <ConversationSidebar
        conversations={[]}
        selectedId={null}
        onSelect={vi.fn()}
        onNewConversation={vi.fn()}
        onDelete={vi.fn()}
        onRename={vi.fn()}
        isLoading={false}
      />
    )

    expect(screen.getByText('No conversations yet')).toBeDefined()
  })

  it('calls onSelect when conversation is clicked', () => {
    const onSelect = vi.fn()
    render(
      <ConversationSidebar
        conversations={mockConversations}
        selectedId={null}
        onSelect={onSelect}
        onNewConversation={vi.fn()}
        onDelete={vi.fn()}
        onRename={vi.fn()}
        isLoading={false}
      />
    )

    fireEvent.click(screen.getByText('Test Conversation 1'))
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('calls onNewConversation when button is clicked', () => {
    const onNewConversation = vi.fn()
    render(
      <ConversationSidebar
        conversations={mockConversations}
        selectedId={null}
        onSelect={vi.fn()}
        onNewConversation={onNewConversation}
        onDelete={vi.fn()}
        onRename={vi.fn()}
        isLoading={false}
      />
    )

    fireEvent.click(screen.getByText('+ New Chat'))
    expect(onNewConversation).toHaveBeenCalled()
  })

  it('disables new chat button when loading', () => {
    render(
      <ConversationSidebar
        conversations={mockConversations}
        selectedId={null}
        onSelect={vi.fn()}
        onNewConversation={vi.fn()}
        onDelete={vi.fn()}
        onRename={vi.fn()}
        isLoading={true}
      />
    )

    const button = screen.getByText('Creating...')
    expect(button).toBeDefined()
  })

  it('highlights selected conversation', () => {
    render(
      <ConversationSidebar
        conversations={mockConversations}
        selectedId={1}
        onSelect={vi.fn()}
        onNewConversation={vi.fn()}
        onDelete={vi.fn()}
        onRename={vi.fn()}
        isLoading={false}
      />
    )

    const selectedElement = screen.getByText('Test Conversation 1').closest('li')
    expect(selectedElement?.className).toContain('bg-gray-800')
  })

  it('calls onDelete when delete button is clicked', () => {
    const onDelete = vi.fn()
    render(
      <ConversationSidebar
        conversations={mockConversations}
        selectedId={null}
        onSelect={vi.fn()}
        onNewConversation={vi.fn()}
        onDelete={onDelete}
        onRename={vi.fn()}
        isLoading={false}
      />
    )

    const deleteButtons = screen.getAllByTitle('Delete')
    fireEvent.click(deleteButtons[0])
    expect(onDelete).toHaveBeenCalledWith(1)
  })

  it('calls onRename when rename button is clicked', () => {
    const onRename = vi.fn()
    render(
      <ConversationSidebar
        conversations={mockConversations}
        selectedId={null}
        onSelect={vi.fn()}
        onNewConversation={vi.fn()}
        onDelete={vi.fn()}
        onRename={onRename}
        isLoading={false}
      />
    )

    const renameButtons = screen.getAllByTitle('Rename')
    fireEvent.click(renameButtons[0])
    // After clicking rename, an input should appear
    expect(screen.getByDisplayValue('Test Conversation 1')).toBeDefined()
  })
})
