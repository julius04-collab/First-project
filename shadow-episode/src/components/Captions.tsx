import React from 'react';
import {useCurrentFrame} from 'remotion';
import {FPS, SEGS} from '../lib/timeline';
import {popIn} from '../lib/anim';

type Word = {w: string; t0: number; t1: number; speaker: string};
type Chunk = {words: Word[]; t0: number; t1: number};

/** split each narration segment into short word chunks with proportional word timings */
const CHUNKS: Chunk[] = (() => {
  const out: Chunk[] = [];
  for (const s of SEGS) {
    const words = s.text.replace(/"/g, '').split(/\s+/).filter(Boolean);
    const weights = words.map((w) => w.length + 1 + (/[,.!?…:]$/.test(w) ? 4 : 0));
    const total = weights.reduce((a, b) => a + b, 0);
    let acc = 0;
    const timed: Word[] = words.map((w, i) => {
      const t0 = s.start + ((s.end - s.start) * acc) / total;
      acc += weights[i];
      return {w, t0, t1: s.start + ((s.end - s.start) * acc) / total, speaker: s.speaker};
    });
    let cur: Word[] = [];
    timed.forEach((wd, i) => {
      cur.push(wd);
      const brk = /[,.!?…:]$/.test(wd.w) || cur.length >= 4 || i === timed.length - 1;
      if (brk) {
        out.push({words: cur, t0: cur[0].t0, t1: cur[cur.length - 1].t1});
        cur = [];
      }
    });
  }
  return out;
})();

const COLOR: Record<string, string> = {N: '#ffffff', L: '#ffd23f', C: '#9fe6ff'};

export const Captions: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const ch = CHUNKS.find((c) => c.t0 <= t && t < c.t1 + 0.12);
  if (!ch) return null;
  const shown = ch.words.filter((w) => w.t0 <= t + 0.02);
  const text = shown.map((w) => w.w.toUpperCase());
  const size = 78;
  return (
    <div style={{position: 'absolute', left: 40, right: 40, top: 1500, display: 'flex', flexWrap: 'wrap', justifyContent: 'center'}}>
      {shown.map((w, i) => {
        const k = Math.min(1.06, popIn(t - w.t0, 0.18));
        return (
          <span key={i} style={{
            fontFamily: 'Inter', fontWeight: 900, fontSize: size, lineHeight: 1.15,
            color: COLOR[w.speaker], WebkitTextStroke: '14px #000', paintOrder: 'stroke fill',
            transform: `scale(${k})`, display: 'inline-block', margin: '0 16px', textShadow: '0 6px 0 rgba(0,0,0,0.35)',
          }}>{text[i]}</span>
        );
      })}
    </div>
  );
};

export const TitleCard: React.FC<{text: string; t: number; dur: number; y?: number; color?: string; bg?: string; size?: number}> = ({text, t, dur, y = 210, color = '#1b1b2a', bg = '#ffd23f', size = 64}) => {
  if (t < 0 || t > dur) return null;
  const k = popIn(t, 0.4);
  const fade = Math.min(1, (dur - t) / 0.25);
  return (
    <div style={{position: 'absolute', left: 60, right: 60, top: y, display: 'flex', justifyContent: 'center', opacity: fade}}>
      <div style={{
        transform: `scale(${k}) rotate(-2deg)`, background: bg, color, fontFamily: 'Inter', fontWeight: 900, fontSize: size,
        lineHeight: 1.1, textAlign: 'center', padding: '22px 36px', borderRadius: 28, border: '7px solid #1b1b2a', boxShadow: '0 12px 0 rgba(0,0,0,0.3)',
      }}>{text}</div>
    </div>
  );
};

export const EmojiPop: React.FC<{emoji: string; x: number; y: number; t: number; size?: number}> = ({emoji, x, y, t, size = 120}) => {
  if (t < 0) return null;
  const k = popIn(t, 0.35);
  return <div style={{position: 'absolute', left: x - size / 2, top: y - size / 2, fontSize: size, transform: `scale(${k})`, lineHeight: 1}}>{emoji}</div>;
};
