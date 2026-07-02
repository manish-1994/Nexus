function WorkflowsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Workflow Engine</h1>
        <p className="text-gray-600 mt-1">Automate complex multi-step processes</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-green-100 rounded-lg">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">About Workflow Engine</h2>
            <p className="text-gray-600 mb-4">
              The Workflow Engine enables creation and execution of automated multi-step processes, combining AI capabilities with traditional automation tools.
            </p>

            <h3 className="text-md font-semibold text-gray-900 mb-2">Planned Capabilities</h3>
            <ul className="list-disc list-inside space-y-1 text-gray-600 mb-4">
              <li>Visual workflow builder</li>
              <li>Pre-built workflow templates</li>
              <li>Conditional branching and loops</li>
              <li>Integration with external APIs</li>
              <li>Scheduled workflow execution</li>
              <li>Workflow monitoring and logging</li>
            </ul>

            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                In Development
              </span>
              <span className="text-sm text-gray-500">Expected in Phase 5</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WorkflowsPage
