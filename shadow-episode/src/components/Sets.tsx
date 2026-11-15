import React from 'react';
import {INK} from './Leo';

/** colour mix for the day -> night palette shift */
export const mix = (a: string, b: string, t: number) => {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return '#' + pa.map((v, i) => Math.round(v + (pb[i] - v) * t).toString(16).padStart(2, '0')).join('');
};

export const W = 1080, H = 1920;
export const WALL_BASE = 1360;

const Planks: React.FC<{y: number; c1: string; c2: string}> = ({y, c1, c2}) => (
  <g>
    <rect x={0} y={y} width={W} height={H - y} fill={c1} />
    {Array.from({length: 9}).map((_, i) => (
      <line key={i} x1={0} y1={y + 40 + i * 64} x2={W} y2={y + 40 + i * 64} stroke={c2} strokeWidth={5} />
    ))}
    {Array.from({length: 30}).map((_, i) => {
      const row = i % 9, x = ((i * 263) % W);
      return <line key={'v' + i} x1={x} y1={y + 40 + row * 64} x2={x} y2={y + 104 + row * 64} stroke={c2} strokeWidth={5} />;
    })}
    <rect x={0} y={y} width={W} height={18} fill={c2} opacity={0.6} />
  </g>
);

/** BEDROOM — night: 0 (warm morning) .. 1 (dark blue). lamp: 0..1 brightness. */
export const Bedroom: React.FC<{night?: number; lamp?: number; mirror?: boolean; bed?: boolean}> = ({night = 0, lamp = 0, mirror, bed = true}) => {
  const k = night;
  const wall = mix('#f7d9a8', '#1f2c52', k), wall2 = mix('#efc98f', '#18234a', k);
  const floor = mix('#c98e57', '#283055', k), floor2 = mix('#b07a46', '#1f2647', k);
  const sky = mix('#bfe8ff', '#0e1838', k);
  return (
    <g>
      <rect x={0} y={0} width={W} height={WALL_BASE} fill={wall} />
      {Array.from({length: 12}).map((_, i) => <rect key={i} x={i * 96 + 40} y={0} width={16} height={WALL_BASE} fill={wall2} opacity={0.35} />)}
      {/* window */}
      <g transform="translate(90,300)">
        <rect x={-14} y={-14} width={368} height={488} rx={10} fill={mix('#fff8ec', '#2d3b66', k)} stroke={INK} strokeWidth={7} />
        <rect x={0} y={0} width={340} height={460} fill={sky} stroke={INK} strokeWidth={5} />
        {k < 0.5 ? <circle cx={250} cy={110} r={58} fill="#ffd54a" stroke={INK} strokeWidth={5} opacity={1 - k * 2} /> : <circle cx={250} cy={110} r={46} fill="#e9eefc" stroke={INK} strokeWidth={5} opacity={(k - 0.5) * 2} />}
        <rect x={0} y={330} width={340} height={130} fill={mix('#9ad17f', '#16244a', k)} />
        <line x1={170} y1={0} x2={170} y2={460} stroke={INK} strokeWidth={8} />
        <line x1={0} y1={230} x2={340} y2={230} stroke={INK} strokeWidth={8} />
        <path d="M-40,-30 L60,-30 L40,500 L-60,500 Z" fill={mix('#e86a5a', '#4a2a55', k)} stroke={INK} strokeWidth={6} />
        <path d="M300,-30 L400,-30 L420,500 L320,500 Z" fill={mix('#e86a5a', '#4a2a55', k)} stroke={INK} strokeWidth={6} />
      </g>
      {k < 0.6 && <path d="M260,300 L560,1360 L900,1360 L430,300 Z" fill="#fff6c8" opacity={0.22 * (1 - k / 0.6)} />}
      {/* picture frame */}
      <rect x={640} y={420} width={200} height={150} rx={6} fill={mix('#ffffff', '#3a4570', k)} stroke={INK} strokeWidth={7} />
      <path d="M660,550 L720,480 L770,530 L800,500 L825,550 Z" fill={mix('#6cc08a', '#2a4a5a', k)} />
      {mirror && (
        <g>
          <rect x={790} y={560} width={210} height={760} rx={100} fill={mix('#cbe8f5', '#33406a', k)} stroke={INK} strokeWidth={8} />
          <path d="M840,700 L900,640 M850,800 L960,690" stroke="#ffffff" strokeWidth={14} strokeLinecap="round" opacity={0.7} />
        </g>
      )}
      <Planks y={WALL_BASE} c1={floor} c2={floor2} />
      <rect x={0} y={WALL_BASE - 26} width={W} height={26} fill={mix('#fff4e0', '#2a3560', k)} stroke={INK} strokeWidth={5} />
    </g>
  );
};

