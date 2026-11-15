import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Leo} from './components/Leo';
import {Shadow} from './components/Shadow';
import {DOWN_L, DOWN_R, Pose} from './components/Figure';

const shadowPoses: [string, Pose, object?][] = [
  ['yawn', {handL: [-70, -165], handR: [70, -165]}, {yawn: 1}],
  ['lean on wall', {lean: -9, handL: [86, 70], handR: [-86, 62], tilt: -10}],
  ['bow', {lean: 34, tilt: 22, hipY: -180, handL: [96, 40], handR: [140, -70]}],
  ['point', {handR: [165, -40]}],
  ['arms folded / tap', {handL: [86, 70], handR: [-86, 62], tapR: 16}],
  ['facepalm', {handL: [52, -150], tilt: 14, lean: 6}],
  ['thumbs up', {handR: [50, -120]}, {thumbR: 'up'}],
  ['thumbs down', {handR: [60, -40]}, {thumbR: 'down'}],
  ['girlfriend wave', {handR: [70, -150], tilt: 10}, {ponytail: true}],
];
const leoFaces: [string, any][] = [
  ['normal', {eyes: 'normal', mouth: 'smile'}], ['shocked', {eyes: 'shocked', mouth: 'open', mouthOpen: 0.8, brows: [14, -4]}],
  ['annoyed', {eyes: 'annoyed', mouth: 'frown', brows: [0, 12]}], ['scared', {eyes: 'scared', mouth: 'wobble', brows: [12, -10], sweat: true}],
];

export const PoseSheet: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: '#f7d9a8', fontFamily: 'Inter', fontWeight: 900}}>
    <svg width={1080} height={1920}>
      {leoFaces.map(([n, p], i) => (
        <g key={n}>
          <Leo x={140 + i * 270} y={720} scale={0.62} pose={{handL: DOWN_L, handR: DOWN_R}} {...p} />
          <text x={140 + i * 270} y={770} textAnchor="middle" fontSize={30} fill="#1b1b2a">{n}</text>
        </g>
      ))}
      {shadowPoses.map(([n, p, extra], i) => (
        <g key={n}>
          <Shadow id={`ps${i}`} x={180 + (i % 3) * 360} y={1150 + Math.floor(i / 3) * 360} scale={0.48} pose={p} {...(extra as object)} />
          <text x={180 + (i % 3) * 360} y={1190 + Math.floor(i / 3) * 360} textAnchor="middle" fontSize={28} fill="#1b1b2a">{n}</text>
        </g>
      ))}
    </svg>
    <div style={{position: 'absolute', top: 60, width: '100%', textAlign: 'center', fontSize: 54, color: '#1b1b2a'}}>LEO + SHADOW POSES</div>
  </AbsoluteFill>
);
