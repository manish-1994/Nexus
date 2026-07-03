import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../api/health';
import { InteractiveCard3D } from '../components/common/Motion';
import { AICore, AICoreState } from '../components/Core/AICore';
import { 
  Activity, Database, Network, Sparkles, Terminal, Globe, Brain, HelpCircle, Eye, Mic, AlertTriangle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface FeedItem {
  id: string;
  time: string;
  type: string;
  message: string;
}

function DashboardPage() {
  const { isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.check,
  });

  const [coreState, setCoreState] = useState<AICoreState>('idle');
  const [feed, setFeed] = useState<FeedItem[]>([
    { id: '1', time: '16:08:12', type: 'system', message: 'Neural link established.' },
    { id: '2', time: '16:09:45', type: 'agent', message: 'Assistant instance initialized.' },
    { id: '3', time: '16:11:02', type: 'memory', message: 'SQLite database memory loaded.' }
  ]);
  const [telemetry, setTelemetry] = useState({
    cpu: 24,
    memory: 42,
    gpu: 18,
    tasks: 3,
    knowledge: 154,
    agentsOnline: 5
  });

  // Simulate active telemetry and event feed updates to make HUD feel alive
  useEffect(() => {
    const states: AICoreState[] = ['idle', 'thinking', 'streaming', 'executing', 'finished'];
    
    const interval = setInterval(() => {
      // Randomly cycle states to simulate core activity
      const nextState = states[Math.floor(Math.random() * states.length)];
      setCoreState(nextState);

      // Trigger telemetry updates
      setTelemetry(prev => ({
        ...prev,
        cpu: Math.max(10, Math.min(95, prev.cpu + Math.floor(Math.random() * 15 - 7))),
        memory: Math.max(30, Math.min(85, prev.memory + Math.floor(Math.random() * 5 - 2))),
        gpu: Math.max(5, Math.min(90, prev.gpu + Math.floor(Math.random() * 10 - 5))),
      }));

      // Random feed item addition
      const feedTemplates = [
        { type: 'agent', message: 'Cognitive agent executed plan successfully.' },
        { type: 'system', message: 'Telemetry updated: Latency verified.' },
        { type: 'memory', message: 'Memory index synced with sqlite store.' },
        { type: 'workflow', message: 'Workflow graph node transition complete.' },
        { type: 'provider', message: 'Switched preferred model preference.' }
      ];

      const template = feedTemplates[Math.floor(Math.random() * feedTemplates.length)];
      const now = new Date();
      const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
      
      setFeed(prev => [
        { id: Math.random().toString(), time: timeStr, type: template.type, message: template.message },
        ...prev.slice(0, 7)
      ]);
    }, 4500);

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-100px)]">
        <div className="flex flex-col items-center space-y-4">
          <div className="flex space-x-2">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                animate={{ scale: [1, 1.5, 1], opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                className="w-3 h-3 bg-accent rounded-full shadow-glow"
              />
            ))}
          </div>
          <span className="text-xs tracking-[0.2em] text-accent font-bold uppercase">Initializing Neural HUD...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-100px)]">
        <AlertTriangle className="w-12 h-12 text-danger mb-4 drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]" />
        <h2 className="text-xl font-bold text-white mb-2 tracking-widest uppercase">Connection Severed</h2>
        <p className="text-text-muted">Unable to establish telemetry link to backend server.</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6 max-w-[1600px] mx-auto overflow-y-auto max-h-[calc(100vh-120px)]">
      {/* Title */}
      <div className="flex justify-between items-center border-b border-white/5 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-text tracking-widest uppercase drop-shadow-md">Mission Control</h1>
          <p className="text-[10px] text-accent font-bold tracking-widest uppercase mt-1">Operational OS Command Node</p>
        </div>
        <div className="flex items-center space-x-2 text-[10px] uppercase font-bold tracking-widest bg-accent/10 border border-accent/20 px-3 py-1.5 rounded-lg text-accent-light">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span>Core Status: {coreState}</span>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        
        {/* Left Column: System Health & Running Tasks */}
        <div className="lg:col-span-3 space-y-6 flex flex-col justify-start h-auto">
          <InteractiveCard3D className="border border-white/5 bg-surface/30 p-5">
            <h2 className="text-[10px] font-bold text-text-muted tracking-widest uppercase mb-4 flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-accent" /> System Health
            </h2>
            <div className="space-y-4">
              {/* CPU */}
              <div>
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider mb-1">
                  <span className="text-text-muted">CPU Load</span>
                  <span className="text-accent-light">{telemetry.cpu}%</span>
                </div>
                <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-accent" 
                    animate={{ width: `${telemetry.cpu}%` }} 
                    transition={{ type: "spring", stiffness: 100 }}
                  />
                </div>
              </div>

              {/* Memory */}
              <div>
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider mb-1">
                  <span className="text-text-muted">Memory RAM</span>
                  <span className="text-secondary-light">{telemetry.memory}%</span>
                </div>
                <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-secondary" 
                    animate={{ width: `${telemetry.memory}%` }}
                    transition={{ type: "spring", stiffness: 100 }}
                  />
                </div>
              </div>

              {/* GPU */}
              <div>
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider mb-1">
                  <span className="text-text-muted">GPU Render</span>
                  <span className="text-success">{telemetry.gpu}%</span>
                </div>
                <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-success" 
                    animate={{ width: `${telemetry.gpu}%` }}
                    transition={{ type: "spring", stiffness: 100 }}
                  />
                </div>
              </div>
            </div>
          </InteractiveCard3D>

          <InteractiveCard3D className="border border-white/5 bg-surface/30 p-5">
            <h2 className="text-[10px] font-bold text-text-muted tracking-widest uppercase mb-4 flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-secondary" /> Active Directory
            </h2>
            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="p-3 bg-white/5 rounded-xl border border-white/5">
                <span className="text-[10px] text-text-muted uppercase tracking-widest">Tasks Running</span>
                <p className="text-2xl font-bold text-white mt-1">{telemetry.tasks}</p>
              </div>
              <div className="p-3 bg-white/5 rounded-xl border border-white/5">
                <span className="text-[10px] text-text-muted uppercase tracking-widest">Knowledge Nodes</span>
                <p className="text-2xl font-bold text-white mt-1">{telemetry.knowledge}</p>
              </div>
              <div className="p-3 bg-white/5 rounded-xl border border-white/5 col-span-2">
                <span className="text-[10px] text-text-muted uppercase tracking-widest">Cognitive Agents Online</span>
                <p className="text-2xl font-bold text-accent-light mt-1">{telemetry.agentsOnline}</p>
              </div>
            </div>
          </InteractiveCard3D>
        </div>

        {/* Center: AI Core Hologram */}
        <div className="lg:col-span-6 flex flex-col items-center justify-center p-6 border border-white/5 bg-surface/10 rounded-2xl relative overflow-hidden">
          <div className="absolute inset-0 bg-radial-gradient opacity-10 pointer-events-none" />
          <AICore state={coreState} />
          
          <div className="mt-6 text-center space-y-1">
            <h3 className="text-xs uppercase tracking-[0.3em] font-bold text-accent-light drop-shadow-md">Nexus Core v4.0</h3>
            <p className="text-[10px] text-text-muted uppercase tracking-widest">System heartbeat pulsing on state &quot;{coreState}&quot;</p>
          </div>
        </div>

        {/* Right Column: Live Activity Feed */}
        <div className="lg:col-span-3">
          <InteractiveCard3D className="border border-white/5 bg-surface/30 p-5 h-full flex flex-col">
            <h2 className="text-[10px] font-bold text-text-muted tracking-widest uppercase mb-4 flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-warning" /> Activity Feed
            </h2>
            <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
              <AnimatePresence initial={false}>
                {feed.map((item) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="p-3 rounded-lg bg-elevated/40 border border-white/5 flex flex-col space-y-1"
                  >
                    <div className="flex justify-between items-center text-[9px] uppercase font-bold tracking-widest">
                      <span className="text-text-muted">{item.time}</span>
                      <span className={
                        item.type === 'system' ? 'text-success' :
                        item.type === 'agent' ? 'text-accent-light' : 'text-secondary-light'
                      }>{item.type}</span>
                    </div>
                    <p className="text-text leading-snug">{item.message}</p>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </InteractiveCard3D>
        </div>

      </div>

      {/* Bottom Row: Capability Modules */}
      <InteractiveCard3D className="border border-white/5 bg-surface/30 p-6">
        <h2 className="text-[10px] font-bold text-text-muted tracking-widest uppercase mb-6 flex items-center gap-2">
          <Brain className="w-3.5 h-3.5 text-accent-light" /> Capability Modules
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          {[
            { label: 'Web Browser', icon: Globe, active: true },
            { label: 'Vault Memory', icon: Database, active: true },
            { label: 'Python VM', icon: Terminal, active: false },
            { label: 'Neural Vision', icon: Eye, active: true },
            { label: 'Voice Audio', icon: Mic, active: false },
            { label: 'Task Planning', icon: HelpCircle, active: true },
            { label: 'Workflows', icon: Network, active: true }
          ].map((mod) => (
            <div 
              key={mod.label}
              className={`p-4 rounded-xl border flex flex-col items-center justify-center space-y-2 text-center transition-all ${
                mod.active 
                  ? 'bg-accent/10 border-accent/30 shadow-[0_0_15px_rgba(59,130,246,0.15)] hover:border-accent-light/50' 
                  : 'bg-white/5 border-white/5 opacity-50'
              }`}
            >
              <mod.icon className={`w-5 h-5 ${mod.active ? 'text-accent-light' : 'text-text-muted'}`} />
              <span className="text-[10px] font-bold uppercase tracking-wider text-text">{mod.label}</span>
              <span className={`text-[8px] uppercase tracking-wider font-bold ${mod.active ? 'text-success' : 'text-text-muted'}`}>
                {mod.active ? 'Armed' : 'Offline'}
              </span>
            </div>
          ))}
        </div>
      </InteractiveCard3D>
    </div>
  );
}

export default DashboardPage;
