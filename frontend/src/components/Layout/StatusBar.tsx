import { useQuery } from '@tanstack/react-query'
import { healthApi } from '../../api/health'
import type { HealthResponse } from '../../api/health'

function StatusBar() {
  const { data: health } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: healthApi.check,
    retry: 1,
    refetchInterval: 60000,
  })

  const getStatusColor = (status?: string) => {
    if (!status) return 'text-gray-500'
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'connected':
        return 'text-green-600'
      case 'degraded':
      case 'warning':
        return 'text-yellow-600'
      case 'error':
      case 'disconnected':
        return 'text-red-600'
      default:
        return 'text-gray-500'
    }
  }

  return (
    <footer className="bg-white border-t border-gray-200 h-8 flex items-center justify-between px-4 text-xs">
      {/* Left section: Backend and Database status */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1.5">
          <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-green-500' : 'bg-gray-300'}`}></span>
          <span className="text-gray-600">Backend:</span>
          <span className={getStatusColor(health?.status)}>
            {health?.status || 'Unknown'}
          </span>
        </div>

        <div className="flex items-center space-x-1.5">
          <span className={`w-2 h-2 rounded-full ${health?.database === 'connected' ? 'bg-green-500' : 'bg-gray-300'}`}></span>
          <span className="text-gray-600">Database:</span>
          <span className={getStatusColor(health?.database)}>
            {health?.database || 'Unknown'}
          </span>
        </div>
      </div>

      {/* Center section: Current Provider and Model */}
      <div className="hidden md:flex items-center space-x-4">
        <div className="flex items-center space-x-1.5">
          <span className="text-gray-600">Provider:</span>
          <span className="text-gray-900 font-medium">OpenRouter</span>
        </div>

        <div className="flex items-center space-x-1.5">
          <span className="text-gray-600">Model:</span>
          <span className="text-gray-900 font-medium">gpt-4</span>
        </div>
      </div>

      {/* Right section: Version and Environment */}
      <div className="flex items-center space-x-4">
        <div className="hidden sm:flex items-center space-x-1.5">
          <span className="text-gray-600">Version:</span>
          <span className="text-gray-900 font-medium">{health?.version || '0.1.0'}</span>
        </div>

        <div className="flex items-center space-x-1.5">
          <span className="text-gray-600">Env:</span>
          <span className="text-gray-900 font-medium">{health?.environment || 'development'}</span>
        </div>
      </div>
    </footer>
  )
}

export default StatusBar
