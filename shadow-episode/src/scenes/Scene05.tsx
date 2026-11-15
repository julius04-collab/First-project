import React from 'react';
import {Street, Bus, Dust, Commuter} from '../components/Sets';
import {lerp, ss} from '../lib/anim';
import {rel} from '../lib/timeline';
import {Stage, useT} from './common';

// The bus wobbles, skids and slides into the ditch. Everyone climbs out, dusty.
export const Scene05: React.FC = () => {
  const t = useT();
  const tSkid = rel(11, 5) + 1.2, tThud = tSkid + 1.0, tOut = rel(12, 5) - 0.2;
  const drive = ss(0, tSkid, t);
  let x = lerp(-500, 520, drive), y = 1395, rot = 0, wob = 0;
  if (t < tSkid) wob = 2.5 * Math.sin(t * 9) * ss(0.5, tSkid, t);
  if (t >= tSkid) {
    const k = ss(tSkid, tThud, t);
    x = lerp(520, 760, k); y = lerp(1395, 1760, k * k); rot = lerp(0, 24, k);
  }
  const shake = t > tThud && t < tThud + 0.4 ? 10 * Math.sin((t - tThud) * 60) : 0;
  const people = [0, 1, 2].map((i) => {
    const k = ss(tOut + i * 0.55, tOut + i * 0.55 + 0.6, t);
    return {k, x: 520 + i * 150, c: ['#e8a33a', '#5bb07a', '#b06ad9'][i], hair: ['#2b1d14', '#d9a066', '#1d1d1d'][i]};
  });
  return (
    <Stage cam={[1, 540 + shake, 960 + shake * 0.5]}>
      <Street variant="road" scroll={t * 60} />
      {t < tSkid && Array.from({length: 4}).map((_, i) => (
        <rect key={i} x={x - 600 - i * 70} y={1100 + i * 60} width={120} height={10} rx={5} fill="#ffffff" opacity={0.7} />
      ))}
      {t >= tSkid && t < tThud && Array.from({length: 5}).map((_, i) => (
        <line key={i} x1={x - 520} y1={y - 300 + i * 70} x2={x - 700} y2={y - 330 + i * 70} stroke="#1b1b2a" strokeWidth={8} strokeLinecap="round" />
      ))}
      {people.map((p, i) => p.k > 0 && (
        <g key={i} transform={`translate(0,${(1 - p.k) * 260})`}>
          <Commuter x={p.x} y={1560} c={p.c} hair={p.hair} />
          <ellipse cx={p.x - 20} cy={1250} rx={20} ry={12} fill="#9b9488" opacity={0.8} />
          {t > tOut + i * 0.55 + 0.6 && <circle cx={p.x + 60} cy={1180 - ((t * 60) % 40)} r={18} fill="#d8cdb6" opacity={0.7} />}
        </g>
      ))}
      <Bus x={x} y={y} rot={rot} wobble={wob} />
      <Dust x={760} y={1700} t={t - tThud} size={1.3} />
    </Stage>
  );
};
