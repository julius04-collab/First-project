import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {Bedroom, BedFront} from '../components/Sets';
import {DOWN_L, DOWN_R} from '../components/Figure';
import {lerp2, ss} from '../lib/anim';
import {Stage, useT, WALL_FEET, WALL_SCALE} from './common';

// Outfit check: Hawaiian = thumbs down, black = thumbs up.
export const Scene09: React.FC = () => {
  const t = useT();
  const tDown = 0.75, tSwap = 1.55, tUp = 1.95, tSigh = 2.8;
  const holding = t < tSwap ? 'hawaiian' : 'black';
  const lift = ss(0.05, 0.35, t);
  const thumb = t >= tUp ? 'up' : t >= tDown ? 'down' : null;
  const tk = t >= tUp ? ss(tUp, tUp + 0.2, t) : ss(tDown, tDown + 0.2, t) * (1 - ss(tSwap - 0.2, tSwap, t));
  return (
    <Stage cam={[1.05, 560, 1020]}>
      <Bedroom mirror />
      <Shadow id="s9" x={300} y={WALL_FEET} scale={WALL_SCALE} thumbR={thumb && tk > 0.5 ? thumb : null}
        pose={{handR: lerp2(DOWN_R, thumb === 'up' ? [50, -120] : [60, -40], tk), handL: [80, 70], tilt: thumb === 'down' ? -8 : 6}} />
      <BedFront />
      <Leo x={600} y={1650} holding={holding} pose={{handR: lerp2(DOWN_R, [10, -40], lift), handL: DOWN_L}}
        eyes={t > tSigh ? 'deadpan' : t > tDown + 0.3 && t < tSwap ? 'annoyed' : 'normal'} look={[-1, -0.2]}
        mouth={t > tSigh ? 'flat' : t > tDown + 0.3 && t < tSwap ? 'frown' : 'smile'} />
    </Stage>
  );
};
