import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, interpolate} from 'remotion';
import {FPS, TOTAL_SEC, sceneStart, sceneEnd, SEGS, rel} from './lib/timeline';
import {Captions} from './components/Captions';
import {Scene01} from './scenes/Scene01';
import {Scene02} from './scenes/Scene02';
import {Scene03} from './scenes/Scene03';
import {Scene04} from './scenes/Scene04';
import {Scene05} from './scenes/Scene05';
import {Scene06} from './scenes/Scene06';
import {Scene07} from './scenes/Scene07';
import {Scene08} from './scenes/Scene08';
import {Scene09} from './scenes/Scene09';
import {Scene10} from './scenes/Scene10';
import {Scene11} from './scenes/Scene11';
import {Scene12} from './scenes/Scene12';

const SCENES = [Scene01, Scene02, Scene03, Scene04, Scene05, Scene06, Scene07, Scene08, Scene09, Scene10, Scene11, Scene12];
const f = (sec: number) => Math.round(sec * FPS);
const abs = (scene: number, local: number) => sceneStart(scene) + local;

// sound-effect cue sheet (absolute seconds)
const T_TWIST = abs(11, rel(27, 11) + 1.1);
const SFX: {file: string; at: number; until?: number; vol?: number; loop?: boolean}[] = [
  {file: 'yawn', at: SEGS[2].start + 0.15, vol: 0.8},
  {file: 'crickets', at: SEGS[4].start, vol: 0.5},
  {file: 'applause', at: abs(3, rel(6, 3) + 0.5), vol: 0.6},
  {file: 'skid', at: abs(5, rel(11, 5) + 1.1), vol: 0.6},
  {file: 'thud', at: abs(5, rel(11, 5) + 2.2), vol: 0.9},
  {file: 'foot-tap', at: SEGS[13].start + 1.0, until: sceneEnd(6), loop: true, vol: 0.7},
  {file: 'facepalm-slap', at: SEGS[17].start + 0.1, vol: 0.9},
  {file: 'slide-whistle', at: SEGS[20].start + 0.1, vol: 0.55},
  {file: 'crash', at: abs(8, rel(21, 8) + 0.95), vol: 0.9},
  {file: 'wrong-buzzer', at: abs(9, 0.8), vol: 0.45},
  {file: 'correct-ding', at: abs(9, 2.0), vol: 0.6},
  {file: 'flicker', at: abs(10, 0.3), vol: 0.6},
  {file: 'drone', at: sceneStart(10), until: T_TWIST, loop: true, vol: 0.55},
  {file: 'boom', at: SEGS[27].start, vol: 0.9},
  {file: 'record-scratch', at: T_TWIST, vol: 0.7},
  {file: 'aww', at: T_TWIST + 1.85, vol: 0.5},
  {file: 'sneaky-tiptoe', at: abs(12, 0.2), vol: 0.6},
  {file: 'ahem', at: abs(12, rel(29, 12) + 1.9), vol: 0.8},
];

export const Episode: React.FC = () => {
  const total = f(TOTAL_SEC);
  const quietFrom = f(sceneStart(10)), quietTo = f(T_TWIST);
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {SCENES.map((S, i) => {
        const from = f(sceneStart(i + 1)), to = f(sceneEnd(i + 1));
        return (
          <Sequence key={i} from={from} durationInFrames={to - from} name={`Scene ${i + 1}`}>
            <S />
          </Sequence>
        );
      })}
      <Captions />
      <Audio src={staticFile('narration.mp3')} />
      <Audio src={staticFile('music.mp3')} volume={(fr) => {
        const base = 0.12;
        if (fr >= quietFrom - 6 && fr < quietTo) return interpolate(fr, [quietFrom - 6, quietFrom], [base, 0], {extrapolateRight: 'clamp'});
        if (fr >= quietTo && fr < quietTo + 20) return interpolate(fr, [quietTo, quietTo + 20], [0, base]);
        return interpolate(fr, [total - 30, total], [base, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
      }} />
      {SFX.map((s, i) => (
        <Sequence key={i} from={f(s.at)} durationInFrames={s.until ? f(s.until - s.at) : undefined} name={`sfx ${s.file}`}>
          <Audio src={staticFile(`sfx/${s.file}.mp3`)} volume={s.vol ?? 0.8} loop={s.loop} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
export const EPISODE_FRAMES = Math.round(TOTAL_SEC * FPS);
