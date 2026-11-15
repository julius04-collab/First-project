import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {Bedroom, BedFront} from '../components/Sets';
import {DOWN_L, DOWN_R} from '../components/Figure';
import {lerp2, popIn, ss} from '../lib/anim';
import {rel} from '../lib/timeline';
import {Stage, useT, WALL_FEET, WALL_SCALE} from './common';

// On camera the shadow is normal; phone down -> theatrical bow.
const PhoneBubble: React.FC<{t: number; show: number}> = ({show}) => {
  if (show <= 0.01) return null;
  return (
    <div style={{position: 'absolute', right: 60, top: 320, width: 330, height: 560, transform: `scale(${show})`, transformOrigin: 'top right'}}>
      <svg width={330} height={560} viewBox="0 0 330 560">
        <rect x={6} y={6} width={318} height={548} rx={44} fill="#2b2b38" stroke="#1b1b2a" strokeWidth={10} />
        <clipPath id="screen"><rect x={26} y={60} width={278} height={440} rx={16} /></clipPath>
        <g clipPath="url(#screen)">
          <rect x={26} y={60} width={278} height={440} fill="#f7d9a8" />
          <rect x={26} y={400} width={278} height={100} fill="#c98e57" />
          <g transform="translate(165,410) scale(0.42)">
            <Shadow id="bubble" x={0} y={0} />
          </g>
        </g>
        <circle cx={60} cy={92} r={10} fill="#ff4f6d" />
        <text x={80} y={100} fontFamily="Inter" fontWeight={900} fontSize={24} fill="#ff4f6d">REC</text>
        <circle cx={165} cy={528} r={14} fill="#555" />
      </svg>
    </div>
  );
};

export const Scene03: React.FC = () => {
  const t = useT();
  const tLower = rel(6, 3), tBow = tLower + 0.45;
  const lift = ss(0.3, 0.8, t) * (1 - ss(tLower, tLower + 0.35, t));
  const bow = ss(tBow, tBow + 0.5, t) * (1 - ss(tBow + 1.8, tBow + 2.3, t));
  const shocked = t > tBow + 0.3;
  const bubble = popIn(t - 0.7, 0.3) * (1 - ss(tLower - 0.1, tLower + 0.15, t));
  return (
    <Stage cam={[1.05, 560, 1020]} overlay={<PhoneBubble t={t} show={bubble} />}>
      <Bedroom />
      <Shadow id="s3" x={840} y={WALL_FEET} scale={WALL_SCALE}
        pose={{lean: 34 * bow, tilt: 22 * bow, hipY: -205 + 25 * bow, handL: lerp2(DOWN_L, [96, 40], bow), handR: lerp2(DOWN_R, [140, -70], bow)}} />
      <BedFront />
      <Leo x={560} y={1650} holding={lift > 0.05 ? 'phone' : null}
        pose={{handR: lerp2(DOWN_R, [70, -150], lift), handL: shocked ? [-70, 40] : DOWN_L}}
        eyes={shocked ? 'shocked' : 'normal'} mouthOpen={shocked ? ss(tBow + 0.3, tBow + 0.7, t) : 0} mouth={shocked ? 'open' : 'closed'}
        look={[1, -0.4]} brows={shocked ? [14, -4] : [0, 0]} />
    </Stage>
  );
};
