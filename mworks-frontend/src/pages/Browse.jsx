import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import MarketplaceCard from '../components/MarketplaceCard.jsx';
import { categories as localCategories } from '../data/marketplace.js';
import { fetchListings } from '../api/listings.js';
import './Browse.css';

const PRICE_BUCKETS = [
  { id: 'any', label: 'Any price', test: () => true },
  { id: '0-25k', label: 'Under ₦25,000', test: (n) => n < 25000 },
  { id: '25k-100k', label: '₦25,000 - ₦100,000', test: (n) => n >= 25000 && n < 100000 },
  { id: '100k-300k', label: '₦100,000 - ₦300,000', test: (n) => n >= 100000 && n < 300000 },
  { id: '300k+', label: '₦300,000+', test: (n) => n >= 300000 },
];
const SORTS = [
  { id: 'relevance', label: 'Relevance' },
  { id: 'newest', label: 'Newest' },
  { id: 'price-asc', label: 'Price: low to high' },
  { id: 'price-desc', label: 'Price: high to low' },
  { id: 'rating', label: 'Top rated' },
];

export default function Browse() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') || '';

  const [type, setType] = useState(params.get('type') || 'all');
  const [cats, setCats] = useState(() => new Set());
  const [bucket, setBucket] = useState('any');
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [minRating, setMinRating] = useState(0);
  const [sort, setSort] = useState('relevance');
  const [showFilters, setShowFilters] = useState(false);
  const [listings, setListings] = useState([]);

  useEffect(() => {
    let live = true;
    fetchListings({ q, type, sort: sort === 'newest' ? 'newest' : 'quality' }).then((rows) => {
      if (live) setListings(rows);
    });
    return () => {
      live = false;
    };
  }, [q, type, sort]);

  const toggleCat = (c) => {
    setCats((prev) => {
      const next = new Set(prev);
      if (next.has(c)) next.delete(c);
      else next.add(c);
      return next;
    });
  };

  const clearAll = () => {
    setType('all');
    setCats(new Set());
    setBucket('any');
    setVerifiedOnly(false);
    setMinRating(0);
    setParams({});
  };

  const results = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const priceTest = PRICE_BUCKETS.find((b) => b.id === bucket).test;
    let out = listings.filter((l) => {
      if (type !== 'all' && l.type !== type) return false;
      if (cats.size && !cats.has(l.category)) return false;
      if (!priceTest(l.priceValue)) return false;
      if (verifiedOnly && !l.verified) return false;
      if (minRating && l.rating < minRating) return false;
      if (needle) {
        const hay = (l.title + ' ' + l.blurb + ' ' + (l.tags || []).join(' ') + ' ' + (l.seller?.name || '')).toLowerCase();
        if (!hay.includes(needle)) return false;
      }
      return true;
    });
    if (sort === 'price-asc') out = [...out].sort((a, b) => a.priceValue - b.priceValue);
    else if (sort === 'price-desc') out = [...out].sort((a, b) => b.priceValue - a.priceValue);
    else if (sort === 'rating') out = [...out].sort((a, b) => b.rating - a.rating);
    else if (sort === 'newest') out = [...out];
    else out = [...out].sort((a, b) => (b.qualityScore || 0) - (a.qualityScore || 0));
    return out;
  }, [listings, q, type, cats, bucket, verifiedOnly, minRating, sort]);

  const activeCount =
    (type !== 'all' ? 1 : 0) + cats.size + (bucket !== 'any' ? 1 : 0) + (verifiedOnly ? 1 : 0) + (minRating ? 1 : 0);

  const filters = (
    <div className="bf">
      <div className="bf-group">
        <span className="bf-label">Type</span>
        <div className="mk-seg">
          {['all', 'automation', 'prompt', 'document', 'agent'].map((t) => (
            <button key={t} className={type === t ? 'on' : ''} onClick={() => setType(t)}>
              {t === 'all' ? 'All' : t === 'automation' ? 'Automations' : t === 'prompt' ? 'Prompts' : t === 'document' ? 'Documents' : 'Agents'}
            </button>
          ))}
        </div>
      </div>

      <div className="bf-group">
        <span className="bf-label">Category</span>
        {localCategories.map((c) => (
          <label key={c} className="bf-check">
            <input type="checkbox" checked={cats.has(c)} onChange={() => toggleCat(c)} />
            {c}
          </label>
        ))}
      </div>

      <div className="bf-group">
        <span className="bf-label">Price</span>
        {PRICE_BUCKETS.map((b) => (
          <label key={b.id} className="bf-check">
            <input type="radio" name="bucket" checked={bucket === b.id} onChange={() => setBucket(b.id)} />
            {b.label}
          </label>
        ))}
      </div>

      <div className="bf-group">
        <span className="bf-label">Rating</span>
        <div className="bf-chips">
          {[0, 4, 4.5].map((r) => (
            <button
              key={r}
              className={'chip' + (minRating === r ? ' on' : '')}
              onClick={() => setMinRating(r)}
            >
              {r === 0 ? 'Any' : `${r}+`}
            </button>
          ))}
        </div>
      </div>

      <label className="bf-check bf-verified">
        <input type="checkbox" checked={verifiedOnly} onChange={(e) => setVerifiedOnly(e.target.checked)} />
        Verified listings only
      </label>

      {activeCount > 0 && (
        <button className="bf-clear" onClick={clearAll}>
          <Icon name="x" className="sm" /> Clear filters
        </button>
      )}
    </div>
  );

  return (
    <div className="mk-page browse">
      <div className="mk-head">
        <div>
          <h1>Browse the marketplace</h1>
          <p className="sub">
            {q ? (
              <>
                Results for <strong>“{q}”</strong>
              </>
            ) : (
              'Verified automations, prompt packs, and document packs ranked by quality, not recency alone.'
            )}
          </p>
        </div>
        <button className="mk-btn ghost sm bf-toggle" onClick={() => setShowFilters((v) => !v)}>
          <Icon name="filter" className="sm" /> Filters{activeCount ? ` · ${activeCount}` : ''}
        </button>
      </div>

      <div className="browse-grid">
        <aside className={'browse-side' + (showFilters ? ' open' : '')}>{filters}</aside>

        <div className="browse-main">
          <div className="browse-bar">
            <span className="browse-count">{results.length} listing{results.length === 1 ? '' : 's'}</span>
            <label className="browse-sort">
              Sort
              <select value={sort} onChange={(e) => setSort(e.target.value)}>
                {SORTS.map((s) => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
            </label>
          </div>

          {results.length === 0 ? (
            <div className="mk-empty">No listings match these filters. Try widening your price range or clearing filters.</div>
          ) : (
            <div className="browse-results">
              {results.map((l) => (
                <MarketplaceCard key={l.id} listing={l} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
