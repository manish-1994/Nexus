import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../api/health';
import type { HealthResponse } from '../../api/health';
import { Activity, Database as DbIcon } from 'lucide-react';
import { cn } from '../common/Motion';

function StatusBar() {
  const { data: health } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: healthApi.check,
    retry: 1,
    refetchInterval: 60000,
  });

  const getStatusColor = (status?: string) => {
    if (!status) return 'bg-text-muted shadow-none';
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'connected':
        return 'bg-success shadow-[0_0_8px_rgba(34,197,94,0.8)]';
      case 'degraded':
      case 'warning':
        return 'bg-warning shadow-[0_0_8px_rgba(245,158,11,0.8)]';
      case 'error':
      case 'disconnected':
        return 'bg-danger shadow-[0_0_8px_rgba(239,68,68,0.8)]';
      default:
        return 'bg-text-muted shadow-none';
    }
  };

  return (
    <footer className="h-8 flex items-center justify-between px-4 text-[10px] font-medium tracking-wider text-text-muted bg-transparent">
      {/* Left section: Backend and Database status */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <span className={cn("w-1.5 h-1.5 rounded-full", getStatusColor(health?.status))}></span>
          <span className="uppercase flex items-center gap-1">
            <Activity className="w-3 h-3" />
            CORE: <span className="text-white">{health?.status || 'UNKNOWN'}</span>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className={cn("w-1.5 h-1.5 rounded-full", getStatusColor(health?.database))}></span>
          <span className="uppercase flex items-center gap-1">
            <DbIcon className="w-3 h-3" />
            MEM: <span className="text-white">{health?.database || 'UNKNOWN'}</span>
          </span>
        </div>
      </div>

      {/* Center section: Current Provider and Model */}
      <div className="hidden md:flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <span className="uppercase">PROVIDER:</span>
          <span className="text-accent-light bg-accent/10 px-2 py-0.5 rounded text-[9px]">OPENROUTER</span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="uppercase">MODEL:</span>
          <span className="text-white">CLAUDE 3 OPUS</span>
        </div>
      </div>

      {/* Right section: Version and Environment */}
      <div className="flex items-center space-x-6">
        <div className="hidden sm:flex items-center space-x-2">
          <span className="uppercase">BUILD:</span>
          <span className="text-white">{health?.version || '0.1.0'}</span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="uppercase">ENV:</span>
          <span className="text-white bg-surface border border-white/10 px-2 py-0.5 rounded text-[9px]">
            {health?.environment || 'DEV'}
          </span>
        </div>
      </div>
    </footer>
  );
}

export default StatusBar;
