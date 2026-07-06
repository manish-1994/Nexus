import { NexusReactorCore } from '../../Core/NexusReactorCore';
import type { ExecutionState } from '../../../types/mission-control';

interface ReactorCoreProps {
  cx: number;
  cy: number;
  shiftX: number;
  shiftY: number;
  reactorSize: number;
  coreState: ExecutionState;
  activeExecutions: any;
  coreBreathScale: number;
}


export function ReactorCore({
  cx,
  cy,
  shiftX,
  shiftY,
  reactorSize,
  coreState,
  activeExecutions,
  coreBreathScale
}: ReactorCoreProps) {
  return (
    <div
      className="absolute z-10 pointer-events-none"
      style={{
        left: cx + shiftX,
        top: cy + shiftY,
        transform: `translate(-50%,-50%) scale(${coreBreathScale})`,
      }}
    >
      <NexusReactorCore
        state={coreState}
        activeExecutions={activeExecutions}
        reactorSize={reactorSize}
      />
    </div>
  );
}
