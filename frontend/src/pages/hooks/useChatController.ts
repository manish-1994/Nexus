import { useState, useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { chatApi } from '../../api/chat'
import { useConversationManager } from './useConversationManager'
import { useOptimisticMessages } from './useOptimisticMessages'
import { useModelSelection } from './useModelSelection'
import { useAgentStore } from '../../stores/agentStore'
import { toast } from 'sonner'
import { Agent } from '../../types/agent'

export function useChatController() {
  const queryClient = useQueryClient()
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null)

  const {
    conversations,
    displayedConversations,
    searchQuery,
    setSearchQuery,
    sortBy,
    setSortBy,
    isManagerLoading,
    handleNewConversation: createNewConversation,
    handleDeleteConversation,
    handleRenameConversation,
  } = useConversationManager()

  const {
    sendMessage,
    cancelStreaming,
    retryMessage,
    isStreaming,
  } = useOptimisticMessages(selectedConversationId)
  
  const { selectedProviderId, selectedModelId, selectedModel } = useModelSelection()
  const selectedAgentId = useAgentStore((state) => state.selectedAgentId)
  
  const modelName = selectedModel?.name || selectedModel?.display_name || null

  const handleSelectConversation = useCallback((id: number) => {
    setSelectedConversationId(id)
  }, [])

  const handleNewConversation = useCallback(async () => {
    const newConversation = await createNewConversation('New Conversation')
    setSelectedConversationId(newConversation.id)
  }, [createNewConversation])

  const handleDelete = useCallback(async (id: number) => {
    await handleDeleteConversation(id)
    if (selectedConversationId === id) {
      setSelectedConversationId(null)
    }
  }, [handleDeleteConversation, selectedConversationId])

  const handleSendMessage = useCallback(async (content: string) => {
    if (!selectedProviderId || !modelName) {
      toast.error('Please select a provider and model first')
      return
    }

    let conversationId = selectedConversationId

    if (!conversationId) {
      const title = content.slice(0, 40) + (content.length > 40 ? '...' : '')
      const newConversation = await createNewConversation(title)
      conversationId = newConversation.id
      setSelectedConversationId(conversationId)
    }

    const agents = queryClient.getQueryData<Agent[]>(['agents']) || []
    const agent = agents.find(a => a.id === selectedAgentId)
    const providerOverride = agent && selectedProviderId !== agent.provider_id ? selectedProviderId : undefined
    const modelOverride = agent && modelName && selectedModelId !== agent.preferred_model_id ? modelName : undefined
  
    await sendMessage(content, conversationId, selectedProviderId, modelName, selectedAgentId, providerOverride, modelOverride)
    
    // Check if title is "New Conversation", update if needed.
    const conversation = conversations.find(c => c.id === conversationId)
    if (conversation && (conversation.title === 'New Conversation' || !conversation.title)) {
      const title = content.slice(0, 40) + (content.length > 40 ? '...' : '')
      await chatApi.updateConversation(conversationId, { title })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    }
  }, [
  selectedConversationId,
  createNewConversation,
  sendMessage,
  selectedProviderId,
  selectedModelId,
  modelName,
  selectedAgentId,
  conversations,
  queryClient
])

  const handleRetry = useCallback(async () => {
    if (!selectedConversationId || !selectedProviderId || !modelName) return
  
    const agents = queryClient.getQueryData<Agent[]>(['agents']) || []
    const agent = agents.find(a => a.id === selectedAgentId)
    const providerOverride = agent && selectedProviderId !== agent.provider_id ? selectedProviderId : undefined
    const modelOverride = agent && modelName && selectedModelId !== agent.preferred_model_id ? modelName : undefined
  
    await retryMessage(selectedConversationId, selectedProviderId, modelName, selectedAgentId, providerOverride, modelOverride)
  }, [selectedConversationId, selectedProviderId, modelName, selectedModelId, selectedAgentId, retryMessage, queryClient])

  const handleCancel = useCallback(() => {
    if (selectedConversationId) {
      cancelStreaming(selectedConversationId)
    }
  }, [selectedConversationId, cancelStreaming])

  // Sync with URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const conversationId = params.get('conversation')
    if (conversationId) {
      const id = parseInt(conversationId)
      if (!isNaN(id)) {
        setSelectedConversationId(id)
      }
    }
  }, [])

  useEffect(() => {
    const url = new URL(window.location.href)
    if (selectedConversationId) {
      url.searchParams.set('conversation', selectedConversationId.toString())
    } else {
      url.searchParams.delete('conversation')
    }
    window.history.replaceState({}, '', url.toString())
  }, [selectedConversationId])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
      const modKey = isMac ? e.metaKey : e.ctrlKey

      if (modKey && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        handleNewConversation()
        return
      }

      if (modKey && e.shiftKey && e.key.toLowerCase() === 'c') {
        e.preventDefault()
        if (selectedConversationId) {
          handleDelete(selectedConversationId)
        }
        return
      }

      if (e.key === '/' && document.activeElement?.tagName !== 'TEXTAREA' && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault()
        const searchInput = document.querySelector('input[aria-label="Search conversations"]') as HTMLInputElement
        searchInput?.focus()
        return
      }

      if (e.key === 'Escape' && isStreaming) {
        e.preventDefault()
        handleCancel()
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleNewConversation, handleDelete, handleCancel, selectedConversationId, isStreaming])

  return {
    selectedConversationId,
    handleSelectConversation,
    handleNewConversation,
    handleDeleteConversation: handleDelete,
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
    conversations,
  }
}
