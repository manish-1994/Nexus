import { useState } from 'react'
import type { Conversation } from '../../types/chat'

interface ConversationSidebarProps {
  conversations: Conversation[]
  selectedId: number | null
  onSelect: (id: number) => void
  onNewConversation: () => void
  onDelete: (id: number) => void
  onRename: (id: number, title: string) => void
  isLoading: boolean
}

function ConversationSidebar({
  conversations,
  selectedId,
  onSelect,
  onNewConversation,
  onDelete,
  onRename,
  isLoading,
}: ConversationSidebarProps) {
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingTitle, setEditingTitle] = useState('')

  const handleStartRename = (conversation: Conversation) => {
    setEditingId(conversation.id)
    setEditingTitle(conversation.title)
  }

  const handleSaveRename = (id: number) => {
    if (editingTitle.trim()) {
      onRename(id, editingTitle.trim())
    }
    setEditingId(null)
    setEditingTitle('')
  }

  const handleKeyDown = (e: React.KeyboardEvent, id: number) => {
    if (e.key === 'Enter') {
      handleSaveRename(id)
    } else if (e.key === 'Escape') {
      setEditingId(null)
      setEditingTitle('')
    }
  }

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <button
          onClick={onNewConversation}
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 font-medium transition-colors"
        >
          {isLoading ? 'Creating...' : '+ New Chat'}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 flex flex-col items-center justify-center h-full text-center">
            <div className="text-4xl mb-2">📭</div>
            <div className="text-gray-400 text-sm font-medium">No conversations yet</div>
            <div className="text-gray-500 text-xs mt-1">Create a new chat to get started</div>
          </div>
        ) : (
          <ul className="space-y-1 p-2">
            {conversations.map((conversation) => (
              <li
                key={conversation.id}
                className={`group rounded-lg px-3 py-2 cursor-pointer transition-colors ${
                  selectedId === conversation.id
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                {editingId === conversation.id ? (
                  <input
                    type="text"
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onBlur={() => handleSaveRename(conversation.id)}
                    onKeyDown={(e) => handleKeyDown(e, conversation.id)}
                    autoFocus
                    className="w-full bg-gray-700 text-white rounded px-2 py-1 text-sm"
                  />
                ) : (
                  <div
                    className="flex items-center justify-between"
                    onClick={() => onSelect(conversation.id)}
                  >
                    <span className="truncate text-sm flex-1">{conversation.title}</span>
                    <div className="hidden group-hover:flex items-center space-x-1 ml-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleStartRename(conversation)
                        }}
                        className="text-gray-400 hover:text-white p-1"
                        title="Rename"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onDelete(conversation.id)
                        }}
                        className="text-gray-400 hover:text-red-400 p-1"
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default ConversationSidebar
