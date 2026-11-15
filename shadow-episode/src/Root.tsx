import React from 'react';
import {Composition} from 'remotion';
import {Episode, EPISODE_FRAMES} from './Episode';
import {PoseSheet} from './PoseSheet';

export const Root: React.FC = () => (
  <>
    <Composition id="ShadowEpisode" component={Episode} durationInFrames={EPISODE_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="PoseSheet" component={PoseSheet} durationInFrames={1} fps={30} width={1080} height={1920} />
  </>
);
