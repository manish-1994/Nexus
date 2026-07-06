interface ProviderStatusProps {
  status: string
  message?: string
}

function ProviderStatus({ status, message }: ProviderStatusProps) {
  type StatusConfig = { color: string; icon: string; label: string }
  const statusConfigs: Record<string, StatusConfig> = {
    active: { color: 'text-success', icon: '✓', label: 'Active' },
    inactive: { color: 'text-text-muted', icon: '○', label: 'Inactive' },
    error: { color: 'text-danger', icon: '✗', label: 'Error' },
    checking: { color: 'text-warning', icon: '◌', label: 'Checking' },
  }
  const config = statusConfigs[status] || { color: 'text-text-muted', icon: '?', label: 'Unknown' }

  return (
    <div className={`flex items-center gap-2 ${config.color}`}>
      <span className="text-lg">{config.icon}</span>
      <span className="font-medium">{config.label}</span>
      {message && <span className="text-sm text-text-dim">- {message}</span>}
    </div>
  )
}

export default ProviderStatus
