function ToolsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text tracking-wider uppercase">Tool Runtime</h1>
        <p className="text-text-muted mt-1 text-sm">Universal tool execution and management</p>
      </div>

      <div className="glass-surface rounded-card p-lg">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-warning/15 border border-warning/30 rounded-button">
            <svg className="w-8 h-8 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-text mb-2">About Tool Runtime</h2>
            <p className="text-text-muted mb-4 text-sm leading-relaxed">
              The Universal Tool Runtime enables agents to execute external tools — file operations, code execution, web search, terminal commands, and more — with full permission control and streaming support.
            </p>

            <h3 className="text-md font-semibold text-text mb-2">Available Tool Categories</h3>
            <ul className="list-disc list-inside space-y-1 text-text-muted mb-4 text-sm">
              <li>File System Operations</li>
              <li>Python Code Execution</li>
              <li>Web Search & Browsing</li>
              <li>Terminal Commands</li>
              <li>Memory Operations</li>
              <li>Custom Tool Integration</li>
            </ul>

            <div className="flex items-center space-x-2">
              <span className="badge-success">
                Operational
              </span>
              <span className="text-xs text-text-dim">Core runtime active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ToolsPage