import { useQuery } from '@tanstack/react-query'
import { chatApi } from '../api/chat'
import { useChatController } from './hooks/useChatController'
import { useModelSelection } from './hooks/useModelSelection'
import ConversationSidebar from '../components/Chat/ConversationSidebar'
import MessageList from '../components/Chat/MessageList'
import { MessageComposer } from '../components/Chat/MessageComposer'
import { ConversationHeader } from '../components/Chat/ConversationHeader'
import { EmptyState } from '../components/Chat/EmptyState'

function ChatPage() {
  const {
    selectedConversationId,
    handleSelectConversation,
    handleNewConversation,
    handleDeleteConversation,
    handleRenameConversation,
    handleSendMessage,
    handleRetry,
    handleCancel,
    displayedConversations,
    searchQuery,
    setSearchQuery,
    sortBy,
    setSortBy,
    isManagerLoading,
    isStreaming,
    conversations
  } = useChatController()

  const { selectedProviderId, selectedModel } = useModelSelection()

  const { data: messages = [], isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', selectedConversationId],
    queryFn: () => chatApi.getMessages(selectedConversationId!),
    enabled: selectedConversationId !== null,
  })

  const isLoading = isManagerLoading || messagesLoading

  if (isLoading && conversations.length === 0) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <div className="text-gray-500 text-sm">Loading conversations...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen">
      <ConversationSidebar
        conversations={displayedConversations}
        selectedId={selectedConversationId}
        onSelect={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDelete={handleDeleteConversation}
        onRename={handleRenameConversation}
        isLoading={isManagerLoading}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        sortBy={sortBy}
        onSortChange={setSortBy}
      />
      <div className="flex-1 flex flex-col">
        {selectedConversationId ? (
          <>
            <ConversationHeader />
            <MessageList
              messages={messages}
              isLoading={messagesLoading}
              onRetry={handleRetry}
              onCancel={handleCancel}
            />
            <MessageComposer
              onSend={handleSendMessage}
              isLoading={isStreaming}
              isStreaming={isStreaming}
              onStopStreaming={handleCancel}
              canSend={!!selectedProviderId && !!selectedModel}
            />
          </>
        ) : (
          <EmptyState onNewConversation={handleNewConversation} />
        )}
      </div>
    </div>
  )
}

export default ChatPage
