import React from 'react';
import {V2} from '../lib/anim';
import {Pose, RIG, solve, pathOf, pts} from './Figure';

export const INK = '#1b1b2a';
const SKIN0 = '#f2c9a0';
const SHIRT0 = '#8ec5f5';
const PANTS0 = '#4a4f5c';
const HAIR0 = '#7a4a26';
const SKIN = SKIN0;

export type Eyes = 'normal' | 'shocked' | 'annoyed' | 'scared' | 'closed' | 'happy' | 'deadpan';
export type Mouth = 'closed' | 'smile' | 'open' | 'o' | 'frown' | 'grin' | 'wobble' | 'flat';
export type Holding = null | 'phone' | 'hawaiian' | 'black' | 'pizza';

export type LeoProps = {
  x: number; y: number; scale?: number; pose?: Pose;
  eyes?: Eyes; mouth?: Mouth; mouthOpen?: number; look?: V2; brows?: [number, number];
  holding?: Holding; sweat?: boolean; dusty?: boolean; rotate?: number; flip?: boolean;
  colors?: {skin?: string; shirt?: string; pants?: string; hair?: string};
};

const hairPath = (() => {
  const R = RIG.HEAD_R;
  const p: string[] = [];
  const n = 13;
  for (let i = 0; i <= n; i++) {
    const a = ((200 + (i * 140) / n) * Math.PI) / 180;
    const r = i === 0 || i === n ? R - 4 : R + (i % 2 ? 26 : 6);
    p.push(`${(Math.cos(a) * r).toFixed(1)},${(Math.sin(a) * r).toFixed(1)}`);
  }
  // fringe dipping onto the forehead
  p.push('62,-30', '40,-20', '28,-40', '6,-24', '-14,-42', '-34,-26', '-58,-34', '-74,-20');
  return 'M' + p.join(' L') + 'Z';
})();
export const HAIR_PATH = hairPath;

const Limb: React.FC<{d: string; w: number; color: string}> = ({d, w, color}) => (
  <>
    <path d={d} stroke={INK} strokeWidth={w + 12} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    <path d={d} stroke={color} strokeWidth={w} fill="none" strokeLinecap="round" strokeLinejoin="round" />
  </>
);

const HawaiianShirt: React.FC<{x: number; y: number; kind: 'hawaiian' | 'black'}> = ({x, y, kind}) => (
  <g transform={`translate(${x},${y - 30})`}>
    <path d="M-80,-60 L-40,-80 L40,-80 L80,-60 L95,-10 L60,0 L60,110 L-60,110 L-60,0 L-95,-10 Z" fill={kind === 'black' ? '#22222c' : '#ff7a3d'} stroke={INK} strokeWidth={6} strokeLinejoin="round" />
    {kind === 'hawaiian' && (
      <>
        {[[-35, -30], [25, -10], [-20, 50], [35, 70], [-45, 85]].map(([fx, fy], i) => (
          <g key={i} transform={`translate(${fx},${fy})`}>
            {[0, 72, 144, 216, 288].map((a) => (
              <ellipse key={a} cx={Math.cos((a * Math.PI) / 180) * 11} cy={Math.sin((a * Math.PI) / 180) * 11} rx={9} ry={9} fill={i % 2 ? '#ffe14d' : '#ff4fa0'} />
            ))}
            <circle r={6} fill="#ffffff" />
          </g>
        ))}
        <path d="M10,10 q30,-30 50,0 q-20,10 -50,0" fill="#2fbf71" />
      </>
    )}
    <path d="M-40,-80 L0,-40 L40,-80" fill="none" stroke={INK} strokeWidth={5} />
  </g>
);

export const Phone: React.FC<{x: number; y: number; rot?: number}> = ({x, y, rot = 0}) => (
  <g transform={`translate(${x},${y}) rotate(${rot})`}>
    <rect x={-26} y={-78} width={52} height={96} rx={10} fill="#2b2b38" stroke={INK} strokeWidth={5} />
    <rect x={-20} y={-70} width={40} height={78} rx={5} fill="#7fd0ff" />
    <circle cx={0} cy={-30} r={9} fill="#ff4f6d" />
  </g>
);

const Pizza: React.FC<{x: number; y: number}> = ({x, y}) => (
  <g transform={`translate(${x},${y - 20}) rotate(-20)`}>
    <path d="M-50,-60 L50,-60 L0,60 Z" fill="#ffcf5a" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
    <path d="M-56,-66 L56,-66 L50,-50 L-50,-50 Z" fill="#d98a3a" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
    <circle cx={-14} cy={-30} r={10} fill="#d64541" />
    <circle cx={16} cy={-20} r={9} fill="#d64541" />
    <circle cx={2} cy={8} r={8} fill="#d64541" />
  </g>
);

