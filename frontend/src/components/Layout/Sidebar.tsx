import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, MessageSquare, Database, Settings2, ListTodo, Workflow, 
  File, FileText, Briefcase, CheckSquare, Zap, Terminal, Code, Globe, Settings 
} from 'lucide-react';
import { cn, springs } from '../common/Motion';

interface NavItem {
  to: string;
  label: string;
  icon: React.ElementType;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const coreNavItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
  { to: '/memory', label: 'Memory', icon: Database },
  { to: '/providers', label: 'Providers', icon: Settings2 },
];

const intelligenceNavItems: NavItem[] = [
  { to: '/planner', label: 'Planner', icon: ListTodo },
  { to: '/workflows', label: 'Workflows', icon: Workflow },
];

const workspaceNavItems: NavItem[] = [
  { to: '/workspace', label: 'Files', icon: File },
  { to: '/notes', label: 'Notes', icon: FileText },
  { to: '/projects', label: 'Projects', icon: Briefcase },
  { to: '/tasks', label: 'Tasks', icon: CheckSquare },
];

const toolsNavItems: NavItem[] = [
  { to: '/tools', label: 'Capabilities', icon: Zap },
  { to: '/terminal', label: 'Terminal', icon: Terminal },
  { to: '/python', label: 'Python', icon: Code },
  { to: '/browser', label: 'Browser', icon: Globe },
];

const systemNavItems: NavItem[] = [
  { to: '/settings', label: 'Settings', icon: Settings },
  { to: '/developer', label: 'Developer', icon: Code },
];

const navSections: NavSection[] = [
  { title: 'Core', items: coreNavItems },
  { title: 'Intelligence', items: intelligenceNavItems },
  { title: 'Workspace', items: workspaceNavItems },
  { title: 'Tools', items: toolsNavItems },
  { title: 'System', items: systemNavItems },
];

function Sidebar() {
  return (
    <motion.aside 
      initial={{ x: -250, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={springs.gentle}
      className="w-64 glass-elevated h-full m-md rounded-panel overflow-y-auto overflow-x-hidden flex flex-col"
    >
      {/* Logo / Brand */}
      <div className="p-lg pb-sm flex items-center space-x-sm">
        <motion.div 
          whileHover={{ scale: 1.1, rotate: 5 }}
          transition={springs.smooth}
          className="w-8 h-8 rounded-button bg-accent flex items-center justify-center shadow-glow-sm"
        >
          <Zap className="w-5 h-5 text-white" />
        </motion.div>
        <span className="text-xl font-bold tracking-wider text-text font-heading">NEXUS</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-sm" aria-label="Main navigation">
        {navSections.map((section) => (
          <div key={section.title} className="mb-lg">
            <h2 className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em] mb-sm px-sm">
              {section.title}
            </h2>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.to} className="relative">
                    <NavLink
                      to={item.to}
                      className={({ isActive }) =>
                        cn(
                          "group relative flex items-center space-x-sm px-sm py-sm rounded-button text-sm font-medium transition-all duration-normal focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none",
                          isActive
                            ? "bg-accent/15 text-accent shadow-glow-sm"
                            : "text-text-muted hover:bg-surface/60 hover:text-text hover:translate-x-0.5"
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          {/* Animated left indicator */}
                          {isActive && (
                            <motion.div 
                              layoutId="active-indicator"
                              className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-accent rounded-r-full shadow-glow-sm"
                              initial={false}
                              transition={springs.smooth}
                            />
                          )}
                          {/* Animated icon */}
                          <motion.div 
                            whileHover={{ scale: 1.15 }}
                            whileTap={{ scale: 0.9 }}
                            transition={springs.instant}
                            className={cn(
                              "transition-colors duration-normal",
                              isActive ? "text-accent" : "text-text-muted group-hover:text-accent"
                            )}
                          >
                            <Icon className="w-5 h-5" />
                          </motion.div>
                          <span>{item.label}</span>
                        </>
                      )}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </motion.aside>
  );
}

export default Sidebar;
