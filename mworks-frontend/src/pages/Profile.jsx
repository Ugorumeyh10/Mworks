import { Link, useParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import MarketplaceCard from '../components/MarketplaceCard.jsx';
import { getProfile, listingsBySeller, reviewsForSeller } from '../data/profile.js';
import './Profile.css';

const ROLE_LABEL = { buyer: 'Buyer', seller: 'Seller', employer: 'Employer', candidate: 'Open to work' };

export default function Profile() {
  const { handle } = useParams();
  const p = getProfile(handle);

  if (!p) {
    return (
      <div className="mk-page mk-narrow">
        <Link to="/browse" className="mk-back"><Icon name="arrow-left" className="sm" /> Marketplace</Link>
        <div className="mk-empty">No profile found for “{handle}”.</div>
      </div>
    );
  }

  const listings = listingsBySeller(p.name);
  const reviews = reviewsForSeller(p.name);
  const idVerified = p.identity?.status === 'verified';

  return (
    <div className="mk-page">
      <div className="mk-card pf-header">
        <div className="pf-id">
          <span className="avatar pf-avatar">{p.avatar}</span>
          <div>
            <div className="pf-name-row">
              <h1>{p.name}</h1>
              {idVerified && (
                <span className="mk-pill ok"><Icon name="shield" className="sm" /> Verified identity</span>
              )}
            </div>
            <div className="pf-handle">@{p.handle}</div>
            <p className="pf-headline">{p.headline}</p>
            <div className="pf-meta">
              {p.roles.map((r) => <span className="mk-pill info" key={r}>{ROLE_LABEL[r] || r}</span>)}
              {p.location && <span className="pf-meta-item"><Icon name="pin" className="sm" /> {p.location}</span>}
              <span className="pf-meta-item"><Icon name="clock" className="sm" /> Member since {p.memberSince}</span>
            </div>
          </div>
        </div>
        <div className="pf-actions">
          {p.isMe ? (
            <Link to="/settings/profile" className="mk-btn ghost sm"><Icon name="pencil" className="sm" /> Edit profile</Link>
          ) : (
            <>
              <button className="mk-btn sm">Follow</button>
              <Link to="/messages" className="mk-btn ghost sm">Message</Link>
            </>
          )}
        </div>
      </div>

      <div className="mk-tiles pf-tiles">
        <div className="mk-tile"><b>{p.trustScore}</b><span>Trust score</span></div>
        <div className="mk-tile"><b>{p.points.toLocaleString('en-NG')}</b><span>Reputation points</span></div>
        <div className="mk-tile"><b>{p.rating.toFixed(1)}</b><span>Rating · {p.ratingCount} reviews</span></div>
        <div className="mk-tile"><b>{p.stats.sales}</b><span>Completed sales</span></div>
        <div className="mk-tile"><b>{p.stats.completionRate}%</b><span>Completion rate</span></div>
      </div>

      {p.skills?.length > 0 && (
        <>
          <h2 className="pf-h2">Verified skills</h2>
          <div className="pf-skills">
            {p.skills.map((s) => <span className="chip" key={s}>{s}</span>)}
          </div>
        </>
      )}

      <h2 className="pf-h2">Listings{listings.length ? ` (${listings.length})` : ''}</h2>
      {listings.length === 0 ? (
        <div className="mk-empty">No public listings yet.</div>
      ) : (
        <div className="pf-listings">
          {listings.map((l) => <MarketplaceCard key={l.id} listing={l} />)}
        </div>
      )}

      <h2 className="pf-h2">Reviews received{reviews.length ? ` (${reviews.length})` : ''}</h2>
      {reviews.length === 0 ? (
        <div className="mk-empty">No reviews yet.</div>
      ) : (
        <div className="mk-card pf-reviews">
          {reviews.map((r, i) => (
            <div className="pf-review" key={i}>
              <div className="pf-review-top">
                <strong>{r.author}</strong>
                <span className="pf-review-stars">{'★'.repeat(r.stars || 5)}</span>
              </div>
              <p>{r.text}</p>
              <span className="pf-review-listing">on {r.listing}</span>
            </div>
          ))}
        </div>
      )}

      {p.links?.length > 0 && (
        <>
          <h2 className="pf-h2">Links</h2>
          <div className="pf-links">
            {p.links.map((l) => (
              <span className="pf-link" key={l.label}>
                <Icon name="external" className="sm" /> {l.label} - {l.url}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
