import { useEffect, useState } from 'react';
import PostCard from '../components/PostCard.jsx';
import { fetchFeed, recordFeedEvent } from '../api/feed.js';
import './DiscoverFeed.css';

const TABS = ['For You', 'Jobs', 'Training'];

export default function DiscoverFeed() {
  const [tab, setTab] = useState('For You');
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let live = true;
    setLoading(true);
    fetchFeed(tab).then((rows) => {
      if (!live) return;
      setPosts(Array.isArray(rows) ? rows : []);
      setLoading(false);
    });
    return () => {
      live = false;
    };
  }, [tab]);

  return (
    <div className="feed-page">
      <div className="feed-tabs">
        {TABS.map((t) => (
          <button
            key={t}
            className={'feed-tab' + (tab === t ? ' on' : '')}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      <p className="feed-note">
        {tab === 'For You'
          ? 'Ranked by likely click, purchase, and seller trust. Unverified posts are pushed down.'
          : tab === 'Jobs'
            ? 'Jobs are a separate inventory. They never mix into For You.'
            : 'Training showcases sit in their own inventory.'}
      </p>

      <div className="feed-list">
        {loading ? (
          <p className="body-text">Loading feed…</p>
        ) : posts.length === 0 ? (
          <div className="mk-empty">Nothing in this inventory yet.</div>
        ) : (
          posts.map((p) => (
            <PostCard
              key={p.id}
              post={p}
              onOpen={() => recordFeedEvent(p.id, 'click')}
            />
          ))
        )}
      </div>
    </div>
  );
}
