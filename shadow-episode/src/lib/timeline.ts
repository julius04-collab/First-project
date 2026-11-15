import data from '../timeline.json';

export type Segment = {id: number; scene: number; speaker: 'N' | 'L' | 'C'; text: string; start: number; end: number};
export const FPS = 30;
export const SEGS: Segment[] = data.segments as Segment[];
export const TOTAL_SEC = data.duration + 1.2;
export const seg = (id: number) => SEGS[id];

const firstOf = (scene: number) => SEGS.find((s) => s.scene === scene)!;
/** scene start (seconds) – a quarter second before its first narration line */
export const sceneStart = (scene: number) => (scene === 1 ? 0 : firstOf(scene).start - 0.25);
export const sceneEnd = (scene: number) => (scene === 12 ? TOTAL_SEC : sceneStart(scene + 1));
/** time of a narration segment relative to the start of its scene */
export const rel = (id: number, scene: number) => SEGS[id].start - sceneStart(scene);
export const relEnd = (id: number, scene: number) => SEGS[id].end - sceneStart(scene);
