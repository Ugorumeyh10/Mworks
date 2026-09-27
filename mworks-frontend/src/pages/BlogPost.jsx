import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import AdSlot from '../components/AdSlot.jsx';
import { fetchBlogPost, fetchBlogPosts } from '../api/blog.js';
import { AiBadge, BlogBody, BlogCover, BlogMedia } from './blogShared.jsx';
import './Blog.css';

export default function BlogPost() {
  const { slug } = useParams();
  const [post, setPost] = useState(null);
  const [related, setRelated] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    let live = true;
    setPost(null);
    setError('');
    fetchBlogPost(slug)
      .then((row) => {
        if (live) setPost(row);
      })
      .catch((err) => {
        if (live) setError(err.status === 404 ? 'That post is not published.' : (err.message || 'Could not load this post.'));
      });
    fetchBlogPosts().then((rows) => {
      if (!live) return;
      setRelated((rows || []).filter((r) => r.id !== slug).slice(0, 3));
    });
    return () => { live = false; };
  }, [slug]);

  if (error) {
    return (
      <div className="blog-page mk-narrow">
        <Link to="/blog" className="mk-back"><Icon name="arrow-left" className="sm" /> Newsroom</Link>
        <div className="mk-empty">{error}</div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="blog-page mk-narrow">
        <p className="body-text">Loading…</p>
      </div>
    );
  }

  return (
    <article className="blog-page blog-article">
      <Link to="/blog" className="mk-back"><Icon name="arrow-left" className="sm" /> Newsroom</Link>
      <div className="blog-card-meta">
        <span className="blog-cat">{post.category}</span>
        <span>{post.readMinutes} min read</span>
        {post.publishedAt && <span>{post.publishedAt}</span>}
        {post.status === 'draft' && <span className="mk-pill warn">Draft</span>}
      </div>
      <h1>{post.title}</h1>
      <p className="blog-lede">{post.excerpt}</p>
      <div className="blog-byline">
        <span>{post.authorName || 'Mworks'}</span>
        <AiBadge post={post} />
      </div>

      {post.aiAssisted && (
        <div className="blog-disclose">
          <span className="blog-disclose-stripe" aria-hidden="true" />
          <p>
            A newsroom agent drafted this from a public headline.
            {post.sourceName ? ` Original reporting: ${post.sourceName}.` : ''}
          </p>
        </div>
      )}

      <BlogMedia items={post.media || []} />

      <BlogBody text={post.body} midSlot={<AdSlot className="ad-slot-inarticle" format="fluid" />} />

      {post.sourceUrl && (
        <p className="blog-source">
          Read the original at{' '}
          <a href={post.sourceUrl} target="_blank" rel="noopener noreferrer">
            {post.sourceName || 'the source'} <Icon name="external" className="sm" />
          </a>
        </p>
      )}

      <AdSlot className="ad-slot-banner" format="horizontal" />
      <p className="blog-ad-note">Ads help keep the newsroom free.</p>

      {related.length > 0 && (
        <section className="blog-more">
          <h2>Keep reading</h2>
          <div className="blog-grid">
            {related.map((p) => (
              <Link to={`/blog/${p.id}`} className="blog-card" key={p.id}>
                <BlogCover post={p} />
                <div className="blog-card-meta">
                  <span className="blog-cat">{p.category}</span>
                  <span>{p.readMinutes} min</span>
                </div>
                <h3>{p.title}</h3>
                <p>{p.excerpt}</p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
