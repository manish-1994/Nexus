import { Provider } from '../../types/provider'
import { CapabilityBadge } from './CapabilityBadge'

interface ProviderCardProps {
  provider: Provider
  onTest: (id: number) => void
  onDelete: (id: number) => void
  onDiscoverModels: (id: number) => void
}

function ProviderCard({ provider, onTest, onDelete, onDiscoverModels }: ProviderCardProps) {
  const statusColors = {
    active: 'bg-green-100 text-green-800',
    inactive: 'bg-gray-100 text-gray-800',
    error: 'bg-red-100 text-red-800',
    checking: 'bg-yellow-100 text-yellow-800',
  }

  const capabilities = provider.capabilities || {}

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold">{provider.name}</h3>
          <p className="text-sm text-gray-500 capitalize">{provider.type}</p>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[provider.health_status as keyof typeof statusColors] || statusColors.checking}`}>
          {provider.health_status}
        </span>
      </div>

      {provider.base_url && (
        <p className="text-sm text-gray-600 mb-2 font-mono">{provider.base_url}</p>
      )}

      <div className="text-xs text-gray-500 space-y-1 mb-4">
        {provider.default_model && <p>Default: {provider.default_model}</p>}
        <p>Timeout: {provider.timeout}s | Priority: {provider.priority} | Retries: {provider.max_retries}</p>
      </div>

      {Object.keys(capabilities).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {Object.entries(capabilities).map(([key, value]) => (
            <CapabilityBadge key={key} capability={key} supported={value} />
          ))}
        </div>
      )}

      {provider.error_message && (
        <p className="text-sm text-red-600 mb-4">{provider.error_message}</p>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => onTest(provider.id)}
          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
        >
          Test
        </button>
        <button
          onClick={() => onDiscoverModels(provider.id)}
          className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
        >
          Discover Models
        </button>
        <button
          onClick={() => onDelete(provider.id)}
          className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
        >
          Delete
        </button>
      </div>
    </div>
  )
}

export default ProviderCard