/** furniture drawn in FRONT of wall shadows */
export const BedFront: React.FC<{night?: number; lamp?: number}> = ({night = 0, lamp = 0}) => {
  const k = night;
  return (
    <g>
      {/* nightstand + lamp */}
      <g transform="translate(470,1240)">
        <rect x={0} y={0} width={150} height={190} rx={10} fill={mix('#c8834e', '#3a3050', k)} stroke={INK} strokeWidth={6} />
        <line x1={10} y1={90} x2={140} y2={90} stroke={INK} strokeWidth={5} />
        <circle cx={75} cy={50} r={8} fill={INK} />
        <circle cx={75} cy={140} r={8} fill={INK} />
        <rect x={68} y={-90} width={14} height={90} fill={INK} />
        <path d="M20,-90 L130,-90 L105,-190 L45,-190 Z" fill={lamp > 0.05 ? mix('#fff0b0', '#ffe27a', lamp) : mix('#f5e6c8', '#4a4a6a', k)} stroke={INK} strokeWidth={6} />
        <defs>
          <radialGradient id="lampglow">
            <stop offset="0%" stopColor="#ffe27a" stopOpacity={0.55} />
            <stop offset="100%" stopColor="#ffe27a" stopOpacity={0} />
          </radialGradient>
        </defs>
        {lamp > 0.05 && <circle cx={75} cy={-130} r={300} fill="url(#lampglow)" opacity={lamp} />}
      </g>
      {/* bed */}
      <g transform="translate(-20,1080)">
        <rect x={0} y={0} width={60} height={420} rx={12} fill={mix('#9a5a34', '#2c2440', k)} stroke={INK} strokeWidth={6} />
        <rect x={20} y={170} width={460} height={200} rx={24} fill={mix('#ffffff', '#b8c4e6', k)} stroke={INK} strokeWidth={6} />
        <rect x={40} y={130} width={170} height={80} rx={34} fill={mix('#fffaf0', '#c9d3f0', k)} stroke={INK} strokeWidth={6} />
        <path d="M200,175 L480,175 L480,370 L200,370 Q170,270 200,175 Z" fill={mix('#5aa0e0', '#3a4a8a', k)} stroke={INK} strokeWidth={6} />
        <rect x={20} y={360} width={470} height={60} rx={10} fill={mix('#9a5a34', '#2c2440', k)} stroke={INK} strokeWidth={6} />
      </g>
    </g>
  );
};

