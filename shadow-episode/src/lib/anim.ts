export const clamp = (x: number, a = 0, b = 1) => Math.max(a, Math.min(b, x));
/** smoothstep from a to b */
export const ss = (a: number, b: number, x: number) => {
  const t = b === a ? (x >= a ? 1 : 0) : clamp((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export type V2 = [number, number];
export const lerp2 = (p: V2, q: V2, t: number): V2 => [lerp(p[0], q[0], t), lerp(p[1], q[1], t)];
/** overshoot pop 0..1 */
export const popIn = (t: number, dur = 0.35) => {
  const x = clamp(t / dur) - 1;
  const k = 1.9;
  return t <= 0 ? 0 : 1 + x * x * ((k + 1) * x + k);
};
/** two-bone IK; picks the elbow solution that points outward */
export const ik = (sx: number, sy: number, tx: number, ty: number, outward: number, l1: number, l2: number) => {
  const dx = tx - sx, dy = ty - sy;
  const d = clamp(Math.hypot(dx, dy), 10, l1 + l2 - 1);
  const a = Math.atan2(dy, dx);
  const al = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1));
  const c1: V2 = [sx + l1 * Math.cos(a + al), sy + l1 * Math.sin(a + al)];
  const c2: V2 = [sx + l1 * Math.cos(a - al), sy + l1 * Math.sin(a - al)];
  const score = (c: V2) => (c[0] - sx) * outward + (c[1] - sy) * 0.3;
  const el = score(c1) > score(c2) ? c1 : c2;
  const hd: V2 = [sx + d * Math.cos(a), sy + d * Math.sin(a)];
  return {el, hd};
};
/** deterministic jitter */
export const jitter = (t: number, seed: number, amp: number) =>
  amp * (Math.sin(t * 37.1 + seed * 12.9) * 0.6 + Math.sin(t * 59.3 + seed * 4.1) * 0.4);
