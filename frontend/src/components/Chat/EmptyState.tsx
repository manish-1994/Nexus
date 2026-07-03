

interface EmptyStateProps {
  onNewConversation: () => void
}

export function EmptyState({ onNewConversation }: EmptyStateProps) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="text-6xl">💬</div>
        <h2 className="text-2xl font-semibold text-gray-700">Welcome to NEXUS V4 Chat</h2>
        <p className="text-gray-500 max-w-md">
          Select a conversation from the sidebar or create a new one to start chatting with AI
        </p>
        <button
          onClick={onNewConversation}
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Start New Conversation
        </button>
      </div>
    </div>
  )
}
