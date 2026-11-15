import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {Bedroom, BedFront} from '../components/Sets';
import {DOWN_L} from '../components/Figure';
import {jitter, lerp2, ss} from '../lib/anim';
import {rel} from '../lib/timeline';
import {Stage, useT, WALL_FEET, WALL_SCALE} from './common';

export const flickerAt = (t: number, t0: number, t1: number) => {
  if (t < t0 || t > t1) return 1;
  const v = Math.sin(t * 47) * Math.sin(t * 23.3) + Math.sin(t * 91);
  return v > 0.35 ? 1 : v > -0.4 ? 0.35 : 0.05;
};

// Night: the lamp flickers, the shadow turns, points at Leo and trembles.
export const Scene10: React.FC = () => {
  const t = useT();
  const tTurn = rel(24, 10);
  const lamp = flickerAt(t, 0.3, 2.6);
  const turn = ss(tTurn, tTurn + 0.6, t);
  const squash = 1 - 0.8 * Math.sin(Math.PI * turn);
  const point = ss(tTurn + 0.7, tTurn + 1.2, t);
  const tr = t > tTurn + 1.0 ? 1 : 0;
  const jx = jitter(t, 1, 6 * tr), jy = jitter(t, 2, 4 * tr);
  const dim = 0.55 + 0.45 * lamp;
  return (
    <Stage cam={[1.08, 560, 1040]}>
      <g opacity={1}>
        <Bedroom night={1} lamp={lamp} />
        <g transform={`translate(${820 + jx},0) scale(${squash},1) translate(${-820},0)`}>
          <Shadow id="s10" x={820} y={WALL_FEET + jy} scale={WALL_SCALE} opacity={0.85 * (0.5 + 0.5 * dim)} color="#0b0b18"
            pose={{handL: lerp2(DOWN_L, [-170, -30], point), handR: [12 + jitter(t, 3, 8 * tr), 172], tilt: jitter(t, 4, 3 * tr)}} />
        </g>
        <BedFront night={1} lamp={lamp} />
        <Leo x={330} y={1500} pose={{legs: 'sit', hipY: -150, handL: [-30, 110], handR: [30, 110]}}
          eyes={t > tTurn + 1.2 ? 'scared' : 'normal'} look={t > tTurn ? [1, -0.3] : [0.5, 0]} sweat={t > tTurn + 2}
          mouth={t > tTurn + 2 ? 'wobble' : 'flat'} brows={t > tTurn + 1.2 ? [10, -10] : [0, 0]} />
        <rect x={-100} y={-100} width={1300} height={2200} fill="#000a20" opacity={0.45 * (1 - dim)} />
      </g>
    </Stage>
  );
};
