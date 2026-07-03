import { Provider } from '../../types/provider'

interface ProviderSelectorProps {
  providers: Provider[]
  selectedProviderId: number | null
  onProviderChange: (id: number) => void
  onDiscoverModels: () => void
  isLoading: boolean
}

export function ProviderSelector({
  providers,
  selectedProviderId,
  onProviderChange,
  onDiscoverModels,
  isLoading
}: ProviderSelectorProps) {
  const selectedProvider = providers.find(p => p.id === selectedProviderId)
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="block text-[10px] font-bold text-text-muted uppercase tracking-widest font-label">Provider</label>
        <button
          onClick={onDiscoverModels}
          disabled={!selectedProviderId || isLoading}
          className="px-3 py-1 bg-accent/20 border border-accent/40 text-accent-light text-[9px] font-bold tracking-widest uppercase rounded-lg hover:bg-accent/30 disabled:bg-white/5 disabled:text-text-muted/40 disabled:cursor-not-allowed transition-all"
        >
          {isLoading ? 'Syncing...' : 'Sync Models'}
        </button>
      </div>
      <div className="relative">
        <select
          value={selectedProviderId || ''}
          onChange={(e) => onProviderChange(Number(e.target.value))}
          className="w-full bg-elevated/40 text-text border border-white/10 rounded-xl px-3 py-2.5 text-xs font-heading tracking-wider focus:outline-none focus:ring-1 focus:ring-accent/30 focus:border-accent-light/50 transition-all appearance-none cursor-pointer"
        >
          <option value="" disabled className="bg-surface">Select a provider</option>
          {providers.map((provider) => (
            <option key={provider.id} value={provider.id} className="bg-surface text-text">
              {provider.name.toUpperCase()} ({provider.type.toUpperCase()})
            </option>
          ))}
        </select>
      </div>
      {selectedProvider && (
        <div className="mt-2 flex items-center gap-2 font-label">
          <span className={`w-1.5 h-1.5 rounded-full ${
            selectedProvider.health_status === 'active' ? 'bg-success animate-pulse' :
            selectedProvider.health_status === 'error' ? 'bg-danger' :
            selectedProvider.health_status === 'checking' ? 'bg-warning animate-pulse' :
            'bg-text-muted'
          }`} />
          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider">{selectedProvider.health_status}</span>
          <span className="text-[9px] text-text-muted/60 tracking-wider uppercase">• {selectedProvider.models?.length || 0} models</span>
        </div>
      )}
    </div>
  )
}
