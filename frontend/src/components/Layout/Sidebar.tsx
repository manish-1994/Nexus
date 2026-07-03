import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, MessageSquare, Database, Settings2, ListTodo, Workflow, 
  File, FileText, Briefcase, CheckSquare, Zap, Terminal, Code, Globe, Settings 
} from 'lucide-react';
import { cn } from '../common/Motion';

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
      className="w-64 glass-elevated h-full m-4 rounded-2xl overflow-y-auto flex flex-col"
    >
      <div className="p-6 pb-2 flex items-center space-x-3">
        <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center shadow-glow">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold tracking-wider text-text">NEXUS</span>
      </div>

      <nav className="flex-1 p-4" aria-label="Main navigation">
        {navSections.map((section) => (
          <div key={section.title} className="mb-6">
            <h2 className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em] mb-3 px-3">
              {section.title}
            </h2>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      className={({ isActive }) =>
                        cn(
                          "group flex items-center space-x-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-300",
                          isActive 
                            ? "bg-accent/20 text-accent-light shadow-[inset_0_0_12px_rgba(59,130,246,0.2)]" 
                            : "text-text-muted hover:bg-surface hover:text-text"
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <motion.div 
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.95 }}
                            className={cn("transition-colors duration-300", isActive ? "text-accent-light" : "text-text-muted group-hover:text-accent-light")}
                          >
                            <Icon className="w-5 h-5" />
                          </motion.div>
                          <span>{item.label}</span>
                          {isActive && (
                            <motion.div 
                              layoutId="active-indicator"
                              className="absolute left-0 w-1 h-6 bg-accent rounded-r-full"
                              initial={false}
                              transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            />
                          )}
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
