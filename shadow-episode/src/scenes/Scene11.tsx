import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {Bedroom, BedFront, Hearts} from '../components/Sets';
import {TitleCard} from '../components/Captions';
import {DOWN_L, DOWN_R} from '../components/Figure';
import {jitter, lerp, lerp2, ss} from '../lib/anim';
import {rel} from '../lib/timeline';
import {Stage, useT, WALL_FEET, WALL_SCALE} from './common';

export const TWIST_OFFSET = (id: number) => rel(id, 11);

// Leo looks behind him: a second shadow with a ponytail waves shyly. Twist: it's the girlfriend.
export const Scene11: React.FC = () => {
  const t = useT();
  const tSecond = rel(26, 11), tWave = rel(27, 11), tTwist = tWave + 1.1, tWalk = tTwist + 0.4, tHug = tWalk + 1.4;
  const turnHead = ss(0.2, 2.0, t);
  const her = ss(tSecond - 0.2, tSecond + 0.6, t);
  const wave = t > tWave && t < tWave + 1.4 ? Math.sin((t - tWave) * 10) : 0;
  const warm = ss(tTwist, tTwist + 0.7, t);
  const night = 1 - 0.85 * warm;
  const walk = ss(tWalk, tHug, t);
  const shX = lerp(820, 330, walk);
  const scared = warm < 0.5;
  const tr = scared ? 1 : 0;
  return (
    <Stage cam={[1.08, 560, 1040]} overlay={<TitleCard text="MEET THE GIRLFRIEND 💕" t={t - (tTwist + 0.9)} dur={3.4} bg="#ff8fb3" />}>
      <Bedroom night={night} lamp={1} />
      <Shadow id="gf" x={170} y={WALL_FEET} scale={WALL_SCALE * 0.94} ponytail opacity={0.85 * her} color={warm > 0.5 ? '#1a1a2e' : '#0b0b18'}
        pose={{handR: t > tWave ? [60 + 18 * wave, -150] : DOWN_R, tilt: t > tWave ? 10 : 0, handL: [40, 90]}} />
      <Shadow id="s11" x={shX + jitter(t, 1, 5 * tr)} y={WALL_FEET} scale={WALL_SCALE} color={warm > 0.5 ? '#1a1a2e' : '#0b0b18'}
        pose={{legs: walk > 0 && walk < 1 ? 'walk' : 'stand', stride: 0.7, phase: t * 7,
          handL: walk >= 1 ? [-150, -40] : scared ? [-170, -30] : lerp2([-170, -30], DOWN_L, ss(tTwist, tTwist + 0.3, t)),
          handR: walk >= 1 ? [40, 60] : DOWN_R, tilt: walk >= 1 ? -10 : jitter(t, 4, 3 * tr), bob: walk >= 1 ? 2 * Math.sin(t * 4) : 0}} />
      {t > tHug && <Hearts x={250} y={720} t={t - tHug} />}
      <BedFront night={night} lamp={1} />
      <Leo x={330} y={1500} pose={{legs: 'sit', hipY: -150, handL: [-30, 110], handR: [30, 110], tilt: -14 * turnHead * (1 - ss(tTwist + 0.6, tTwist + 1.2, t))}}
        eyes={t > tTwist + 1.0 ? 'deadpan' : t > tSecond ? 'shocked' : 'scared'} look={t > tTwist + 1.0 ? [0, 0] : [-1, -0.5]}
        mouth={t > tTwist + 1.0 ? 'flat' : t > tSecond ? 'open' : 'wobble'} mouthOpen={t > tSecond && t < tTwist + 1.0 ? 0.6 : 0}
        sweat={t < tTwist + 1.0} brows={t > tTwist + 1.0 ? [0, 0] : [14, -10]} />
    </Stage>
  );
};
