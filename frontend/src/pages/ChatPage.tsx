import { useQuery } from '@tanstack/react-query'
import { chatApi } from '../api/chat'
import { useChatController } from './hooks/useChatController'
import { useModelSelection } from './hooks/useModelSelection'
import ConversationSidebar from '../components/Chat/ConversationSidebar'
import { MessageList } from '../components/Chat/MessageList'
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
    staleTime: Infinity,
    structuralSharing: false,
    // Prevent refetch on window focus/reconnect which can race with streaming
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  })

  const isLoading = isManagerLoading || messagesLoading

  if (isLoading && conversations.length === 0) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto"></div>
          <div className="text-text-muted text-sm">Loading conversations...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-1 overflow-hidden">
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
            <ConversationHeader conversationId={selectedConversationId} />
            <MessageList
              messages={messages}
              isLoading={messagesLoading}
              onRetry={handleRetry}
              onCancel={handleCancel}
              conversationId={selectedConversationId}
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
          <EmptyState
            onNewConversation={handleNewConversation}
            onSelectConversation={handleSelectConversation}
            conversations={conversations}
          />
        )}
      </div>
    </div>
  )
}

export default ChatPage
