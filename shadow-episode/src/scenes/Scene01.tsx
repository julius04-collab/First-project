import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {Bedroom, BedFront} from '../components/Sets';
import {TitleCard} from '../components/Captions';
import {DOWN_L, DOWN_R} from '../components/Figure';
import {lerp2, ss} from '../lib/anim';
import {rel} from '../lib/timeline';
import {Stage, useT, WALL_FEET, WALL_SCALE} from './common';

// Leo raises his hand; the shadow yawns instead.
export const Scene01: React.FC = () => {
  const t = useT();
  const tRaise = rel(1, 1) + 0.15, tYawn = rel(2, 1);
  const bob = 3 * Math.sin(t * 3);
  const raise = ss(tRaise, tRaise + 0.45, t);
  const leoHand = lerp2(DOWN_L, [-40, -175], raise);
  const stretch = ss(tYawn, tYawn + 0.5, t);
  const yawn = Math.max(0, Math.sin(Math.PI * Math.min(1, Math.max(0, (t - tYawn - 0.1) / 1.4))));
  const shocked = t > tYawn + 0.55;
  return (
    <Stage cam={[1.05, 560, 1020]} overlay={<TitleCard text="WHAT IF YOUR SHADOW HAD A MIND OF ITS OWN?" t={t} dur={2.6} size={58} />}>
      <Bedroom />
      <Shadow id="s1" x={830} y={WALL_FEET} scale={WALL_SCALE} yawn={yawn}
        pose={{bob: stretch > 0 ? 0 : bob, handL: lerp2(DOWN_L, [-70, -165], stretch), handR: lerp2(DOWN_R, [70, -165], stretch), tilt: -8 * yawn}} />
      <BedFront />
      <Leo x={560} y={1650} pose={{bob, handL: leoHand}} eyes={shocked ? 'shocked' : 'normal'} mouth={shocked ? 'o' : 'smile'}
        look={shocked ? [1, -0.4] : [0, 0]} brows={shocked ? [12, -4] : [0, 0]} />
    </Stage>
  );
};
