function PlannerPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Planner Engine</h1>
        <p className="text-gray-600 mt-1">Intelligent task planning and execution</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">About Planner Engine</h2>
            <p className="text-gray-600 mb-4">
              The Planner Engine breaks down complex tasks into manageable steps, creates execution plans, and coordinates multi-step workflows to achieve user goals.
            </p>

            <h3 className="text-md font-semibold text-gray-900 mb-2">Planned Capabilities</h3>
            <ul className="list-disc list-inside space-y-1 text-gray-600 mb-4">
              <li>Task decomposition and planning</li>
              <li>Step-by-step execution tracking</li>
              <li>Dependency management</li>
              <li>Progress monitoring and reporting</li>
              <li>Adaptive replanning on failures</li>
              <li>Integration with workflow engine</li>
            </ul>

            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                In Development
              </span>
              <span className="text-sm text-gray-500">Expected in Phase 4</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PlannerPage
