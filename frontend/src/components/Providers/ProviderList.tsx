import { Provider } from '../../types/provider'
import ProviderCard from './ProviderCard'

interface ProviderListProps {
  providers: Provider[]
  onTest: (id: number) => void
  onDelete: (id: number) => void
  onDiscoverModels: (id: number) => void
}

function ProviderList({ providers, onTest, onDelete, onDiscoverModels }: ProviderListProps) {
  if (providers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
        No providers configured. Add your first provider to get started.
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {providers.map((provider) => (
        <ProviderCard
          key={provider.id}
          provider={provider}
          onTest={onTest}
          onDelete={onDelete}
          onDiscoverModels={onDiscoverModels}
        />
      ))}
    </div>
  )
}

export default ProviderList
