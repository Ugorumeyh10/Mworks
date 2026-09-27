import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import AdSlot from '../components/AdSlot.jsx';
import { fetchBlogPosts } from '../api/blog.js';
import { getUser } from '../api/session.js';
import { AiBadge, BLOG_CATS, BlogCover } from './blogShared.jsx';
import './Blog.css';

export default function Blog() {
  const [posts, setPosts] = useState([]);
  const [cat, setCat] = useState('All');
  const [loading, setLoading] = useState(true);
  const isAdmin = Boolean(getUser()?.isAdmin);

  useEffect(() => {
    let live = true;
    setLoading(true);
    fetchBlogPosts(cat).then((rows) => {
      if (!live) return;
      setPosts(Array.isArray(rows) ? rows : []);
      setLoading(false);
    });
    return () => { live = false; };
  }, [cat]);

  const featured = posts[0];
  const rest = posts.slice(1);
  const cats = useMemo(() => {
    const seen = new Set(posts.map((p) => p.category).filter(Boolean));
    return BLOG_CATS.filter((c) => c === 'All' || seen.has(c) || c === cat);
  }, [posts, cat]);

  return (
    <div className="blog-page">
      <header className="blog-hero">
        <span className="blog-hero-stripe" aria-hidden="true" />
        <div className="blog-hero-copy">
          <p className="blog-kicker">The newsroom</p>
          <h1>Stories for builders</h1>
          <p className="sub">
            Playbooks, product notes, and the latest tech news. The news agent
            writes from public feeds and publishes as soon as a story is ready.
          </p>
        </div>
        {isAdmin && (
          <Link to="/blog/newsroom" className="mk-btn">Open newsroom</Link>
        )}
      </header>

      <div className="blog-layout">
        <div className="blog-main">
          <div className="blog-chips" role="tablist" aria-label="Blog categories">
            {cats.map((c) => (
              <button
                key={c}
                type="button"
                role="tab"
                aria-selected={cat === c}
                className={'chip' + (cat === c ? ' on' : '')}
                onClick={() => setCat(c)}
              >
                {c}
              </button>
            ))}
          </div>

          {loading ? (
            <p className="body-text">Loading the newsroom…</p>
          ) : posts.length === 0 ? (
            <div className="mk-empty">Nothing published in this category yet.</div>
          ) : (
            <>
              {featured && (
                <Link to={`/blog/${featured.id}`} className="blog-feature">
                  <span className="blog-feature-stripe" aria-hidden="true" />
                  <BlogCover post={featured} className="blog-cover-feature" />
                  <div>
                    <div className="blog-card-meta">
                      <span className="blog-cat">{featured.category}</span>
                      <span>{featured.readMinutes} min read</span>
                      {featured.publishedAt && <span>{featured.publishedAt}</span>}
                    </div>
                    <h2>{featured.title}</h2>
                    <p>{featured.excerpt}</p>
                    <div className="blog-card-foot">
                      <span>{featured.authorName || 'Mworks'}</span>
                      <AiBadge post={featured} />
                    </div>
                  </div>
                </Link>
              )}

              <AdSlot className="ad-slot-banner" format="horizontal" />

              <div className="blog-grid">
                {rest.map((p) => (
                  <Link to={`/blog/${p.id}`} className="blog-card" key={p.id}>
                    <BlogCover post={p} />
                    <div className="blog-card-meta">
                      <span className="blog-cat">{p.category}</span>
                      <span>{p.readMinutes} min</span>
                    </div>
                    <h3>{p.title}</h3>
                    <p>{p.excerpt}</p>
                    <div className="blog-card-foot">
                      <span>{p.publishedAt}</span>
                      <AiBadge post={p} />
                    </div>
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>

        <aside className="blog-aside">
          <div className="blog-aside-card">
            <span className="blog-aside-icon"><Icon name="bot" /></span>
            <h3>Meet the news agent</h3>
            <p>
              It reads public tech feeds, pulls in pictures or video when the
              source has them, and publishes the story straight away.
            </p>
          </div>
          <AdSlot className="ad-slot-rail" format="rectangle" />
          <p className="blog-ad-note">Ads help keep the newsroom free. We never sell your data.</p>
        </aside>
      </div>
    </div>
  );
}
