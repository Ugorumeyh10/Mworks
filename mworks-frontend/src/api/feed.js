import { api, apiEnabled } from './client.js';
import { posts as fallbackPosts } from '../data/sampleData.js';

const TAB = {
  'For You': 'for_you',
  Following: 'following',
  Jobs: 'jobs',
  Training: 'training',
};

export async function fetchFeed(label) {
  if (!apiEnabled()) return fallbackPosts;
  const tab = TAB[label] || 'for_you';
  try {
    return await api(`/v1/feed?tab=${encodeURIComponent(tab)}`);
  } catch {
    return [];
  }
}

export async function recordFeedEvent(postKey, kind = 'click') {
  if (!apiEnabled() || !postKey) return;
  try {
    await api('/v1/feed/events', { method: 'POST', body: { post_key: postKey, kind } });
  } catch {
    /* click telemetry is best-effort */
  }
}
