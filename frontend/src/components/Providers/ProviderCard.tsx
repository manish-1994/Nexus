import { Provider } from '../../types/provider'
import CapabilityBadge from './CapabilityBadge'
import ProviderIcon from './ProviderIcon'

interface ProviderCardProps {
  provider: Provider
  onTest: (id: number) => void
  onDelete: (id: number) => void
  onDiscoverModels: (id: number) => void
}

function ProviderCard({ provider, onTest, onDelete, onDiscoverModels }: ProviderCardProps) {
  const statusColors = {
    active: 'bg-green-100 text-green-800 border-green-200',
    inactive: 'bg-gray-100 text-gray-800 border-gray-200',
    error: 'bg-red-100 text-red-800 border-red-200',
    checking: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  }

  const capabilities = provider.capabilities || {}
  const modelCount = provider.models?.length || 0

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <ProviderIcon type={provider.type} className="w-8 h-8 text-2xl" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{provider.name}</h3>
            <p className="text-sm text-gray-500 capitalize">{provider.type.replace(/_/g, ' ')}</p>
          </div>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${statusColors[provider.health_status as keyof typeof statusColors] || statusColors.checking}`}>
          {provider.health_status}
        </span>
      </div>

      {provider.base_url && (
        <p className="text-sm text-gray-600 mb-3 font-mono bg-gray-50 px-2 py-1 rounded">{provider.base_url}</p>
      )}

      <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 mb-4">
        {provider.default_model && (
          <div>
            <span className="font-medium">Default:</span> {provider.default_model}
          </div>
        )}
        <div>
          <span className="font-medium">Timeout:</span> {provider.timeout}s
        </div>
        <div>
          <span className="font-medium">Priority:</span> {provider.priority}
        </div>
        <div>
          <span className="font-medium">Retries:</span> {provider.max_retries}
        </div>
        <div>
          <span className="font-medium">Models:</span> {modelCount}
        </div>
        <div>
          <span className="font-medium">Status:</span>{' '}
          <span className={provider.is_active ? 'text-green-600' : 'text-gray-500'}>
            {provider.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      {Object.keys(capabilities).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {Object.entries(capabilities).map(([key, value]) => (
            <CapabilityBadge key={key} capability={key} supported={value} />
          ))}
        </div>
      )}

      {provider.error_message && (
        <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-700">{provider.error_message}</p>
        </div>
      )}

      <div className="flex gap-2 pt-2 border-t border-gray-100">
        <button
          onClick={() => onTest(provider.id)}
          className="flex-1 px-3 py-1.5 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm font-medium transition-colors"
        >
          Test
        </button>
        <button
          onClick={() => onDiscoverModels(provider.id)}
          className="flex-1 px-3 py-1.5 bg-green-500 text-white rounded hover:bg-green-600 text-sm font-medium transition-colors"
        >
          Discover Models
        </button>
        <button
          onClick={() => onDelete(provider.id)}
          className="px-3 py-1.5 bg-red-500 text-white rounded hover:bg-red-600 text-sm font-medium transition-colors"
        >
          Delete
        </button>
      </div>
    </div>
  )
}

export default ProviderCard
