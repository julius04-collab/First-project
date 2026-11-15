import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {LivingRoom, Chair, Fan, Dust} from '../components/Sets';
import {DOWN_L, DOWN_R} from '../components/Figure';
import {lerp, lerp2, ss} from '../lib/anim';
import {rel} from '../lib/timeline';
import {Stage, useT, WALL_FEET, WALL_SCALE} from './common';

// "This is MY apartment!" -> dragged out by the ankle -> fan crashes onto the empty chair.
export const Scene08: React.FC = () => {
  const t = useT();
  const tLine = rel(19, 8), tDrag = rel(20, 8), tFall = rel(21, 8) + 0.5, tHit = tFall + 0.45, tPeek = tHit + 0.9;
  const wobble = 3 * Math.sin(t * 6) * (1 + ss(0, tFall, t) * 3);
  const fanY = t < tFall ? 290 : lerp(290, 1340, ss(tFall, tHit, t) ** 2);
  const fanRot = t < tFall ? wobble : lerp(wobble, 30, ss(tFall, tHit, t));
  const broke = ss(tHit, tHit + 0.15, t);
  const doorOpen = ss(tDrag - 0.2, tDrag + 0.3, t);
  // shadow: points at door, grabs ankle and walks right dragging him
  const point = ss(0.1, 0.5, t) * (1 - ss(tDrag - 0.2, tDrag, t));
  const reach = ss(tDrag - 0.2, tDrag, t);
  const drag = ss(tDrag + 0.15, tDrag + 1.6, t);
  const sx = lerp(760, 1180, drag);
  // Leo
  const dragging = t >= tDrag + 0.15;
  const arguing = t >= tLine - 0.1 && t < tDrag;
  const lx = dragging ? lerp(560, 1350, drag) : 520;
  const flail = Math.sin(t * 22);
  return (
    <Stage cam={[1.05, 560, 1000]}>
      <LivingRoom doorOpen={doorOpen} />
      <Shadow id="s8" x={sx} y={WALL_FEET} scale={WALL_SCALE}
        pose={{legs: drag > 0 && drag < 1 ? 'walk' : 'stand', stride: 0.8, phase: t * 9, lean: drag > 0 && drag < 1 ? 12 : 0,
          handR: point > 0.01 ? lerp2(DOWN_R, [165, -40], point) : DOWN_R, handL: lerp2(DOWN_L, [-60, 160], reach)}} />
      <Fan x={520} y={fanY} spin={t * 600} wobble={fanRot} rod={t < tFall ? 140 : 40} />
      {t >= tFall && t < tHit && <line x1={520} y1={150} x2={520} y2={250} stroke="#1b1b2a" strokeWidth={14} />}
      <Chair x={520} y={1660} broken={broke} />
      <Dust x={520} y={1560} t={t - tHit} size={0.8} />
      {!dragging && (
        <Leo x={520} y={1640} pose={{legs: 'sit', hipY: -150, handL: arguing ? [-30, 175] : [-20, 120], handR: arguing ? [40, -40 + 20 * Math.sin(t * 12)] : [20, 120]}}
          eyes={arguing ? 'annoyed' : t > 0.6 ? 'normal' : 'normal'} look={arguing ? [0, 0] : [1, -0.3]}
          mouthOpen={arguing ? 0.35 + 0.35 * Math.abs(Math.sin(t * 10)) : 0} mouth={arguing ? 'open' : 'closed'} brows={arguing ? [0, 14] : [4, 0]} />
      )}
      {dragging && t < tPeek && (
        <Leo x={lx} y={1600} rotate={-82} pose={{handL: [-90 + 60 * flail, -150], handR: [90 - 60 * flail, -150]}}
          eyes="shocked" mouth="open" mouthOpen={0.8} brows={[16, -4]} look={[0, -1]} />
      )}
      {t >= tPeek && (
        <g>
          <clipPath id="door"><rect x={800} y={700} width={240} height={660} /></clipPath>
          <g clipPath="url(#door)">
            <Leo x={1010 - 60 * ss(tPeek, tPeek + 0.4, t)} y={1650} pose={{handL: [-30, 120]}} eyes="shocked" look={[-1, 0.4]} mouth="o" brows={[16, -4]} />
          </g>
          <rect x={782} y={682} width={18} height={678} fill="#fffaf0" stroke="#1b1b2a" strokeWidth={6} />
        </g>
      )}
    </Stage>
  );
};