/** LIVING ROOM with door (right), ceiling fan anchor, window */
export const LivingRoom: React.FC<{doorOpen?: number}> = ({doorOpen = 0}) => (
  <g>
    <rect x={0} y={0} width={W} height={WALL_BASE} fill="#bfe3d6" />
    {Array.from({length: 7}).map((_, i) => <rect key={i} x={0} y={120 + i * 180} width={W} height={10} fill="#aed6c8" />)}
    <rect x={0} y={0} width={W} height={150} fill="#f4f1e8" stroke={INK} strokeWidth={6} />
    <g transform="translate(70,330)">
      <rect x={-12} y={-12} width={284} height={384} rx={8} fill="#fffaf0" stroke={INK} strokeWidth={7} />
      <rect x={0} y={0} width={260} height={360} fill="#bfe8ff" stroke={INK} strokeWidth={5} />
      <rect x={0} y={240} width={260} height={120} fill="#9ad17f" />
      <line x1={130} y1={0} x2={130} y2={360} stroke={INK} strokeWidth={7} />
    </g>
    <rect x={430} y={380} width={180} height={140} rx={6} fill="#fff" stroke={INK} strokeWidth={7} />
    <circle cx={520} cy={450} r={40} fill="#ffb347" />
    {/* door frame + opening */}
    <g transform="translate(800,700)">
      <rect x={-18} y={-18} width={276} height={WALL_BASE - 700 + 18} fill="#fffaf0" stroke={INK} strokeWidth={7} />
      <rect x={0} y={0} width={240} height={WALL_BASE - 700} fill="#ffe9b0" />
      <rect x={0} y={420} width={240} height={WALL_BASE - 700 - 420} fill="#d8c7a0" />
      <polygon points={`0,0 ${240 - 200 * doorOpen},${20 * doorOpen} ${240 - 200 * doorOpen},${WALL_BASE - 700 - 20 * doorOpen} 0,${WALL_BASE - 700}`} fill="#b9773f" stroke={INK} strokeWidth={6} />
      <circle cx={210 - 180 * doorOpen} cy={360} r={11} fill="#ffd54a" stroke={INK} strokeWidth={4} />
    </g>
    <Planks y={WALL_BASE} c1="#d9a46c" c2="#c08a52" />
    <rect x={0} y={WALL_BASE - 24} width={W} height={24} fill="#fffaf0" stroke={INK} strokeWidth={5} />
    {/* plant */}
    <g transform="translate(110,1290)">
      <path d="M-50,0 L50,0 L38,110 L-38,110 Z" fill="#e2725b" stroke={INK} strokeWidth={6} />
      {[-60, -30, 0, 30, 60].map((a, i) => <ellipse key={i} cx={Math.sin((a * Math.PI) / 180) * 60} cy={-60 - Math.cos((a * Math.PI) / 180) * 30} rx={22} ry={60} transform={`rotate(${a} ${Math.sin((a * Math.PI) / 180) * 60} ${-60 - Math.cos((a * Math.PI) / 180) * 30})`} fill="#3fa65a" stroke={INK} strokeWidth={5} />)}
    </g>
  </g>
);

export const Chair: React.FC<{x: number; y: number; broken?: number}> = ({x, y, broken = 0}) => (
  <g transform={`translate(${x},${y})`}>
    <rect x={-90} y={-330 + broken * 120} width={180} height={190 - broken * 120} rx={20} fill="#e2a03f" stroke={INK} strokeWidth={6} transform={`rotate(${broken * -20})`} />
    <rect x={-100} y={-150} width={200} height={44} rx={14} fill="#f0b553" stroke={INK} strokeWidth={6} />
    <line x1={-80} y1={-106} x2={-90 - broken * 30} y2={0} stroke={INK} strokeWidth={12} strokeLinecap="round" />
    <line x1={80} y1={-106} x2={90 + broken * 40} y2={0} stroke={INK} strokeWidth={12} strokeLinecap="round" />
  </g>
);

export const Fan: React.FC<{x: number; y: number; spin: number; wobble: number; rod?: number}> = ({x, y, spin, wobble, rod = 150}) => (
  <g transform={`translate(${x},${y}) rotate(${wobble})`}>
    <line x1={0} y1={-rod} x2={0} y2={0} stroke={INK} strokeWidth={14} />
    {[0, 120, 240].map((a) => {
      const sx = Math.cos(((a + spin) * Math.PI) / 180);
      return <ellipse key={a} cx={sx * 130} cy={8} rx={Math.abs(sx) * 130 + 12} ry={18} fill="#f4f1e8" stroke={INK} strokeWidth={6} />;
    })}
    <ellipse cx={0} cy={10} rx={46} ry={30} fill="#9aa3ad" stroke={INK} strokeWidth={6} />
  </g>
);

