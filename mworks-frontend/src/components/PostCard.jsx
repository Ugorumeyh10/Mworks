import { useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from './Icon.jsx';
import './PostCard.css';

export default function PostCard({ post, onOpen }) {
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(post.likes || 0);

  const toggleLike = () => {
    setLiked((v) => !v);
    setLikeCount((c) => (liked ? c - 1 : c + 1));
  };

  const isJob = post.type === 'job';
  const href = post.href || (isJob ? '/jobs/board' : `/listing/${post.id}`);
  const seller = post.seller || {};

  return (
    <article className="post-card">
      {!isJob && (
        <div className={`post-media media-${post.type || 'automation'}`}>
          <span>{post.title}</span>
          {post.verified && <span className="badge-verified">Verified</span>}
          {post.meta && <span className="media-metric">{post.meta}</span>}
        </div>
      )}

      <div className="post-body">
        {isJob ? (
          <>
            <span className="job-flag">Job</span>
            <h4 className="post-title">{post.title}</h4>
            <p className="job-meta">{post.meta}</p>
          </>
        ) : (
          <div className="post-header">
            <span className={`avatar sm${seller.org ? ' org' : ''}`}>{seller.avatar || '?'}</span>
            <div className="post-who">
              <strong>{seller.name || 'Mworks'}</strong>
              {seller.trust ? <span className="trust-label">Trust score {seller.trust}</span> : null}
              {post.type === 'training' && <span className="partner-label">Training partner</span>}
            </div>
          </div>
        )}

        <p className="caption">{post.caption}</p>

        <div className="post-actions">
          <button className={`action-btn${liked ? ' liked' : ''}`} onClick={toggleLike}>
            <Icon name="heart" className="sm" /> {likeCount}
          </button>
          <span className="action-btn"><Icon name="message" className="sm" /> {post.comments || 0}</span>

          <Link to={href} className="cta-btn" onClick={onOpen}>
            {isJob ? 'View role' : post.priceValue ? `View · ₦${Number(post.priceValue).toLocaleString('en-NG')}` : 'View'}
          </Link>
        </div>
      </div>
    </article>
  );
}
