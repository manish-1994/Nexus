function WorkspacePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Workspace</h1>
        <p className="text-gray-600 mt-1">File management and project organization</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-indigo-100 rounded-lg">
            <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">About Workspace</h2>
            <p className="text-gray-600 mb-4">
              The Workspace provides a unified environment for managing files, notes, projects, and tasks. Keep all your work organized and accessible in one place.
            </p>

            <h3 className="text-md font-semibold text-gray-900 mb-2">Planned Capabilities</h3>
            <ul className="list-disc list-inside space-y-1 text-gray-600 mb-4">
              <li>File browser with folder management</li>
              <li>Rich text note editor</li>
              <li>Project management dashboard</li>
              <li>Task tracking with priorities</li>
              <li>File versioning and history</li>
              <li>Collaboration features</li>
            </ul>

            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                In Development
              </span>
              <span className="text-sm text-gray-500">Expected in Phase 6</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WorkspacePage
