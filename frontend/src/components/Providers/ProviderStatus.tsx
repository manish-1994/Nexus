interface ProviderStatusProps {
  status: string
  message?: string
}

function ProviderStatus({ status, message }: ProviderStatusProps) {
  type StatusConfig = { color: string; icon: string; label: string }
  const statusConfigs: Record<string, StatusConfig> = {
    active: { color: 'text-green-600', icon: '✓', label: 'Active' },
    inactive: { color: 'text-gray-600', icon: '○', label: 'Inactive' },
    error: { color: 'text-red-600', icon: '✗', label: 'Error' },
    checking: { color: 'text-yellow-600', icon: '◌', label: 'Checking' },
  }
  const config = statusConfigs[status] || { color: 'text-gray-600', icon: '?', label: 'Unknown' }

  return (
    <div className={`flex items-center gap-2 ${config.color}`}>
      <span className="text-lg">{config.icon}</span>
      <span className="font-medium">{config.label}</span>
      {message && <span className="text-sm text-gray-500">- {message}</span>}
    </div>
  )
}

export default ProviderStatus
