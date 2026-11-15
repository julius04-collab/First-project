import React from 'react';
import {Leo} from '../components/Leo';
import {Shadow} from '../components/Shadow';
import {Street, Bus} from '../components/Sets';
import {TitleCard} from '../components/Captions';
import {ss} from '../lib/anim';
import {rel} from '../lib/timeline';
import {Stage, useT, GROUND_BEHIND_L} from './common';

// Leo climbs out of the ditch; his shadow waits on the sidewalk, arms folded, tapping its foot.
export const Scene06: React.FC = () => {
  const t = useT();
  const rise = ss(0.1, 1.0, t);
  const tap = Math.max(0, Math.sin(t * 9)) * 16;
  const tCard = rel(13, 6) + 1.6;
  return (
    <Stage cam={[1.15, 540, 1180]} overlay={<TitleCard text="I TOLD YOU 🙄" t={t - tCard} dur={3.2} />}>
      <Street variant="road" />
      <Bus x={840} y={1830} rot={24} />
      <Shadow id="s6" x={430} y={1700} project={GROUND_BEHIND_L} scale={1.05}
        pose={{handL: [86, 70], handR: [-86, 62], tapR: tap, tilt: -6}} />
      <g transform={`translate(0,${(1 - rise) * 420})`}>
        <Leo x={600} y={1700} dusty sweat={t > 1.4} pose={{handL: [-40, 120], handR: [60, 120], tilt: -10}}
          eyes={t > 1.2 ? 'annoyed' : 'shocked'} look={[-0.8, 0.9]} mouth={t > 1.2 ? 'wobble' : 'o'} brows={[6, 10]} />
      </g>
    </Stage>
  );
};
