import { useState, ReactNode, Suspense, lazy } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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

      
      {/* Top Bar */}
      <TopBar onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

      <div className="flex flex-1 overflow-hidden">
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
        <main className="flex-1 flex flex-col relative z-10 m-4 ml-0">
          <div className="glass-panel flex-1 rounded-2xl overflow-y-auto">
            <div className="p-8 h-full">
              {children}
            </div>
          </div>
        </main>
      </div>

      {/* Status Bar */}
      <div className="m-4 mt-0 z-20">
        <div className="glass-panel rounded-xl">
           <StatusBar />
        </div>
      </div>
    </div>
  );
}

export default Layout;
