import { useQuery } from '@tanstack/react-query'
import { healthApi } from '../api/health'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'

function HomePage() {
  const { data: health, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.check,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return <ErrorMessage message="Failed to connect to backend" />
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Welcome to NEXUS V3</h2>
        <p className="text-gray-600 mb-4">
          Local-first AI Operating System - Phase 1 Foundation Complete
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">System Status</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="text-lg font-medium text-green-600">{health?.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Version</p>
            <p className="text-lg font-medium">{health?.version}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Database</p>
            <p className="text-lg font-medium">{health?.database}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Environment</p>
            <p className="text-lg font-medium">{health?.environment}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage
