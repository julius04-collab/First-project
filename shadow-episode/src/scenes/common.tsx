import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {FPS} from '../lib/timeline';

export const useT = () => useCurrentFrame() / FPS;

/** full-frame SVG stage with an optional camera (zoom around a world point) */
export const Stage: React.FC<{children: React.ReactNode; overlay?: React.ReactNode; cam?: [number, number, number]}> = ({children, overlay, cam}) => {
  const [z, cx, cy] = cam ?? [1, 540, 960];
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <g transform={`translate(540,960) scale(${z}) translate(${-cx},${-cy})`}>{children}</g>
      </svg>
      {overlay}
    </AbsoluteFill>
  );
};

/** wall-shadow anchor: shadow stands on the wall/floor seam, slightly larger than Leo */
export const WALL_FEET = 1385;
export const WALL_SCALE = 1.08;
/** ground projections (applied after translate to the feet) */
export const GROUND_BEHIND = 'matrix(1,0,-0.55,0.34,0,0)';
export const GROUND_BEHIND_L = 'matrix(1,0,0.55,0.34,0,0)';
