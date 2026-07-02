import { useState } from 'react'
import { ReactNode } from 'react'
import TopBar from './TopBar'
import Sidebar from './Sidebar'
import StatusBar from './StatusBar'

interface LayoutProps {
  children: ReactNode
}

function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Top Bar */}
      <TopBar onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

      <div className="flex flex-1 overflow-hidden">
        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside
          className={`
            fixed lg:static inset-y-0 left-0 z-50
            transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            lg:translate-x-0 transition-transform duration-200 ease-in-out
            w-64 bg-white border-r border-gray-200
            pt-16 lg:pt-0
          `}
        >
          <div className="h-full overflow-y-auto pt-4 lg:pt-0">
            <Sidebar />
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>

      {/* Status Bar */}
      <StatusBar />
    </div>
  )
}

export default Layout
