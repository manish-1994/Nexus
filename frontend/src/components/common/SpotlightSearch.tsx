import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Terminal, MessageSquare, Database, Settings2, Network, ArrowRight } from 'lucide-react';

interface SpotlightItem {
  name: string;
  url: string;
  icon: React.ElementType;
  description: string;
}

export function SpotlightSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const items: SpotlightItem[] = [
    { name: 'System Core', url: '/', icon: Terminal, description: 'OS Mission Control dashboard' },
    { name: 'Neural Chat', url: '/chat', icon: MessageSquare, description: 'Initiate cognitive conversation' },
    { name: 'Memory Vault', url: '/memory', icon: Database, description: 'Inspect conversation memory indexes' },
    { name: 'Provider Endpoints', url: '/providers', icon: Settings2, description: 'Configure LLM API integrations' },
    { name: 'Workflow Engine', url: '/workflows', icon: Network, description: 'Create and run execution graphs' }
  ];

  const filtered = items.filter(item => 
    item.name.toLowerCase().includes(query.toLowerCase()) ||
    item.description.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
      setSelectedIndex(0);
      setQuery('');
    }
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % Math.max(1, filtered.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        window.location.href = filtered[selectedIndex].url;
        setIsOpen(false);
      }
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4">
          {/* Backdrop blur */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            className="absolute inset-0 bg-background/70 backdrop-blur-md"
          />

          {/* Search container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 350 }}
            className="relative w-full max-w-xl glass-elevated rounded-panel overflow-hidden border border-accent/20 shadow-glow-lg"
          >
            {/* Input well */}
            <div className="flex items-center space-x-3 p-4 border-b border-white/5 bg-surface/50">
              <Search className="w-5 h-5 text-accent-light drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search modules, configurations, agents... [Enter]"
                aria-label="Spotlight search"
                className="flex-1 bg-transparent text-text font-heading text-sm placeholder-text-muted/70 outline-none caret-accent selection:bg-accent/30"
              />
              <span className="text-[9px] uppercase font-bold tracking-widest bg-white/5 border border-white/10 px-2 py-1 rounded-button text-text-muted">
                ESC
              </span>
            </div>

            {/* List */}
            <div className="max-h-[300px] overflow-y-auto p-2 bg-surface/20">
              {filtered.length === 0 ? (
                <div className="p-8 text-center text-xs text-text-muted uppercase tracking-widest">
                  No modules detected
                </div>
              ) : (
                filtered.map((item, idx) => {
                  const Icon = item.icon;
                  const isSelected = idx === selectedIndex;
                  return (
                    <div
                      key={item.name}
                      role="button"
                      tabIndex={0}
                      aria-label={`Navigate to ${item.name}`}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      onClick={() => {
                        window.location.href = item.url;
                        setIsOpen(false);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          window.location.href = item.url
                          setIsOpen(false)
                        }
                      }}
                      className={`flex items-center justify-between p-3 rounded-button cursor-pointer transition-all focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none ${
                        isSelected 
                          ? 'bg-accent/15 border border-accent/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]' 
                          : 'border border-transparent hover:bg-white/5'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-button ${isSelected ? 'bg-accent/20 text-accent-light' : 'bg-white/5 text-text-muted'}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="font-heading text-xs font-bold uppercase tracking-wider text-text">
                            {item.name}
                          </p>
                          <p className="text-[10px] text-text-muted mt-0.5 font-label">
                            {item.description}
                          </p>
                        </div>
                      </div>
                      {isSelected && (
                        <ArrowRight className="w-3.5 h-3.5 text-accent-light animate-pulse" />
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}