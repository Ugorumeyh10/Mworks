import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { money } from '../data/marketplace.js';
import { slug } from '../data/profile.js';
import { fetchListing, fileTheftClaim, publishListing } from '../api/listings.js';
import { fetchInterviewerLicense, startInterviewerTrial } from '../api/interviewer.js';
import { getToken } from '../api/session.js';
import './Listing.css';

export default function Listing() {
  const { id } = useParams();
  const [listing, setListing] = useState(null);
  const [missing, setMissing] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState('');
  const [claim, setClaim] = useState('');
  const [claimMsg, setClaimMsg] = useState('');
  const [trialMsg, setTrialMsg] = useState('');
  const [operator, setOperator] = useState(false);

  useEffect(() => {
    let live = true;
    setMissing(false);
    setListing(null);
    setOperator(false);
    fetchListing(id)
      .then((row) => {
        if (!live) return;
        if (row) setListing(row);
        else setMissing(true);
      })
      .catch(() => {
        if (live) setMissing(true);
      });
    return () => {
      live = false;
    };
  }, [id]);

  useEffect(() => {
    if (!listing || listing.type !== 'agent' || !getToken()) return undefined;
    let live = true;
    fetchInterviewerLicense(listing.id)
      .then((row) => {
        if (live) setOperator(row?.plan === 'seller');
      })
      .catch(() => {
        if (live) setOperator(false);
      });
    return () => { live = false; };
  }, [listing]);

  if (missing) {
    return (
      <div className="listing-page">
        <Link to="/browse" className="back-link"><Icon name="arrow-left" className="sm" /> Back to marketplace</Link>
        <p className="body-text">This listing is not on the catalog.</p>
      </div>
    );
  }

  if (!listing) {
    return <p className="body-text">Loading listing…</p>;
  }

  const isPrompt = listing.type === 'prompt';
  const isDoc = listing.type === 'document';
  const isAgent = listing.type === 'agent';
  const live = listing.status === 'live' || !listing.status;
  const sellerSub = `${listing.seller.sales} sales · ${listing.seller.rating}★ from ${listing.seller.reviews} reviews · since ${listing.seller.since}`;
  const verifyLabel = listing.verifyType === 'sandbox'
    ? 'Verified: sandbox tested'
    : 'Verified: originality checked';

  const goLive = async () => {
    setError('');
    setPublishing(true);
    try {
      const next = await publishListing(listing.id);
      setListing(next);
    } catch (err) {
      setError(err.message || 'Could not publish this listing.');
    } finally {
      setPublishing(false);
    }
  };

  const startTrial = async () => {
    setError('');
    setTrialMsg('');
    try {
      await startInterviewerTrial(listing.id);
      setTrialMsg('Trial is on. Open the interviewer console to upload docs and start a session.');
    } catch (err) {
      setError(err.message || 'Could not start the trial.');
    }
  };

  const reportTheft = async () => {
    setError('');
    setClaimMsg('');
    try {
      await fileTheftClaim(listing.id, claim.trim());
      setClaim('');
      setClaimMsg('Claim queued for human review. A listing is not taken down until a reviewer upholds it.');
    } catch (err) {
      setError(err.message || 'Could not file that claim.');
    }
  };

  return (
    <div className="listing-page">
      <Link to="/browse" className="back-link"><Icon name="arrow-left" className="sm" /> Back to marketplace</Link>

      {!live && (
        <div className="listing-private">
          <p>This listing is not on the public catalog. Buyers cannot check out until verification passes.</p>
          {getToken() && listing.status !== 'live' && (
            <button type="button" className="mk-btn sm" onClick={goLive} disabled={publishing}>
              {publishing ? 'Checking…' : 'Run verification'}
            </button>
          )}
        </div>
      )}
      {error && <p className="body-text" role="alert">{error}</p>}
      {trialMsg && <p className="body-text">{trialMsg}</p>}

      <div className="listing-hero">
        <Icon name={isPrompt || isAgent ? 'bot' : isDoc ? 'cap' : 'tag'} />
        <span>
          {isAgent
            ? 'Hosted AI interviewer. Disclosed as AI. Never a fake human.'
            : isPrompt
              ? 'Sample output preview'
              : isDoc
                ? `${listing.title}: pack preview`
                : `${listing.title}: video demo`}
        </span>
      </div>

      <div className="listing-top">
        <h1>{listing.title}</h1>
        <span className="listing-price">{money(listing.priceValue)}</span>
      </div>

      <div className="listing-chips">
        {listing.verified && (
          <span className="chip verified-chip">{verifyLabel}</span>
        )}
        <span className="chip">{listing.category}</span>
        {listing.license && <span className="chip">{listing.license}</span>}
        {listing.tags?.map((t) => (
          <span className="chip" key={t}>{t}</span>
        ))}
      </div>

      {isPrompt ? (
        <div className="metrics-row">
          <div className="metric-box"><b>{listing.promptCount}</b><span>Prompts in pack</span></div>
          <div className="metric-box"><b>{listing.models.length}</b><span>Supported models</span></div>
          <div className="metric-box"><b>{listing.rating.toFixed(1)}</b><span>Rating · {listing.reviewCount} reviews</span></div>
        </div>
      ) : (
        listing.metrics && listing.metrics.length > 0 && (
          <div className="metrics-row">
            {listing.metrics.map((m) => (
              <div className="metric-box" key={m.label}>
                <b>{m.value}</b>
                <span>{m.label}</span>
              </div>
            ))}
          </div>
        )
      )}

      <div className="seller-card">
        <span className="avatar">{listing.seller.avatar}</span>
        <div>
          <Link to={`/u/${slug(listing.seller.name)}`} className="seller-link">{listing.seller.name}</Link>
          <div className="seller-sub">{sellerSub}</div>
        </div>
        <button className="follow-btn">Follow</button>
      </div>

      <h3 className="sec-title">Description</h3>
      <p className="body-text">{listing.description}</p>

      {isAgent && (
        <p className="body-text">
          Delivery: hosted license plus a downloadable playbook. Start a capped free trial, buy seats, or hire the seller
          to customize the rubric. The agent always says it is an AI. A human still decides any hire.
        </p>
      )}

      {isPrompt && (
        <>
          <h3 className="sec-title">Works with</h3>
          <div className="listing-chips">
            {listing.models.map((m) => <span className="chip" key={m}>{m}</span>)}
          </div>
          <p className="body-text" style={{ marginTop: 12 }}>
            Delivery: {listing.delivery}. Full prompt text is unlocked after purchase; the sample output above is the buyer preview.
          </p>
        </>
      )}

      {isDoc && (
        <p className="body-text">
          Delivery: {listing.delivery}. The first two pages are the public preview. The full pack unlocks after escrow.
          Need it adapted to your process? Use Revise. It is capped at ₦25,000 and one round.
        </p>
      )}

      {listing.verificationLog && (
        <>
          <h3 className="sec-title">Verification log</h3>
          {listing.verificationLog.map((v, i) => (
            <div className="vrow" key={`${v.label}-${i}`}>
              <span>{v.label}</span>
              <span className={String(v.status).toLowerCase().includes('fail') ? 'bad' : 'ok'}>{v.status}</span>
            </div>
          ))}
        </>
      )}

      <h3 className="sec-title">Reviews: post-purchase only</h3>
      {listing.reviews && listing.reviews.length > 0 ? (
        listing.reviews.map((r) => (
          <div className="review-row" key={r.author}>
            <strong>{r.author}:</strong> {r.text}
            <span className="stars">{'★'.repeat(r.stars || 5)}</span>
          </div>
        ))
      ) : (
        <p className="body-text">No reviews yet. This listing is newly verified.</p>
      )}

      {getToken() && (
        <div className="listing-claim">
          <h3 className="sec-title">Report a copy or theft</h3>
          <p className="body-text">Exact SHA-256 matches are blocked at publish. Near-copies go to human review. Filing a claim does not silently unpublish.</p>
          <textarea
            className="jd-note"
            rows="3"
            placeholder="Describe the original pack and why this listing copies it."
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
          />
          {claimMsg && <p className="body-text">{claimMsg}</p>}
          <button type="button" className="mk-btn ghost sm" onClick={reportTheft} disabled={claim.trim().length < 20}>
            Submit for human review
          </button>
        </div>
      )}

      {live ? (
      <div className="buy-bar">
        <span className="buy-price">{money(listing.priceValue)}</span>
        {isAgent ? (
          <>
            {operator ? (
              <Link to={`/interviewer?listing=${listing.id}`} className="hire-btn">Open console</Link>
            ) : (
              <>
                <Link to={`/checkout/${listing.id}`} className="buy-btn">Buy hosted license</Link>
                <Link to={`/checkout/${listing.id}?mode=hire`} className="hire-btn">Hire to customize</Link>
                {getToken() ? (
                  <button type="button" className="hire-btn" onClick={startTrial}>Start free trial</button>
                ) : (
                  <Link to={`/login?next=/listing/${listing.id}`} className="hire-btn">Sign in to trial</Link>
                )}
                <Link to={`/interviewer?listing=${listing.id}`} className="hire-btn">Open console</Link>
              </>
            )}
          </>
        ) : (
          <>
            <Link to={`/checkout/${listing.id}`} className="buy-btn">Buy now: escrow protected</Link>
            {isDoc ? (
              <Link to={`/checkout/${listing.id}?mode=revise`} className="hire-btn">Revise this pack</Link>
            ) : !isPrompt && (
              <Link to={`/checkout/${listing.id}?mode=hire`} className="hire-btn">Hire for customization</Link>
            )}
          </>
        )}
      </div>
      ) : (
        <div className="buy-bar">
          <span className="buy-price">{money(listing.priceValue)}</span>
          <span className="body-text">Checkout unlocks after publish.</span>
        </div>
      )}
    </div>
  );
}
