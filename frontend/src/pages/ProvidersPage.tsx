import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { providersApi } from '../api/providers'
import ProviderList from '../components/Providers/ProviderList'
import ProviderForm from '../components/Providers/ProviderForm'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import { showError, showSuccess } from '../utils/toast'

function ProvidersPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingProvider, setEditingProvider] = useState<{
    id: number
    name: string
    type: string
    api_key?: string
    base_url?: string | null
    is_active?: boolean
    default_model?: string
    timeout?: number
    priority?: number
    max_retries?: number
    organization_id?: string
  } | null>(null)
  const queryClient = useQueryClient()

  const { data: providers, isLoading, error, refetch } = useQuery({
    queryKey: ['providers'],
    queryFn: providersApi.list,
  })

  const testMutation = useMutation({
    mutationFn: providersApi.test,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['providers'] })
      showSuccess(`Connection ${result.status}: ${result.message}`)
    },
    onError: (err) => {
      showError('Connection test failed', {
        description: err instanceof Error ? err.message : undefined,
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: providersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['providers'] })
      showSuccess('Provider deleted successfully')
    },
    onError: (err) => {
      showError('Failed to delete provider', {
        description: err instanceof Error ? err.message : undefined,
      })
    },
  })

  const discoverMutation = useMutation({
    mutationFn: providersApi.discoverModels,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['providers'] })
      showSuccess('Models discovered successfully')
    },
    onError: (err) => {
      showError('Failed to discover models', {
        description: err instanceof Error ? err.message : undefined,
      })
    },
  })

  const createMutation = useMutation({
    mutationFn: providersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['providers'] })
      setShowForm(false)
      showSuccess('Provider created successfully')
    },
    onError: (err) => {
      showError('Failed to create provider', {
        description: err instanceof Error ? err.message : undefined,
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      providersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['providers'] })
      setEditingProvider(null)
      setShowForm(false)
      showSuccess('Provider updated successfully')
    },
    onError: (err) => {
      showError('Failed to update provider', {
        description: err instanceof Error ? err.message : undefined,
      })
    },
  })

  const handleSubmit = (data: Record<string, unknown>) => {
    if (editingProvider) {
      updateMutation.mutate({ id: editingProvider.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const handleTest = async (id: number) => {
    try {
      await testMutation.mutateAsync(id)
      refetch()
    } catch {
      // Error handled in onError
    }
  }

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this provider?')) {
      deleteMutation.mutate(id)
    }
  }

  const handleDiscoverModels = async (id: number) => {
    try {
      await discoverMutation.mutateAsync(id)
      refetch()
    } catch {
      // Error handled in onError
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return <ErrorMessage message="Failed to load providers" />
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Providers</h1>
        <button
          onClick={() => {
            setEditingProvider(null)
            setShowForm(!showForm)
          }}
          className="px-4 py-2 bg-primary-500 text-white rounded hover:bg-primary-600"
        >
          {showForm ? 'Cancel' : 'Add Provider'}
        </button>
      </div>

      {showForm && (
        <ProviderForm
          onSubmit={handleSubmit}
          onCancel={() => {
            setShowForm(false)
            setEditingProvider(null)
          }}
          initialData={editingProvider ?? undefined}
        />
      )}

      <ProviderList
        providers={providers || []}
        onTest={handleTest}
        onDelete={handleDelete}
        onDiscoverModels={handleDiscoverModels}
      />
    </div>
  )
}

export default ProvidersPage
