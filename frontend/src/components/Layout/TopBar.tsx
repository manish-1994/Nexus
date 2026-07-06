import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Menu, Search, Bell, User, Cpu } from 'lucide-react';
import { cn, springs } from '../common/Motion';

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
    <header className="h-14 flex items-center justify-between px-lg mx-md mt-md glass-surface rounded-panel z-50 sticky top-md">
      {/* Left section: Menu toggle + Breadcrumbs */}
      <div className="flex items-center space-x-sm">
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          transition={springs.instant}
          onClick={onMenuToggle}
          className="p-sm rounded-button text-text-muted hover:text-text hover:bg-surface transition-colors focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
          aria-label="Toggle menu"
        >
          <Menu className="w-5 h-5" />
        </motion.button>

        <nav className="hidden sm:flex items-center space-x-2 text-sm">
          <Link to="/" className="text-text-muted hover:text-text transition-colors font-medium">
            Home
          </Link>
          {getBreadcrumbs().slice(1).map((crumb, index) => (
            <span key={index} className="flex items-center space-x-2">
              <span className="text-white/20">/</span>
              <span className="text-text font-semibold tracking-wide">{crumb}</span>
            </span>
          ))}
        </nav>

        <h1 className="text-lg font-bold text-text sm:hidden tracking-wider">
          {getCurrentModule()}
        </h1>
      </div>

      {/* Center section: Global Search — centered for HUD feel */}
      <div className="hidden md:block absolute left-1/2 -translate-x-1/2">
        <motion.div
          animate={{ width: searchFocused ? 320 : 240 }}
          transition={springs.smooth}
          className="relative"
        >
          <input
            type="text"
            placeholder="Search..."
            aria-label="Global search"
            className={cn(
              "w-full pl-10 pr-md py-sm rounded-input bg-surface/50 border text-sm text-text placeholder-text-muted/70 transition-all duration-normal outline-none",
              searchFocused
                ? "border-accent/40 ring-2 ring-accent/20 bg-surface shadow-glow-sm"
                : "hover:bg-surface/80 hover:border-[rgba(255,255,255,0.15)]"
            )}
            style={{ borderColor: searchFocused ? undefined : 'rgba(255,255,255,0.08)' }}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
          />
          <Search className={cn(
            "absolute left-3 top-2.5 w-4 h-4 transition-colors duration-normal",
            searchFocused ? "text-accent" : "text-text-muted"
          )} />
        </motion.div>
      </div>

      {/* Right section: System Status, Notifications, User — equal spacing */}
      <div className="flex items-center space-x-sm">
        {/* System Status / Agent */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          transition={springs.instant}
          className="hidden lg:flex items-center space-x-1.5 px-sm py-1.5 rounded-button bg-surface/50 border text-text-muted hover:text-text hover:border-accent/20 transition-all duration-normal"
          style={{ borderColor: 'rgba(255,255,255,0.08)' }}
          aria-label="Active model"
        >
          <Cpu className="w-4 h-4 text-accent" />
          <span className="text-xs font-semibold tracking-wide">GEMINI 1.5 PRO</span>
        </motion.button>

        {/* Notifications */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          transition={springs.instant}
          className="p-sm rounded-button text-text-muted hover:text-text hover:bg-surface transition-colors relative focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
          aria-label="Notifications"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent rounded-full shadow-glow-sm"></span>
        </motion.button>

        {/* User Menu */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          transition={springs.instant}
          className="p-sm rounded-button text-text-muted hover:text-text hover:bg-surface transition-colors bg-gradient-to-tr from-accent/20 to-transparent focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
          aria-label="User menu"
        >
          <User className="w-5 h-5 text-accent" />
        </motion.button>
      </div>
    </header>
  );
}

export default TopBar;
