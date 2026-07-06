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
      <div className="glass-surface rounded-card p-lg">
        <h2 className="text-xl font-semibold mb-4 text-text">Welcome to NEXUS V4</h2>
        <p className="text-text-muted mb-4">
          Local-first AI Operating System - Phase 
        </p>
      </div>

      <div className="glass-surface rounded-card p-lg">
        <h3 className="text-lg font-semibold mb-4 text-text">System Status</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-text-muted">Status</p>
            <p className="text-lg font-medium text-success">{health?.status}</p>
          </div>
          <div>
            <p className="text-sm text-text-muted">Version</p>
            <p className="text-lg font-medium text-text">{health?.version}</p>
          </div>
          <div>
            <p className="text-sm text-text-muted">Database</p>
            <p className="text-lg font-medium text-text">{health?.database}</p>
          </div>
          <div>
            <p className="text-sm text-text-muted">Environment</p>
            <p className="text-lg font-medium text-text">{health?.environment}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage