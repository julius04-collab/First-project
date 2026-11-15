import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {LivingRoom, Chair} from '../components/Sets';
import {DOWN_L, DOWN_R} from '../components/Figure';
import {lerp2, ss} from '../lib/anim';
import {rel} from '../lib/timeline';
import {Stage, useT, WALL_FEET, WALL_SCALE} from './common';

// Scam call. The shadow facepalms; Leo hangs up.
export const Scene07: React.FC = () => {
  const t = useT();
  const tCall = rel(15, 7), tPalm = rel(17, 7), tLook = tPalm + 0.6, tHang = tPalm + 1.2;
  const onPhone = ss(tCall - 0.3, tCall + 0.2, t) * (1 - ss(tHang, tHang + 0.3, t));
  const nod = t > tCall + 1 && t < tPalm ? 6 * Math.sin(t * 7) : 0;
  const palm = ss(tPalm, tPalm + 0.18, t);
  const looked = t > tLook;
  return (
    <Stage cam={[1.05, 560, 1020]}>
      <LivingRoom />
      <Shadow id="s7" x={760} y={WALL_FEET} scale={WALL_SCALE}
        pose={{handL: lerp2(DOWN_L, [52, -150], palm), tilt: 14 * palm, lean: 6 * palm}} />
      <Chair x={900} y={1660} />
      <Leo x={430} y={1650} holding={onPhone > 0.5 ? 'phone' : null}
        pose={{handR: lerp2(DOWN_R, [44, -108], onPhone), handL: DOWN_L, tilt: nod + (looked ? -6 : 0)}}
        eyes={looked ? 'shocked' : 'normal'} look={looked ? [1, -0.3] : [0.2, 0]} mouth={looked ? 'o' : 'smile'}
        brows={looked ? [12, -4] : [0, 0]} />
    </Stage>
  );
};