export const Face: React.FC<{eyes: Eyes; mouth: Mouth; mouthOpen: number; look: V2; brows: [number, number]; sweat?: boolean; skin?: string}> = ({eyes, mouth, mouthOpen, look, brows, sweat, skin = SKIN}) => {
  const [lx, ly] = look;
  const eyeEls: React.ReactNode[] = [];
  for (const ex of [-1, 1]) {
    const cx = ex * 30 + lx * 4, cy = -6 + ly * 4;
    if (eyes === 'closed' || eyes === 'happy') {
      const up = eyes === 'happy' ? -14 : 8;
      eyeEls.push(<path key={ex} d={`M${cx - 18},${cy + 2} Q${cx},${cy + up} ${cx + 18},${cy + 2}`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />);
      continue;
    }
    const big = eyes === 'shocked' || eyes === 'scared';
    const rx = big ? 28 : 24, ry = big ? 36 : 30;
    const pr = big ? 8 : 11;
    eyeEls.push(
      <g key={ex}>
        <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="#fff" stroke={INK} strokeWidth={5} />
        <circle cx={cx + lx * 10} cy={cy + 3 + ly * 12} r={pr} fill={INK} />
        <circle cx={cx + lx * 10 - 3} cy={cy - 2 + ly * 12} r={3} fill="#fff" />
        {(eyes === 'annoyed' || eyes === 'deadpan') && (
          <>
            <path d={`M${cx - rx - 2},${cy - ry - 2} L${cx + rx + 2},${cy - ry - 2} L${cx + rx + 2},${cy + (eyes === 'deadpan' ? -2 : -6)} L${cx - rx - 2},${cy + (eyes === 'deadpan' ? -2 : -6)} Z`} fill={skin} />
            <line x1={cx - rx + 2} y1={cy + (eyes === 'deadpan' ? -2 : -6)} x2={cx + rx - 2} y2={cy + (eyes === 'deadpan' ? -2 : -6)} stroke={INK} strokeWidth={5} strokeLinecap="round" />
          </>
        )}
      </g>,
    );
  }
  const [raise, inner] = brows;
  const browY = eyes === 'shocked' || eyes === 'scared' ? -52 : -44;
  const browEls = [-1, 1].map((ex) => (
    <line key={ex} x1={ex * 12} y1={browY - raise + inner} x2={ex * 46} y2={browY - raise} stroke={INK} strokeWidth={7} strokeLinecap="round" />
  ));
  const my = 46;
  let m: React.ReactNode;
  const open = Math.max(mouthOpen, mouth === 'open' ? 0.7 : mouth === 'o' ? 0.35 : 0);
  if (open > 0.05) {
    const w = mouth === 'o' ? 12 + 6 * open : 20 + 8 * open, h = 6 + 34 * open;
    m = (
      <g>
        <ellipse cx={0} cy={my + h * 0.15} rx={w} ry={h / 2 + 2} fill="#5a1520" stroke={INK} strokeWidth={5} />
        <ellipse cx={0} cy={my + h * 0.35} rx={w * 0.55} ry={h * 0.18} fill="#e05a6a" />
      </g>
    );
  } else if (mouth === 'smile' || mouth === 'grin') {
    m = <path d={`M-22,${my - 4} Q0,${my + (mouth === 'grin' ? 26 : 16)} 22,${my - 4}`} stroke={INK} strokeWidth={6} fill={mouth === 'grin' ? '#fff' : 'none'} strokeLinecap="round" />;
  } else if (mouth === 'frown') {
    m = <path d={`M-18,${my + 8} Q0,${my - 8} 18,${my + 8}`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />;
  } else if (mouth === 'wobble') {
    m = <path d={`M-20,${my} l8,-5 l8,5 l8,-5 l8,5`} stroke={INK} strokeWidth={5} fill="none" strokeLinecap="round" strokeLinejoin="round" />;
  } else if (mouth === 'flat') {
    m = <line x1={-16} y1={my} x2={16} y2={my} stroke={INK} strokeWidth={6} strokeLinecap="round" />;
  } else {
    m = <path d={`M-12,${my} Q0,${my + 5} 12,${my}`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />;
  }
  return (
    <g>
      {eyeEls}
      {browEls}
      {m}
      {sweat && <path d="M92,-40 q14,22 0,30 q-14,-8 0,-30 Z" fill="#8fd8ff" stroke={INK} strokeWidth={4} />}
    </g>
  );
};

export const Leo: React.FC<LeoProps> = ({x, y, scale = 1, pose = {}, eyes = 'normal', mouth = 'closed', mouthOpen = 0, look = [0, 0], brows = [0, 0], holding = null, sweat, dusty, rotate = 0, flip, colors = {}}) => {
  const SKIN = colors.skin ?? SKIN0, SHIRT = colors.shirt ?? SHIRT0, PANTS = colors.pants ?? PANTS0, HAIR = colors.hair ?? HAIR0;
  const s = solve(pose);
  const R = RIG.HEAD_R;
  const torso: [number, number][] = [];
  const rot = (px: number, py: number): [number, number] => {
    const a = (s.lean * Math.PI) / 180;
    return [px * Math.cos(a) - py * Math.sin(a), s.pelvis[1] + px * Math.sin(a) + py * Math.cos(a)];
  };
  torso.push(rot(-RIG.SH - 6, -RIG.TORSO + 4), rot(RIG.SH + 6, -RIG.TORSO + 4), rot(50, -6), rot(-50, -6));
  const arm = (sh: V2, el: V2, hd: V2) => (
    <>
      <Limb d={pathOf(el, hd)} w={16} color={SKIN} />
      <Limb d={pathOf(sh, [sh[0] + (el[0] - sh[0]) * 0.75, sh[1] + (el[1] - sh[1]) * 0.75])} w={30} color={SHIRT} />
      <circle cx={hd[0]} cy={hd[1]} r={15} fill={SKIN} stroke={INK} strokeWidth={5} />
    </>
  );
  return (
    <g transform={`translate(${x},${y}) rotate(${rotate}) scale(${flip ? -scale : scale},${scale})`}>
      {/* legs */}
      <Limb d={pathOf(s.hipL, s.kneeL, s.footL)} w={30} color={PANTS} />
      <Limb d={pathOf(s.hipR, s.kneeR, s.footR)} w={30} color={PANTS} />
      {[s.footL, s.footR].map((f, i) => (
        <g key={i} transform={`translate(${f[0] + (i ? 8 : -8)},${f[1]})`}>
          <ellipse cx={0} cy={-4} rx={34} ry={17} fill="#fff" stroke={INK} strokeWidth={5} />
          <line x1={-28} y1={4} x2={28} y2={4} stroke="#c9ccd6" strokeWidth={5} />
        </g>
      ))}
      <rect x={-46} y={s.pelvis[1] - 14} width={92} height={36} rx={14} fill={PANTS} stroke={INK} strokeWidth={5} />
      {/* torso */}
      <polygon points={pts(...torso)} fill={SHIRT} stroke={INK} strokeWidth={6} strokeLinejoin="round" />
      <path d={pathOf(rot(-24, -RIG.TORSO + 4), rot(0, -RIG.TORSO + 34), rot(24, -RIG.TORSO + 4))} fill="none" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
      {[0, 1, 2].map((k) => {
        const b = rot(0, -RIG.TORSO + 60 + k * 36);
        return <circle key={k} cx={b[0]} cy={b[1]} r={5} fill="#fff" stroke={INK} strokeWidth={2} />;
      })}
      {dusty && (
        <>
          <ellipse cx={rot(-20, -100)[0]} cy={rot(-20, -100)[1]} rx={22} ry={14} fill="#9b9488" opacity={0.75} />
          <ellipse cx={rot(28, -40)[0]} cy={rot(28, -40)[1]} rx={16} ry={10} fill="#9b9488" opacity={0.75} />
        </>
      )}
      {/* arms */}
      {arm(s.shL, s.elL, s.hdL)}
      {holding === 'phone' && <Phone x={s.hdR[0]} y={s.hdR[1]} rot={-8} />}
      {(holding === 'hawaiian' || holding === 'black') && <HawaiianShirt x={s.hdR[0]} y={s.hdR[1]} kind={holding} />}
      {holding === 'pizza' && <Pizza x={s.hdR[0]} y={s.hdR[1]} />}
      {arm(s.shR, s.elR, s.hdR)}
      {/* neck + head */}
      <Limb d={pathOf(s.neckBase, [s.head[0], s.head[1] + R - 8])} w={18} color={SKIN} />
      <g transform={`translate(${s.head[0]},${s.head[1]}) rotate(${s.tilt})`}>
        <ellipse cx={-R + 2} cy={6} rx={16} ry={22} fill={SKIN} stroke={INK} strokeWidth={5} />
        <ellipse cx={R - 2} cy={6} rx={16} ry={22} fill={SKIN} stroke={INK} strokeWidth={5} />
        <circle r={R} fill={SKIN} stroke={INK} strokeWidth={7} />
        {dusty && <ellipse cx={-40} cy={30} rx={18} ry={11} fill="#9b9488" opacity={0.7} />}
        <path d={hairPath} fill={HAIR} stroke={INK} strokeWidth={6} strokeLinejoin="round" />
        <Face eyes={eyes} mouth={mouth} mouthOpen={mouthOpen} look={look} brows={brows} sweat={sweat} skin={SKIN} />
      </g>
    </g>
  );
};
