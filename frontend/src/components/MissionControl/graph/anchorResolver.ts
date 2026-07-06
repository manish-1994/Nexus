import type { Point } from './graphModel';

export type AnchorDirection = 'top' | 'right' | 'bottom' | 'left';

export interface ResolvedAnchor {
  direction: AnchorDirection;
  position: Point;
}

/**
 * Calculates the exact coordinate on the boundary of the 80x96 agent card
 * closest and most optimal for the approach direction from a source point.
 */
export function resolveAnchor(
  cardCenter: Point,
  sourcePoint: Point
): ResolvedAnchor {
  const dx = cardCenter.x - sourcePoint.x;
  const dy = cardCenter.y - sourcePoint.y;

  let direction: AnchorDirection = 'left';
  const position: Point = { ...cardCenter };

  // Select the closest face based on approach angle vector
  if (Math.abs(dx) > Math.abs(dy)) {
    if (dx > 0) {
      direction = 'left';
      position.x = cardCenter.x - 40; // Half width of 80px card
    } else {
      direction = 'right';
      position.x = cardCenter.x + 40;
    }
  } else {
    if (dy > 0) {
      direction = 'top';
      position.y = cardCenter.y - 48; // Half height of 96px card
    } else {
      direction = 'bottom';
      position.y = cardCenter.y + 48;
    }
  }

  return { direction, position };
}
