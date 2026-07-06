function WorkflowsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text tracking-wider uppercase">Workflow Engine</h1>
        <p className="text-text-muted mt-1 text-sm">Automate complex multi-step processes</p>
      </div>

      <div className="glass-surface rounded-card p-lg">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-success/15 border border-success/30 rounded-button">
            <svg className="w-8 h-8 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-text mb-2">About Workflow Engine</h2>
            <p className="text-text-muted mb-4 text-sm leading-relaxed">
              The Workflow Engine enables creation and execution of automated multi-step processes, combining AI capabilities with traditional automation tools.
            </p>

            <h3 className="text-md font-semibold text-text mb-2">Planned Capabilities</h3>
            <ul className="list-disc list-inside space-y-1 text-text-muted mb-4 text-sm">
              <li>Visual workflow builder</li>
              <li>Pre-built workflow templates</li>
              <li>Conditional branching and loops</li>
              <li>Integration with external APIs</li>
              <li>Scheduled workflow execution</li>
              <li>Workflow monitoring and logging</li>
            </ul>

            <div className="flex items-center space-x-2">
              <span className="badge-warning">
                In Development
              </span>
              <span className="text-xs text-text-dim">Expected in Phase 5</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WorkflowsPage