import {ik, lerp, V2} from '../lib/anim';

/** Shared rig used by Leo AND the shadows so silhouettes match exactly. Local units: feet at (0,0), up is negative. */
export const RIG = {HIP: -205, TORSO: 175, NECK: 16, HEAD_R: 86, SH: 46, UPPER: 92, FORE: 88};

export type Legs = 'stand' | 'walk' | 'sit' | 'dance' | 'tiptoe';
export type Pose = {
  hipY?: number;        // hip height (negative)
  lean?: number;        // torso lean, degrees (+ = toward viewer right)
  handL?: V2;           // viewer-left hand, relative to its shoulder
  handR?: V2;           // viewer-right hand, relative to its shoulder
  legs?: Legs;
  phase?: number;       // walk / dance phase (radians)
  stride?: number;      // 0..1.4
  bend?: number;        // knee bend for dance (0..1)
  tapR?: number;        // right toe lift (px)
  tilt?: number;        // head tilt degrees
  bob?: number;         // body vertical offset (+ = up)
};

export const DOWN_L: V2 = [-12, 172];
export const DOWN_R: V2 = [12, 172];

export type Solved = {
  hipL: V2; hipR: V2; kneeL: V2; kneeR: V2; footL: V2; footR: V2;
  pelvis: V2; neckBase: V2; head: V2; tilt: number; lean: number;
  shL: V2; shR: V2; elL: V2; elR: V2; hdL: V2; hdR: V2;
};

export const solve = (p: Pose): Solved => {
  const hipY = (p.hipY ?? RIG.HIP) - (p.bob ?? 0);
  const lean = ((p.lean ?? 0) * Math.PI) / 180;
  const rot = (x: number, y: number): V2 => [x * Math.cos(lean) - y * Math.sin(lean), hipY + x * Math.sin(lean) + y * Math.cos(lean)];
  const legs = p.legs ?? 'stand';
  const st = p.stride ?? 0, ph = p.phase ?? 0;
  const leg = (side: number, i: number): [V2, V2, V2] => {
    const hip: V2 = [side * 18, hipY + 4];
    if (legs === 'sit') return [hip, [side * 40, hipY + 30], [side * 44, 0]];
    if (legs === 'dance') {
      const b = p.bend ?? 0;
      return [hip, [side * (26 + 26 * b), lerp(hipY / 2, hipY / 2 + 10, b)], [side * 32, 0]];
    }
    const sw = Math.sin(ph + i * Math.PI);
    const lift = Math.max(0, Math.cos(ph + i * Math.PI)) * (legs === 'tiptoe' ? 26 : 18) * st;
    let foot: V2 = [side * 26 + 44 * st * sw, -lift];
    if (side > 0 && p.tapR) foot = [foot[0] + 6, foot[1] - p.tapR];
    const knee: V2 = [side * 22 + 30 * st * sw, hipY / 2 - lift * 0.6];
    return [hip, knee, foot];
  };
  const [hipL, kneeL, footL] = leg(-1, 0);
  const [hipR, kneeR, footR] = leg(1, 1);
  const shL = rot(-RIG.SH, -RIG.TORSO + 8), shR = rot(RIG.SH, -RIG.TORSO + 8);
  const aL = p.handL ?? DOWN_L, aR = p.handR ?? DOWN_R;
  const L = ik(shL[0], shL[1], shL[0] + aL[0], shL[1] + aL[1], -1, RIG.UPPER, RIG.FORE);
  const R = ik(shR[0], shR[1], shR[0] + aR[0], shR[1] + aR[1], 1, RIG.UPPER, RIG.FORE);
  return {
    hipL, hipR, kneeL, kneeR, footL, footR,
    pelvis: [0, hipY], neckBase: rot(0, -RIG.TORSO), head: rot(0, -RIG.TORSO - RIG.NECK - RIG.HEAD_R + 6),
    tilt: (p.tilt ?? 0) + (p.lean ?? 0) * 0.4, lean: p.lean ?? 0,
    shL, shR, elL: L.el, elR: R.el, hdL: L.hd, hdR: R.hd,
  };
};

export const pts = (...ps: V2[]) => ps.map((q) => `${q[0].toFixed(1)},${q[1].toFixed(1)}`).join(' ');
export const pathOf = (...ps: V2[]) => 'M' + ps.map((q) => `${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(' L');
