import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { chatApi } from '../api/chat'
import ConversationSidebar from '../components/Chat/ConversationSidebar'
import MessageList from '../components/Chat/MessageList'
import MessageInput from '../components/Chat/MessageInput'
import ProviderModelSelector from '../components/Chat/ProviderModelSelector'
import { useChatStore } from '../stores/chatStore'
import { useProviderStore } from '../stores/providerStore'
import { useModelStore } from '../stores/modelStore'
import { toast } from 'sonner'
import { parseProviderError } from '../utils/providerErrorParser'

function ChatPage() {
  const queryClient = useQueryClient()
  const { selectedProviderId } = useProviderStore()
  const { selectedModel } = useModelStore()
  const {
    conversations,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    fetchConversations,
    fetchMessages,
    sendMessage,
    retryMessage,
    cancelStreaming,
    clearError,
  } = useChatStore()

  useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

  useEffect(() => {
    if (error) {
      toast.error(error)
      clearError()
    }
  }, [error, clearError])

  const handleSelectConversation = (id: number) => {
    fetchMessages(id)
  }

  const handleSendMessage = async (content: string) => {
    console.log('[ChatPage] handleSendMessage content=', content, 'providerId=', selectedProviderId, 'model=', selectedModel?.name)
    if (!selectedProviderId) {
      toast.error('Please select a provider first')
      return
    }
    if (!selectedModel) {
      toast.error('Please select a model first')
      return
    }

    const modelName = selectedModel.name || selectedModel.display_name || ''
    if (!modelName) {
      toast.error('Invalid model selected')
      return
    }

    const state = useChatStore.getState()
    if (state.isStreaming) {
      console.log('[ChatPage] send blocked: already streaming')
      return
    }

    const current = state.currentConversation
    if (!current?.id) {
      const title = content.slice(0, 40) + (content.length > 40 ? '...' : '')
      console.log('[ChatPage] creating conversation title=', title)
      const newConversation = await chatApi.createConversation({ title })
      console.log('[ChatPage] conversation created id=', newConversation.id)
      useChatStore.setState({ currentConversation: newConversation })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      await sendMessage(newConversation.id, content, selectedProviderId, modelName)
    } else {
      const conversationId = current.id
      console.log('[ChatPage] using existing conversation id=', conversationId)
      await sendMessage(conversationId, content, selectedProviderId, modelName)
      const convo = useChatStore.getState().currentConversation
      if (convo && (convo.title === 'New Conversation' || !convo.title)) {
        const title = content.slice(0, 40) + (content.length > 40 ? '...' : '')
        const updated = await chatApi.updateConversation(conversationId, { title })
        useChatStore.setState({ currentConversation: updated })
        queryClient.invalidateQueries({ queryKey: ['conversations'] })
      }
    }
  }

  const handleNewConversation = async () => {
    const newConversation = await chatApi.createConversation({ title: 'New Conversation' })
    useChatStore.setState({ currentConversation: newConversation })
    queryClient.invalidateQueries({ queryKey: ['conversations'] })
    fetchMessages(newConversation.id)
  }

  const handleDeleteConversation = async (id: number) => {
    await chatApi.deleteConversation(id)
    if (useChatStore.getState().currentConversation?.id === id) {
      useChatStore.setState({ currentConversation: null })
    }
    // Immediately update Zustand store so sidebar re-renders without waiting for refetch
    const currentConversations = useChatStore.getState().conversations
    useChatStore.setState({
      conversations: currentConversations.filter((c) => c.id !== id),
    })
    queryClient.invalidateQueries({ queryKey: ['conversations'] })
    toast.success('Conversation deleted')
  }

  const handleRenameConversation = async (id: number, title: string) => {
    await chatApi.updateConversation(id, { title })
    queryClient.invalidateQueries({ queryKey: ['conversations'] })
    toast.success('Conversation renamed')
  }

  const handleRetry = async () => {
    await retryMessage()
  }

  const handleCancel = () => {
    cancelStreaming()
  }

  const currentConversation = useChatStore((state) => state.currentConversation)
  const selectedConversationId = currentConversation?.id ?? null
  
  // Auto-switch provider on credit/quota errors
  useEffect(() => {
    if (!error) return
    const parsed = parseProviderError(error)
    if (!parsed.canSwitchProvider || parsed.suggestedAction !== 'switch_provider') return
    if (!selectedProviderId) return
  
    const state = useProviderStore.getState()
    const alternative = state.providers
      .filter((p) => p.is_active && p.id !== selectedProviderId)
      .sort((a, b) => b.priority - a.priority)[0]
    if (!alternative) return
  
    const providerName = alternative.name || alternative.type
    toast.error(parsed.title, {
      description: parsed.description,
      action: {
        label: `Switch to ${providerName}`,
        onClick: () => {
          useProviderStore.getState().selectProvider(alternative.id)
          toast.success(`Switched to ${providerName}`)
        },
      },
    })
  }, [error, selectedProviderId])
  
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
        conversations={conversations}
        selectedId={selectedConversationId}
        onSelect={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDelete={handleDeleteConversation}
        onRename={handleRenameConversation}
        isLoading={isLoading}
      />

      <div className="flex-1 flex flex-col">
        {selectedConversationId ? (
          <>
            <div className="px-4 py-3 border-b border-gray-200 bg-white">
              <ProviderModelSelector />
            </div>
            <MessageList
              messages={messages}
              isLoading={isLoading}
              streamingContent={streamingContent}
              onRetry={handleRetry}
              onCancel={handleCancel}
            />
            <MessageInput
              onSend={handleSendMessage}
              isLoading={isStreaming}
              isStreaming={isStreaming}
              onStopStreaming={cancelStreaming}
              canSend={!!selectedProviderId && !!selectedModel}
            />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-3">
              <div className="text-6xl">💬</div>
              <h2 className="text-2xl font-semibold text-gray-700">Welcome to NEXUS V3 Chat</h2>
              <p className="text-gray-500 max-w-md">
                Select a conversation from the sidebar or create a new one to start chatting with AI
              </p>
              <button
                onClick={handleNewConversation}
                className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Start New Conversation
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatPage
