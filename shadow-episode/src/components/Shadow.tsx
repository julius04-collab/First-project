import React from 'react';
import {RIG, Pose, solve, pathOf, pts} from './Figure';
import {HAIR_PATH} from './Leo';

export const SHADOW_COLOR = '#1a1a2e';

export type ShadowProps = {
  id: string;
  x: number; y: number; scale?: number; pose?: Pose;
  /** extra SVG transform applied around the feet point (e.g. ground projection matrix) */
  project?: string;
  yawn?: number;         // 0..1 mouth-shaped gap in the head
  ponytail?: boolean;    // the girlfriend
  opacity?: number;
  color?: string;
  holding?: null | 'phone';
  thumbR?: null | 'up' | 'down';
  fingerR?: boolean;
  fingerL?: boolean;
};

const PONYTAIL = 'M50,-60 C120,-70 150,0 120,70 C110,30 90,-10 60,-20 Z';

/** Solid silhouette with the same outline as Leo but no face. Has its own independent poses. */
export const Shadow: React.FC<ShadowProps> = ({id, x, y, scale = 1, pose = {}, project, yawn = 0, ponytail, opacity = 0.85, color = SHADOW_COLOR, holding, thumbR, fingerR, fingerL}) => {
  const s = solve(pose);
  const R = RIG.HEAD_R;
  const c = color;
  const rot = (px: number, py: number): [number, number] => {
    const a = (s.lean * Math.PI) / 180;
    return [px * Math.cos(a) - py * Math.sin(a), s.pelvis[1] + px * Math.sin(a) + py * Math.cos(a)];
  };
  const torso = [rot(-RIG.SH - 6, -RIG.TORSO + 4), rot(RIG.SH + 6, -RIG.TORSO + 4), rot(ponytail ? 66 : 50, ponytail ? 10 : -6), rot(ponytail ? -66 : -50, ponytail ? 10 : -6)];
  const limb = (d: string, w: number) => <path d={d} stroke={c} strokeWidth={w} fill="none" strokeLinecap="round" strokeLinejoin="round" />;
  const maskId = `yawn-${id}`;
  return (
    <g transform={`translate(${x},${y}) ${project ?? ''} scale(${scale})`} opacity={opacity}>
      <defs>
        <mask id={maskId} maskUnits="userSpaceOnUse" x={-300} y={-300} width={600} height={600}>
          <rect x={-300} y={-300} width={600} height={600} fill="#fff" />
          {yawn > 0.02 && <ellipse cx={0} cy={36} rx={22 + 10 * yawn} ry={6 + 34 * yawn} fill="#000" />}
        </mask>
      </defs>
      {limb(pathOf(s.hipL, s.kneeL, s.footL), 40)}
      {limb(pathOf(s.hipR, s.kneeR, s.footR), 40)}
      {[s.footL, s.footR].map((f, i) => <ellipse key={i} cx={f[0] + (i ? 8 : -8)} cy={f[1] - 4} rx={38} ry={20} fill={c} />)}
      <rect x={-50} y={s.pelvis[1] - 18} width={100} height={44} rx={16} fill={c} />
      <polygon points={pts(...torso)} fill={c} stroke={c} strokeWidth={12} strokeLinejoin="round" />
      {limb(pathOf(s.shL, s.elL, s.hdL), 30)}
      {limb(pathOf(s.shR, s.elR, s.hdR), 30)}
      <circle cx={s.hdL[0]} cy={s.hdL[1]} r={19} fill={c} />
      <circle cx={s.hdR[0]} cy={s.hdR[1]} r={19} fill={c} />
      {thumbR && <rect x={s.hdR[0] - 9} y={thumbR === 'up' ? s.hdR[1] - 48 : s.hdR[1] + 4} width={18} height={44} rx={9} fill={c} />}
      {fingerR && <rect x={s.hdR[0] - 7} y={s.hdR[1] - 50} width={14} height={40} rx={7} fill={c} />}
      {fingerL && <rect x={s.hdL[0] - 7} y={s.hdL[1] - 50} width={14} height={40} rx={7} fill={c} />}
      {holding === 'phone' && <rect x={s.hdR[0] - 28} y={s.hdR[1] - 82} width={56} height={100} rx={10} fill={c} />}
      {limb(pathOf(s.neckBase, [s.head[0], s.head[1] + R - 8]), 26)}
      <g transform={`translate(${s.head[0]},${s.head[1]}) rotate(${s.tilt})`} mask={`url(#${maskId})`}>
        <ellipse cx={-R + 2} cy={6} rx={20} ry={26} fill={c} />
        <ellipse cx={R - 2} cy={6} rx={20} ry={26} fill={c} />
        <circle r={R + 4} fill={c} />
        {ponytail ? (
          <>
            <path d={`M${-R - 4},-10 A${R + 6},${R + 8} 0 0 1 ${R + 4},-10 Z`} fill={c} />
            <path d={PONYTAIL} fill={c} />
            <circle cx={58} cy={-56} r={14} fill={c} />
          </>
        ) : (
          <path d={HAIR_PATH} fill={c} stroke={c} strokeWidth={8} strokeLinejoin="round" />
        )}
      </g>
    </g>
  );
};
