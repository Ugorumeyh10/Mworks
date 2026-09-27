import { Link } from 'react-router-dom';
import Icon from './Icon.jsx';
import { money } from '../data/marketplace.js';
import './MarketplaceCard.css';

export default function MarketplaceCard({ listing }) {
  const isPrompt = listing.type === 'prompt';
  const isDoc = listing.type === 'document';
  const isAgent = listing.type === 'agent';
  const thumb = isPrompt || isAgent ? 'prompt' : isDoc ? 'prompt' : 'automation';
  const icon = isPrompt || isAgent ? 'bot' : isDoc ? 'cap' : 'tag';
  const typeLabel = isAgent
    ? 'AI interviewer'
    : isPrompt
    ? `${listing.promptCount}-prompt pack`
    : isDoc
      ? (listing.license ? `${listing.license} pack` : 'Document pack')
      : listing.platform;
  return (
    <Link to={`/listing/${listing.id}`} className="mkc">
      <div className={`mkc-thumb ${thumb}`}>
        <Icon name={icon} />
        {listing.verified && (
          <span className="mkc-verified">
            <Icon name="shield" className="sm" />
            {listing.verifyType === 'sandbox' ? 'Sandbox verified' : 'Originality checked'}
          </span>
        )}
      </div>

      <div className="mkc-body">
        <div className="mkc-cat">{listing.category}</div>
        <h3 className="mkc-title">{listing.title}</h3>
        <p className="mkc-blurb">{listing.blurb}</p>

        <div className="mkc-meta">
          <span className="avatar sm">{listing.seller.avatar}</span>
          <span className="mkc-seller">{listing.seller.name}</span>
          <span className="mkc-trust">Trust {listing.seller.trust}</span>
          <span className="mkc-rating">
            <Icon name="star" className="sm" /> {listing.rating.toFixed(1)}
          </span>
        </div>
      </div>

      <div className="mkc-foot">
        <span className="mkc-price">{money(listing.priceValue)}</span>
        <span className="mkc-type">{typeLabel}</span>
      </div>
    </Link>
  );
}
