function ToolsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tools</h1>
        <p className="text-gray-600 mt-1">Development and integration tools</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-orange-100 rounded-lg">
            <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">About Tools</h2>
            <p className="text-gray-600 mb-4">
              The Tools section provides development utilities, integrations, and advanced capabilities for power users and developers.
            </p>

            <h3 className="text-md font-semibold text-gray-900 mb-2">Planned Capabilities</h3>
            <ul className="list-disc list-inside space-y-1 text-gray-600 mb-4">
              <li>Integrated terminal emulator</li>
              <li>Python code execution environment</li>
              <li>Browser automation tools</li>
              <li>API testing and debugging</li>
              <li>Data visualization tools</li>
              <li>Plugin system for extensibility</li>
            </ul>

            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                In Development
              </span>
              <span className="text-sm text-gray-500">Expected in Phase 7</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ToolsPage
