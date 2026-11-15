import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {Bedroom, BedFront} from '../components/Sets';
import {EmojiPop} from '../components/Captions';
import {ss} from '../lib/anim';
import {rel} from '../lib/timeline';
import {Stage, useT, WALL_FEET, WALL_SCALE} from './common';

// Victory dance vs. the bored shadow leaning on the wall.
export const Scene02: React.FC = () => {
  const t = useT();
  const beat = 0.42;
  const b = Math.floor(t / beat), ph = (t / beat) % 1;
  const bounce = Math.abs(Math.sin(Math.PI * ph));
  const up = b % 2 === 0;
  const spin = b % 6 === 4 || b % 6 === 5;
  const handL: [number, number] = up ? [-30, -170] : [-90, -40];
  const handR: [number, number] = up ? [90, -40] : [30, -170];
  const tStare = rel(4, 2) - 0.2;
  return (
    <Stage cam={[1.05, 560, 1020]} overlay={<EmojiPop emoji="😐" x={830} y={560} t={t - tStare} size={130} />}>
      <Bedroom />
      <Shadow id="s2" x={840} y={WALL_FEET} scale={WALL_SCALE}
        pose={{lean: -9, handL: [86, 70], handR: [-86, 62], tilt: -10, legs: 'stand'}} />
      <BedFront />
      <Leo x={560} y={1650} flip={spin && b % 2 === 1}
        pose={{legs: 'dance', bend: bounce, hipY: -205 + 30 * bounce, handL, handR, tilt: up ? 8 : -8}}
        eyes="happy" mouth="grin" />
    </Stage>
  );
};
