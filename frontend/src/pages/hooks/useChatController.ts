import { useState, useEffect, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { chatApi } from '../../api/chat'
import { useConversationManager } from './useConversationManager'
import { useOptimisticMessages } from './useOptimisticMessages'
import { useModelSelection } from './useModelSelection'
import { useAgentStore } from '../../stores/agentStore'
import { toast } from 'sonner'
import { Agent } from '../../types/agent'
import type { Message, Conversation } from '../../types/chat'

export function useChatController() {
  const queryClient = useQueryClient()
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null)
  const selectedConversationIdRef = useRef<number | null>(null)
  // Keep ref in sync so callbacks can read latest value without depending on state
  selectedConversationIdRef.current = selectedConversationId

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
    if (selectedConversationIdRef.current === id) {
      setSelectedConversationId(null)
    }
  }, [handleDeleteConversation])

  const handleSendMessage = useCallback(async (content: string) => {
    if (!selectedProviderId || !modelName) {
      toast.error('Please select a provider and model first')
      return
    }

    let conversationId = selectedConversationIdRef.current

    if (!conversationId) {
      const title = content.slice(0, 40) + (content.length > 40 ? '...' : '')
      const newConversation = await createNewConversation(title)
      conversationId = newConversation.id
      
      // PRE-SEED the messages cache BEFORE setting conversationId to prevent
      // useQuery from fetching before optimistic data is added
      queryClient.setQueryData<Message[]>(['messages', conversationId], [])
      
      setSelectedConversationId(conversationId)
    }

    const agents = queryClient.getQueryData<Agent[]>(['agents']) || []
    const agent = agents.find(a => a.id === selectedAgentId)
    const providerOverride = agent && selectedProviderId !== agent.provider_id ? selectedProviderId : undefined
    const modelOverride = agent && modelName && selectedModelId !== agent.preferred_model_id ? modelName : undefined
  
    await sendMessage(content, conversationId, selectedProviderId, modelName, selectedAgentId, providerOverride, modelOverride)
    
    // Check if title is "New Conversation", update if needed.
   const latestConversations = queryClient.getQueryData<Conversation[]>(['conversations']) || []
   const conversation = latestConversations.find(c => c.id === conversationId)
   if (conversation && (conversation.title === 'New Conversation' || !conversation.title)) {
     const title = content.slice(0, 40) + (content.length > 40 ? '...' : '')
     await chatApi.updateConversation(conversationId, { title })
     // Optimistic update instead of invalidate to avoid refetch race
     queryClient.setQueryData<Conversation[]>(['conversations'], (old = []) =>
       old.map(c => c.id === conversationId ? { ...c, title } : c)
     )
   }
  }, [
  createNewConversation,
  sendMessage,
  selectedProviderId,
  selectedModelId,
  modelName,
  selectedAgentId,
  queryClient
])

  const handleRetry = useCallback(async () => {
    const convId = selectedConversationIdRef.current
    if (!convId || !selectedProviderId || !modelName) return
  
    const agents = queryClient.getQueryData<Agent[]>(['agents']) || []
    const agent = agents.find(a => a.id === selectedAgentId)
    const providerOverride = agent && selectedProviderId !== agent.provider_id ? selectedProviderId : undefined
    const modelOverride = agent && modelName && selectedModelId !== agent.preferred_model_id ? modelName : undefined
  
    await retryMessage(convId, selectedProviderId, modelName, selectedAgentId, providerOverride, modelOverride)
  }, [selectedProviderId, modelName, selectedModelId, selectedAgentId, retryMessage, queryClient])

  const handleCancel = useCallback(() => {
    const convId = selectedConversationIdRef.current
    if (convId) {
      cancelStreaming(convId)
    }
  }, [cancelStreaming])

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

  // Keyboard shortcuts — uses refs for stable effect dependencies
  const handleNewConversationRef = useRef(handleNewConversation)
  handleNewConversationRef.current = handleNewConversation
  const handleDeleteRef = useRef(handleDelete)
  handleDeleteRef.current = handleDelete
  const handleCancelRef = useRef(handleCancel)
  handleCancelRef.current = handleCancel
  const isStreamingRef = useRef(isStreaming)
  isStreamingRef.current = isStreaming

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
      const modKey = isMac ? e.metaKey : e.ctrlKey

      if (modKey && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        handleNewConversationRef.current()
        return
      }

      if (modKey && e.shiftKey && e.key.toLowerCase() === 'c') {
        e.preventDefault()
        const convId = selectedConversationIdRef.current
        if (convId) {
          handleDeleteRef.current(convId)
        }
        return
      }

      if (e.key === '/' && document.activeElement?.tagName !== 'TEXTAREA' && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault()
        const searchInput = document.querySelector('input[aria-label="Search conversations"]') as HTMLInputElement
        searchInput?.focus()
        return
      }

      if (e.key === 'Escape' && isStreamingRef.current) {
        e.preventDefault()
        handleCancelRef.current()
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

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