/** KITCHEN at midnight, lit by the open fridge */
export const Kitchen: React.FC<{fridge?: number}> = ({fridge = 1}) => (
  <g>
    <rect x={0} y={0} width={W} height={WALL_BASE} fill="#1b2340" />
    <path d={`M420,700 L1080,420 L1080,1500 L420,1400 Z`} fill="#fff3c4" opacity={0.42 * fridge} />
    <rect x={0} y={WALL_BASE} width={W} height={H - WALL_BASE} fill="#232b4a" />
    {Array.from({length: 8}).map((_, i) => <line key={i} x1={0} y1={WALL_BASE + 30 + i * 70} x2={W} y2={WALL_BASE + 30 + i * 70} stroke="#1a2038" strokeWidth={5} />)}
    <path d={`M420,1380 L1080,1500 L1080,1920 L400,1920 Z`} fill="#fff3c4" opacity={0.14 * fridge} />
    {/* counter on the right */}
    <rect x={640} y={1060} width={460} height={320} fill="#2c355a" stroke={INK} strokeWidth={6} />
    <rect x={620} y={1030} width={480} height={40} fill="#3a4470" stroke={INK} strokeWidth={6} />
    {/* wall clock 12:00 */}
    <g transform="translate(850,360)">
      <circle r={92} fill="#e9eefc" stroke={INK} strokeWidth={8} />
      {Array.from({length: 12}).map((_, i) => {
        const a = (i * Math.PI) / 6;
        return <line key={i} x1={Math.sin(a) * 70} y1={-Math.cos(a) * 70} x2={Math.sin(a) * 82} y2={-Math.cos(a) * 82} stroke={INK} strokeWidth={6} />;
      })}
      <line x1={0} y1={0} x2={0} y2={-52} stroke={INK} strokeWidth={10} strokeLinecap="round" />
      <line x1={0} y1={0} x2={0} y2={-74} stroke={INK} strokeWidth={6} strokeLinecap="round" />
      <circle r={8} fill={INK} />
    </g>
    {/* fridge (open) */}
    <g transform="translate(110,640)">
      <rect x={0} y={0} width={300} height={740} rx={22} fill="#dfe6f2" stroke={INK} strokeWidth={7} />
      <rect x={18} y={18} width={264} height={704} rx={12} fill="#fffbe6" />
      {[200, 360, 520].map((yy) => <line key={yy} x1={18} y1={yy} x2={282} y2={yy} stroke="#d8d2b8" strokeWidth={8} />)}
      <rect x={40} y={140} width={60} height={60} rx={8} fill="#7cc26e" stroke={INK} strokeWidth={4} />
      <rect x={140} y={110} width={40} height={90} rx={8} fill="#ff8a65" stroke={INK} strokeWidth={4} />
      <ellipse cx={200} cy={340} rx={60} ry={18} fill="#ffcf5a" stroke={INK} strokeWidth={4} />
      <rect x={60} y={430} width={170} height={90} rx={10} fill="#f4f1e8" stroke={INK} strokeWidth={4} />
      <polygon points="300,0 380,40 380,700 300,740" fill="#c9d2e3" stroke={INK} strokeWidth={6} />
    </g>
  </g>
);

