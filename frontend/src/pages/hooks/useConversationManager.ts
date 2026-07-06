import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from '../../api/chat'
import type { Conversation } from '../../types/chat'
import { toast } from 'sonner'
import { useCallback, useState } from 'react'

export function useConversationManager() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'newest' | 'oldest'>('newest')

  const { data: conversations = [], isLoading: conversationsLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: chatApi.getConversations,
  })

  const { data: searchResults = [], isLoading: searchLoading } = useQuery({
    queryKey: ['conversations', 'search', searchQuery],
    queryFn: () => chatApi.searchConversations(searchQuery),
    enabled: searchQuery.trim().length > 0,
  })

  const createMutation = useMutation({
    mutationFn: chatApi.createConversation,
    // No onSuccess invalidate - we handle optimistic updates manually in handleNewConversation
    // to avoid race condition where refetch overwrites our optimistic replacement
  })

  const deleteMutation = useMutation({
    mutationFn: chatApi.deleteConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      toast.success('Conversation deleted')
    },
    onError: () => {
      toast.error('Failed to delete conversation')
    },
  })

  const renameMutation = useMutation({
    mutationFn: ({ id, title }: { id: number; title: string }) =>
      chatApi.updateConversation(id, { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      toast.success('Conversation renamed')
    },
    onError: () => {
      toast.error('Failed to rename conversation')
    },
  })

  const displayedConversations = searchQuery.trim() ? searchResults : conversations
  const isManagerLoading = conversationsLoading || searchLoading

  const handleNewConversation = useCallback(async (title: string = 'New Conversation') => {
    // Optimistic insert
    const tempId = Date.now()
    const tempConv = {
      id: tempId,
      title,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      message_count: 0,
    }
    queryClient.setQueryData<Conversation[]>(['conversations'], (old = []) => [tempConv, ...old])

    const realConv = await createMutation.mutateAsync({ title })
    
    // Replace temp with real
    queryClient.setQueryData<Conversation[]>(['conversations'], (old = []) => 
      old.map(c => c.id === tempId ? realConv : c)
    )
    return realConv
  }, [createMutation, queryClient])

  const handleDeleteConversation = useCallback(async (id: number) => {
    await deleteMutation.mutateAsync(id)
  }, [deleteMutation])

  const handleRenameConversation = useCallback(async (id: number, title: string) => {
    await renameMutation.mutateAsync({ id, title })
  }, [renameMutation])

  return {
    conversations,
    displayedConversations,
    searchQuery,
    setSearchQuery,
    sortBy,
    setSortBy,
    isManagerLoading,
    handleNewConversation,
    handleDeleteConversation,
    handleRenameConversation,
  }
}
