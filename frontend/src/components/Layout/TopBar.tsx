import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

interface TopBarProps {
  onMenuToggle: () => void
}

function TopBar({ onMenuToggle }: TopBarProps) {
  const location = useLocation()
  const [searchFocused, setSearchFocused] = useState(false)

  const getBreadcrumbs = () => {
    const path = location.pathname
    if (path === '/') return ['Dashboard']
    if (path === '/chat') return ['Chat']
    if (path === '/providers') return ['Providers']
    if (path === '/memory') return ['Memory']
    if (path === '/planner') return ['Planner']
    if (path === '/workflows') return ['Workflows']
    if (path === '/workspace') return ['Workspace']
    if (path === '/tools') return ['Tools']
    if (path === '/settings') return ['Settings']
    return ['Home']
  }

  const getCurrentModule = () => {
    const path = location.pathname
    const moduleMap: Record<string, string> = {
      '/': 'Dashboard',
      '/chat': 'Chat',
      '/providers': 'Providers',
      '/memory': 'Memory',
      '/planner': 'Planner',
      '/workflows': 'Workflows',
      '/workspace': 'Workspace',
      '/tools': 'Tools',
      '/settings': 'Settings',
    }
    return moduleMap[path] || 'NEXUS V3'
  }

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-4 sticky top-0 z-50">
      {/* Left section: Menu toggle + Breadcrumbs */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <nav className="hidden sm:flex items-center space-x-2 text-sm">
          <Link to="/" className="text-gray-500 hover:text-gray-700">
            Home
          </Link>
          {getBreadcrumbs().slice(1).map((crumb, index) => (
            <span key={index} className="flex items-center space-x-2">
              <span className="text-gray-400">/</span>
              <span className="text-gray-900 font-medium">{crumb}</span>
            </span>
          ))}
        </nav>

        <h1 className="text-lg font-semibold text-gray-900 sm:hidden">
          {getCurrentModule()}
        </h1>
      </div>

      {/* Right section: Search, Theme, Notifications, User */}
      <div className="flex items-center space-x-2">
        {/* Global Search */}
        <div className="hidden md:block relative">
          <input
            type="text"
            placeholder="Search..."
            className={`w-64 pl-10 pr-4 py-2 rounded-lg border ${
              searchFocused ? 'border-primary-500 ring-2 ring-primary-200' : 'border-gray-300'
            } focus:outline-none focus:ring-2 focus:ring-primary-200 text-sm`}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
          />
          <svg
            className="absolute left-3 top-2.5 w-4 h-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        {/* Theme Toggle */}
        <button
          className="p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          aria-label="Toggle theme"
        >
          <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
            />
          </svg>
        </button>

        {/* Notifications */}
        <button
          className="p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 relative"
          aria-label="Notifications"
        >
          <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* User Menu */}
        <button
          className="p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          aria-label="User menu"
        >
          <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        </button>
      </div>
    </header>
  )
}

export default TopBar