/** CITY STREET: buildings, far kerb, road (y 1060-1400), near pavement in the foreground. variant 'road' adds a grassy ditch bottom-right */
export const ROAD_Y = 1385;
export const Street: React.FC<{variant?: 'stop' | 'road'; scroll?: number}> = ({variant = 'stop', scroll = 0}) => {
  const bld = [
    ['#f0a868', -40, 260], ['#7fb8d8', 160, 420], ['#e8d7a8', 340, 330], ['#a0c98a', 520, 480], ['#f2b8c6', 720, 360], ['#9fa8d8', 900, 450],
  ] as const;
  return (
    <g>
      <rect x={0} y={0} width={W} height={1060} fill="#a8dcf5" />
      <circle cx={880} cy={220} r={70} fill="#ffe066" stroke={INK} strokeWidth={6} />
      {[[160, 200], [560, 140]].map(([cx, cy], i) => (
        <g key={i} transform={`translate(${cx},${cy})`}>
          <ellipse cx={0} cy={0} rx={90} ry={40} fill="#fff" />
          <ellipse cx={60} cy={-20} rx={60} ry={40} fill="#fff" />
        </g>
      ))}
      {bld.map(([c, x, h], i) => (
        <g key={i} transform={`translate(${x},0)`}>
          <rect x={0} y={1000 - h - 200} width={190} height={h + 200} fill={c} stroke={INK} strokeWidth={6} />
          {Array.from({length: 4}).map((_, r) => [0, 1].map((cc) => <rect key={`${r}-${cc}`} x={30 + cc * 76} y={1000 - h - 160 + r * 100} width={50} height={60} fill="#e9f6ff" stroke={INK} strokeWidth={4} />))}
        </g>
      ))}
      <rect x={0} y={1000} width={W} height={60} fill="#d5d9e0" stroke={INK} strokeWidth={5} />
      <rect x={0} y={1060} width={W} height={340} fill="#4a4f5a" />
      {Array.from({length: 8}).map((_, i) => <rect key={i} x={i * 180 - (scroll % 180)} y={1222} width={100} height={14} fill="#f4f1e8" />)}
      <rect x={0} y={1400} width={W} height={34} fill="#9aa1ad" stroke={INK} strokeWidth={6} />
      <rect x={0} y={1434} width={W} height={H - 1434} fill="#d5d9e0" />
      {Array.from({length: 12}).map((_, i) => <line key={i} x1={i * 120} y1={1434} x2={i * 120 - 120} y2={H} stroke="#b8bdc8" strokeWidth={5} />)}
      {[1560, 1720, 1880].map((yy) => <line key={yy} x1={0} y1={yy} x2={W} y2={yy} stroke="#b8bdc8" strokeWidth={5} />)}
      {variant === 'road' && (
        <g>
          <path d="M520,1434 Q760,1480 1080,1470 L1080,1920 L380,1920 Q470,1640 520,1434 Z" fill="#6aa84f" stroke={INK} strokeWidth={6} />
          <path d="M600,1620 Q820,1680 1080,1660 L1080,1920 L520,1920 Q560,1760 600,1620 Z" fill="#4f7f37" />
          {[[620, 1500], [860, 1520], [980, 1500]].map(([gx, gy], i) => <path key={i} d={`M${gx},${gy} l10,-30 l10,30 l10,-24 l8,24`} stroke="#3f7a2f" strokeWidth={5} fill="none" />)}
        </g>
      )}
    </g>
  );
};

export const BusStopFront: React.FC = () => (
  <g>
    <g transform="translate(40,1150)">
      <rect x={0} y={0} width={340} height={26} fill="#3a4470" stroke={INK} strokeWidth={5} />
      <rect x={12} y={26} width={14} height={330} fill="#3a4470" />
      <rect x={314} y={26} width={14} height={330} fill="#3a4470" />
      <rect x={26} y={44} width={288} height={210} fill="#cfefff" opacity={0.5} stroke={INK} strokeWidth={4} />
      <rect x={40} y={270} width={260} height={28} rx={8} fill="#c8834e" stroke={INK} strokeWidth={5} />
    </g>
    <g transform="translate(980,1120)">
      <rect x={-8} y={0} width={16} height={420} fill="#5a6070" stroke={INK} strokeWidth={4} />
      <circle cx={0} cy={0} r={64} fill="#2f7de0" stroke={INK} strokeWidth={6} />
      <text x={0} y={-6} textAnchor="middle" fontFamily="Inter" fontWeight={900} fontSize={28} fill="#fff">BUS</text>
      <text x={0} y={26} textAnchor="middle" fontFamily="Inter" fontWeight={900} fontSize={24} fill="#fff">STOP</text>
    </g>
  </g>
);

