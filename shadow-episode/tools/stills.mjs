// Render the pose sheet + a set of preview stills in one bundle pass:  node tools/stills.mjs 1.5 7 ...
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'path';
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const times = process.argv.slice(2).map(Number);
const pose = await selectComposition({serveUrl, id: 'PoseSheet', browserExecutable});
await renderStill({composition: pose, serveUrl, output: 'out/posesheet.png', browserExecutable});
const comp = await selectComposition({serveUrl, id: 'ShadowEpisode', browserExecutable});
for (const t of times) {
  await renderStill({composition: comp, serveUrl, output: `out/st_${t}.png`, frame: Math.round(t * 30), browserExecutable, scale: 0.4});
}
console.log('done');
