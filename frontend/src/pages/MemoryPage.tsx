function MemoryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text tracking-wider uppercase">Memory Engine</h1>
        <p className="text-text-muted mt-1 text-sm">Persistent knowledge and context management</p>
      </div>

      <div className="glass-surface rounded-card p-lg">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-secondary/15 border border-secondary/30 rounded-button">
            <svg className="w-8 h-8 text-secondary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-text mb-2">About Memory Engine</h2>
            <p className="text-text-muted mb-4 text-sm leading-relaxed">
              The Memory Engine provides persistent knowledge storage, enabling agents to recall past interactions, maintain context across sessions, and build long-term understanding.
            </p>

            <h3 className="text-md font-semibold text-text mb-2">Planned Capabilities</h3>
            <ul className="list-disc list-inside space-y-1 text-text-muted mb-4 text-sm">
              <li>Long-term conversation memory</li>
              <li>Semantic knowledge graphs</li>
              <li>Context-aware retrieval</li>
              <li>Memory prioritization and decay</li>
              <li>Cross-agent memory sharing</li>
              <li>Memory export and backup</li>
            </ul>

            <div className="flex items-center space-x-2">
              <span className="badge-warning">
                In Development
              </span>
              <span className="text-xs text-text-dim">Expected in Phase 4</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MemoryPage