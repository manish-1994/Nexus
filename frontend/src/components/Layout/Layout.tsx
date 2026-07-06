import { useState, ReactNode, Suspense, lazy } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import StatusBar from './StatusBar';
import { ErrorBoundary } from '../common/ErrorBoundary';

import { AmbientBackground } from '../Core/AmbientBackground';
import { SpotlightSearch } from '../common/SpotlightSearch';

const BackgroundScene = lazy(() => import('../Core/BackgroundScene'));

interface LayoutProps {
  children: ReactNode;
}

function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();
  const isChatRoute = location.pathname === '/chat';

  return (
    <div className="h-screen w-screen bg-background overflow-hidden flex flex-col relative z-0">
      {/* Global Spotlight Search */}
      <SpotlightSearch />

      {/* Ambient Background Layers (1 to 5) */}
      <AmbientBackground />

      {/* 3D Neural Particles Layer */}
      <ErrorBoundary fallback={null}>
        <Suspense fallback={null}>
          <BackgroundScene />
        </Suspense>
      </ErrorBoundary>

      
      {/* HUD decorative lines */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-[1]">
        <div className="hud-line" style={{ top: '15%', animationDelay: '0s' }} />
        <div className="hud-line" style={{ top: '35%', animationDelay: '1.5s', opacity: 0.5 }} />
        <div className="hud-line" style={{ top: '55%', animationDelay: '0.8s', opacity: 0.4 }} />
        <div className="hud-line" style={{ top: '75%', animationDelay: '2.2s', opacity: 0.3 }} />
      </div>

      {/* Top Bar */}
      <TopBar onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

      <div className="flex flex-1 overflow-hidden min-w-0">
        {/* Sidebar */}
        <AnimatePresence initial={false}>
          {sidebarOpen && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 280, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="flex-shrink-0 z-20 relative"
            >
              <Sidebar />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative z-10 min-w-0">
          {isChatRoute ? (
            /* Chat — full bleed, no glass wrapper */
            <div className="flex-1 flex flex-col overflow-hidden min-w-0">
              {children}
            </div>
          ) : (
            /* Other pages — glass surface card */
            <div className="flex-1 flex flex-col m-4 ml-0 min-w-0 min-h-0">
              <div className="glass-surface flex-1 rounded-card min-w-0 min-h-0 flex flex-col overflow-hidden">
                <div className={location.pathname === '/' ? "flex-1 flex flex-col min-h-0" : "p-8 overflow-y-auto flex-1 min-h-0"}>
                  {children}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Status Bar */}
      <div className="m-4 mt-0 z-20">
        <div className="glass-surface rounded-panel">
           <StatusBar />
        </div>
      </div>
    </div>
  );
}

export default Layout;