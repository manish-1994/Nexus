import { motion } from 'framer-motion'
import { Provider } from '../../types/provider'
import CapabilityBadge from './CapabilityBadge'
import ProviderIcon from './ProviderIcon'
import { springs } from '../common/Motion'

interface ProviderCardProps {
  provider: Provider
  onTest: (id: number) => void
  onDelete: (id: number) => void
  onDiscoverModels: (id: number) => void
}

function ProviderCard({ provider, onTest, onDelete, onDiscoverModels }: ProviderCardProps) {
  const statusColors = {
    active: 'badge-success',
    inactive: 'badge-neutral',
    error: 'badge-danger',
    checking: 'badge-warning',
  }

  const capabilities = provider.capabilities || {}
  const modelCount = provider.models?.length || 0

  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={springs.smooth}
      className="glass-surface rounded-card p-lg hover:shadow-glow-sm transition-shadow duration-normal card-hover"
    >
      <div className="flex justify-between items-start mb-md">
        <div className="flex items-center gap-sm">
          <ProviderIcon type={provider.type} className="w-8 h-8 text-2xl" />
          <div>
            <h3 className="text-lg font-semibold text-text font-heading">{provider.name}</h3>
            <p className="text-sm text-text-muted capitalize">{provider.type.replace(/_/g, ' ')}</p>
          </div>
        </div>
        <span className={statusColors[provider.health_status as keyof typeof statusColors] || statusColors.checking}>
          {provider.health_status}
        </span>
      </div>

      {provider.base_url && (
        <p className="text-sm text-text-muted mb-sm font-mono bg-surface/40 px-sm py-xs rounded-input">{provider.base_url}</p>
      )}

      <div className="grid grid-cols-2 gap-sm text-xs text-text-muted mb-md">
        {provider.default_model && (
          <div>
            <span className="font-medium text-text-dim">Default:</span> {provider.default_model}
          </div>
        )}
        <div>
          <span className="font-medium text-text-dim">Timeout:</span> {provider.timeout}s
        </div>
        <div>
          <span className="font-medium text-text-dim">Priority:</span> {provider.priority}
        </div>
        <div>
          <span className="font-medium text-text-dim">Retries:</span> {provider.max_retries}
        </div>
        <div>
          <span className="font-medium text-text-dim">Models:</span> {modelCount}
        </div>
        <div>
          <span className="font-medium text-text-dim">Status:</span>{' '}
          <span className={provider.is_active ? 'text-success' : 'text-text-muted'}>
            {provider.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      {Object.keys(capabilities).length > 0 && (
        <div className="flex flex-wrap gap-sm mb-md">
          {Object.entries(capabilities).map(([key, value]) => (
            <CapabilityBadge key={key} capability={key} supported={value} />
          ))}
        </div>
      )}

      {provider.error_message && (
        <div className="mb-md p-sm bg-danger/10 border border-danger/30 rounded-input">
          <p className="text-sm text-danger/80">{provider.error_message}</p>
        </div>
      )}

      <div className="flex gap-sm pt-sm border-t border-white/5">
        <button
          onClick={() => onTest(provider.id)}
          className="flex-1 px-sm py-xs bg-accent text-white rounded-button hover:bg-accent-dark text-sm font-medium transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
        >
          Test
        </button>
        <button
          onClick={() => onDiscoverModels(provider.id)}
          className="flex-1 px-sm py-xs bg-success text-white rounded-button hover:bg-success/80 text-sm font-medium transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-success/30 focus-visible:outline-none"
        >
          Discover Models
        </button>
        <button
          onClick={() => onDelete(provider.id)}
          className="px-sm py-xs bg-danger text-white rounded-button hover:bg-danger/80 text-sm font-medium transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-danger/30 focus-visible:outline-none"
        >
          Delete
        </button>
      </div>
    </motion.div>
  )
}

export default ProviderCard
