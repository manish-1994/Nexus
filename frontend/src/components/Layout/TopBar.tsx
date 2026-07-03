import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Menu, Search, Bell, User, Cpu } from 'lucide-react';
import { cn } from '../common/Motion';

interface TopBarProps {
  onMenuToggle: () => void;
}

function TopBar({ onMenuToggle }: TopBarProps) {
  const location = useLocation();
  const [searchFocused, setSearchFocused] = useState(false);

  const getBreadcrumbs = () => {
    const path = location.pathname;
    if (path === '/') return ['Dashboard'];
    if (path === '/chat') return ['Chat'];
    if (path === '/providers') return ['Providers'];
    if (path === '/memory') return ['Memory'];
    if (path === '/planner') return ['Planner'];
    if (path === '/workflows') return ['Workflows'];
    if (path === '/workspace') return ['Workspace'];
    if (path === '/tools') return ['Tools'];
    if (path === '/settings') return ['Settings'];
    return ['Home'];
  };

  const getCurrentModule = () => {
    const path = location.pathname;
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
    };
    return moduleMap[path] || 'NEXUS';
  };

  return (
    <header className="h-16 flex items-center justify-between px-6 mx-4 mt-4 glass-panel rounded-2xl z-50 sticky top-4">
      {/* Left section: Menu toggle + Breadcrumbs */}
      <div className="flex items-center space-x-4">
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onClick={onMenuToggle}
          className="p-2 rounded-xl text-text-muted hover:text-white hover:bg-surface transition-colors focus:outline-none"
          aria-label="Toggle menu"
        >
          <Menu className="w-5 h-5" />
        </motion.button>

        <nav className="hidden sm:flex items-center space-x-2 text-sm">
          <Link to="/" className="text-text-muted hover:text-white transition-colors font-medium">
            Home
          </Link>
          {getBreadcrumbs().slice(1).map((crumb, index) => (
            <span key={index} className="flex items-center space-x-2">
              <span className="text-white/20">/</span>
              <span className="text-white font-semibold tracking-wide">{crumb}</span>
            </span>
          ))}
        </nav>

        <h1 className="text-lg font-bold text-white sm:hidden tracking-wider">
          {getCurrentModule()}
        </h1>
      </div>

      {/* Right section: Search, System Status, Notifications, User */}
      <div className="flex items-center space-x-3">
        {/* Global Search */}
        <div className="hidden md:block relative">
          <motion.div
            animate={{ width: searchFocused ? 300 : 220 }}
            className="relative"
          >
            <input
              type="text"
              placeholder="Search..."
              className={cn(
                "w-full pl-10 pr-4 py-2 rounded-xl bg-surface/50 border border-white/10 text-sm text-white placeholder-text-muted transition-all outline-none",
                searchFocused ? "border-accent/50 ring-2 ring-accent/20 bg-surface shadow-glow" : "hover:bg-surface/80 hover:border-white/20"
              )}
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
            />
            <Search className={cn("absolute left-3 top-2.5 w-4 h-4 transition-colors", searchFocused ? "text-accent-light" : "text-text-muted")} />
          </motion.div>
        </div>

        {/* System Status / Agent */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="hidden lg:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-surface/50 border border-white/10 text-text-muted hover:text-white transition-colors"
        >
          <Cpu className="w-4 h-4 text-accent" />
          <span className="text-xs font-semibold tracking-wide">GEMINI 1.5 PRO</span>
        </motion.button>

        {/* Notifications */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="p-2 rounded-xl text-text-muted hover:text-white hover:bg-surface transition-colors relative"
          aria-label="Notifications"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-accent-light rounded-full shadow-[0_0_8px_rgba(96,165,250,0.8)]"></span>
        </motion.button>

        {/* User Menu */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="p-2 rounded-xl text-text-muted hover:text-white hover:bg-surface transition-colors bg-gradient-to-tr from-accent/20 to-transparent"
          aria-label="User menu"
        >
          <User className="w-5 h-5 text-accent-light" />
        </motion.button>
      </div>
    </header>
  );
}

export default TopBar;