export const Bus: React.FC<{x: number; y: number; rot?: number; doorOpen?: number; wobble?: number}> = ({x, y, rot = 0, doorOpen = 0, wobble = 0}) => (
  <g transform={`translate(${x},${y}) rotate(${rot + wobble})`}>
    <ellipse cx={0} cy={0} rx={470} ry={24} fill="#000" opacity={0.25} />
    <rect x={-460} y={-420} width={920} height={380} rx={40} fill="#e8473c" stroke={INK} strokeWidth={8} />
    <rect x={-460} y={-170} width={920} height={40} fill="#ffffff" stroke={INK} strokeWidth={5} />
    {[-400, -270, -140, 120, 250].map((wx, i) => (
      <g key={wx}>
        <rect x={wx} y={-380} width={110} height={150} rx={14} fill="#bfe8ff" stroke={INK} strokeWidth={5} />
        <circle cx={wx + 55} cy={-290} r={26} fill="#2a2a3a" opacity={0.55} />
        <rect x={wx + 25} y={-264} width={60} height={34} rx={10} fill="#2a2a3a" opacity={0.55} />
      </g>
    ))}
    {/* door */}
    <rect x={-10} y={-390} width={120} height={350} rx={10} fill="#2a2a3a" stroke={INK} strokeWidth={5} />
    <rect x={-10 + 60 * doorOpen} y={-390} width={60 - 60 * doorOpen} height={350} fill="#9fd8f0" stroke={INK} strokeWidth={4} />
    <rect x={50} y={-390} width={60 - 60 * doorOpen} height={350} fill="#9fd8f0" stroke={INK} strokeWidth={4} />
    <rect x={-440} y={-120} width={50} height={36} rx={8} fill="#fff6a0" stroke={INK} strokeWidth={4} />
    <rect x={300} y={-460} width={140} height={44} rx={8} fill="#2a2a3a" stroke={INK} strokeWidth={5} />
    <text x={370} y={-428} textAnchor="middle" fontFamily="Inter" fontWeight={900} fontSize={30} fill="#ffd54a">42</text>
    {[-300, 300].map((wx) => (
      <g key={wx}>
        <circle cx={wx} cy={-36} r={62} fill="#2a2a3a" stroke={INK} strokeWidth={6} />
        <circle cx={wx} cy={-36} r={26} fill="#c9ced6" stroke={INK} strokeWidth={4} />
      </g>
    ))}
  </g>
);

export const Dust: React.FC<{x: number; y: number; t: number; size?: number}> = ({x, y, t, size = 1}) => {
  if (t < 0 || t > 2.2) return null;
  const q = t / 2.2;
  return (
    <g opacity={1 - q}>
      {Array.from({length: 14}).map((_, i) => {
        const a = (i / 14) * Math.PI * 2;
        const r = (60 + 260 * q) * size;
        return <circle key={i} cx={x + Math.cos(a) * r} cy={y - Math.abs(Math.sin(a)) * r * 0.6} r={(70 - 30 * q) * size} fill="#c9b99a" stroke={INK} strokeWidth={4} />;
      })}
    </g>
  );
};

export const Hearts: React.FC<{x: number; y: number; t: number}> = ({x, y, t}) => (
  <g>
    {Array.from({length: 6}).map((_, i) => {
      const q = ((t * 0.6 + i / 6) % 1);
      if (t < i * 0.15) return null;
      const hx = x + Math.sin(i * 2.1 + t) * 90, hy = y - q * 280;
      return <path key={i} transform={`translate(${hx},${hy}) scale(${1.2 - q * 0.4})`} d="M0,18 C-40,-8 -24,-40 0,-20 C24,-40 40,-8 0,18 Z" fill="#ff5c8a" stroke={INK} strokeWidth={4} opacity={1 - q} />;
    })}
  </g>
);

export const Commuter: React.FC<{x: number; y: number; c: string; hair: string; w?: number}> = ({x, y, c, hair}) => (
  <g transform={`translate(${x},${y})`}>
    <line x1={-14} y1={-150} x2={-16} y2={0} stroke={INK} strokeWidth={22} strokeLinecap="round" />
    <line x1={14} y1={-150} x2={16} y2={0} stroke={INK} strokeWidth={22} strokeLinecap="round" />
    <rect x={-40} y={-300} width={80} height={160} rx={24} fill={c} stroke={INK} strokeWidth={6} />
    <circle cx={0} cy={-350} r={50} fill="#e9b88c" stroke={INK} strokeWidth={6} />
    <path d="M-50,-360 A50,50 0 0 1 50,-360 L50,-372 Q0,-430 -50,-372 Z" fill={hair} stroke={INK} strokeWidth={5} />
    <circle cx={-16} cy={-350} r={7} fill={INK} />
    <circle cx={16} cy={-350} r={7} fill={INK} />
  </g>
);
