import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {Kitchen} from '../components/Sets';
import {TitleCard} from '../components/Captions';
import {DOWN_L, DOWN_R} from '../components/Figure';
import {lerp, lerp2, ss} from '../lib/anim';
import {rel, sceneEnd, sceneStart} from '../lib/timeline';
import {Stage, useT} from './common';

// Midnight pizza heist, foiled by two disapproving shadows.
export const Scene12: React.FC = () => {
  const t = useT();
  const dur = sceneEnd(12) - sceneStart(12);
  const tGrab = 2.6, tShadows = rel(29, 12) + 1.6, tBack = tShadows + 1.6;
  const sneak = ss(0.2, tGrab - 0.2, t);
  const lx = lerp(1000, 560, sneak);
  const grab = ss(tGrab, tGrab + 0.4, t) * (1 - ss(tBack, tBack + 1.6, t));
  const hasPizza = t > tGrab + 0.3 && t < tBack + 1.2;
  const sh = ss(tShadows, tShadows + 0.5, t);
  const wag = 24 * Math.sin(t * 9);
  const caught = t > tShadows + 0.4;
  return (
    <Stage cam={[1.05, 560, 1020]} overlay={<TitleCard text="WOULD YOU TRUST YOUR SHADOW? 👇" t={t - (dur - 2.4)} dur={3} y={260} size={60} />}>
      <Kitchen />
      {[{x: 700, gf: false}, {x: 880, gf: true}].map((s, i) => (
        <Shadow key={i} id={`k${i}`} x={s.x} y={1030} scale={0.82} ponytail={s.gf} opacity={0.85 * sh}
          pose={{handL: [86, 70], handR: [30 + wag, -125], tilt: -6}} fingerR />
      ))}
      <Leo x={lx} y={1680} flip holding={hasPizza ? 'pizza' : null}
        pose={{legs: sneak < 1 ? 'tiptoe' : 'stand', stride: sneak > 0 && sneak < 1 ? 0.7 : 0, phase: t * 7,
          handR: lerp2(sneak < 1 ? [40, -110] : DOWN_R, [150, -60], grab), handL: sneak < 1 ? [-40, -110] : DOWN_L, hipY: sneak < 1 ? -190 : -205}}
        eyes={caught ? 'shocked' : 'annoyed'} look={caught ? [-1, -0.3] : [1, 0]} mouth={caught ? 'o' : 'smile'}
        brows={caught ? [14, -6] : [0, 0]} sweat={caught} />
    </Stage>
  );
};
