import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {Street, BusStopFront, Bus, Commuter} from '../components/Sets';
import {DOWN_L, DOWN_R} from '../components/Figure';
import {lerp, lerp2, ss} from '../lib/anim';
import {rel, relEnd} from '../lib/timeline';
import {Stage, useT, GROUND_BEHIND} from './common';

// Bus stop: the shadow points at the bus and shakes its head; Leo gets on anyway.
export const Scene04: React.FC = () => {
  const t = useT();
  const tPoint = rel(7, 4) + 2.3, tLine = rel(9, 4), tOn = rel(10, 4);
  const busX = lerp(1700, 560, ss(0.3, tPoint - 0.3, t)) - (t > tOn + 0.9 ? 1500 * ss(tOn + 0.9, tOn + 2.4, t) ** 1.6 : 0);
  const doorOpen = ss(tPoint - 0.4, tPoint, t) * (1 - ss(tOn + 0.6, tOn + 0.9, t));
  // Leo walks in from the left, stops, argues, then boards
  const walkIn = ss(0, tPoint - 0.6, t);
  let lx = lerp(150, 520, walkIn), ly = 1720, sc = 1;
  const walking = t < tPoint - 0.6;
  const board = ss(tOn, tOn + 0.7, t);
  lx = lerp(lx, 600, board); ly = lerp(ly, 1440, board); sc = lerp(1, 0.86, board);
  const leoAlpha = 1 - ss(tOn + 0.5, tOn + 0.75, t);
  const arguing = t >= tLine - 0.1 && t < tOn;
  const waveOff = arguing ? [120 + 40 * Math.sin(t * 14), -90] as [number, number] : DOWN_R;
  // shadow: follows until tPoint, then stays put and points at the bus
  const sx = Math.min(lx, lerp(150, 520, ss(0, tPoint - 0.6, Math.min(t, tPoint))));
  const pointK = ss(tPoint, tPoint + 0.35, t);
  const shake = t > tPoint + 0.4 && t < tLine ? 14 * Math.sin((t - tPoint) * 16) : 0;
  const stride = walking ? 0.8 : board > 0 && board < 1 ? 0.6 : 0;
  const phase = t * 8;
  return (
    <Stage>
      <Street variant="stop" />
      <Commuter x={150} y={1500} c="#e8a33a" hair="#2b1d14" />
      <Commuter x={290} y={1520} c="#5bb07a" hair="#d9a066" />
      <Bus x={busX} y={1395} doorOpen={doorOpen} />
      {leoAlpha < 1 && t > tOn + 0.5 ? null : null}
      <BusStopFront />
      <Shadow id="s4" x={sx} y={1722} project={GROUND_BEHIND} scale={1}
        pose={{legs: 'walk', stride: t < tPoint ? stride : 0, phase, handR: lerp2(DOWN_R, [150, -110], pointK), tilt: shake}} />
      <g opacity={leoAlpha}>
        <Leo x={lx} y={ly} scale={sc} pose={{legs: 'walk', stride, phase, handR: waveOff, handL: DOWN_L}}
          eyes={arguing ? 'annoyed' : 'normal'} look={arguing ? [0.3, -1] : [1, 0]} mouthOpen={arguing ? 0.3 + 0.3 * Math.abs(Math.sin(t * 11)) : 0}
          mouth={arguing ? 'open' : 'smile'} />
      </g>
    </Stage>
  );
};
