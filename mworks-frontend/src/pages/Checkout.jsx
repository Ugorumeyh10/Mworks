import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { paymentMethods, commissionRate, money } from '../data/marketplace.js';
import { checkoutListing, fetchListing } from '../api/listings.js';
import { apiEnabled } from '../api/client.js';
import { getToken } from '../api/session.js';
import './Checkout.css';

const REVISE_CAP = 25000;

export default function Checkout() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const mode = params.get('mode');
  const isHire = mode === 'hire';
  const isRevise = mode === 'revise';
  const scoped = isHire || isRevise;

  const [listing, setListing] = useState(null);
  const [missing, setMissing] = useState(false);
  const [method, setMethod] = useState('paystack');
  const [terms, setTerms] = useState(false);
  const [brief, setBrief] = useState('');
  const [budget, setBudget] = useState(isRevise ? '15000' : '');
  const [timeline, setTimeline] = useState('Under 1 week');
  const [errors, setErrors] = useState({});
  const [done, setDone] = useState(null);

  useEffect(() => {
    let live = true;
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

  if (missing) {
    return (
      <div className="mk-page mk-narrow">
        <p className="body-text">This listing is not available for checkout.</p>
        <Link to="/browse">Back to marketplace</Link>
      </div>
    );
  }

  if (!listing) return <p className="body-text">Loading checkout…</p>;

  if (listing.status && listing.status !== 'live') {
    return (
      <div className="mk-page mk-narrow">
        <p className="body-text">This listing is not on the public catalog yet.</p>
        <Link to="/browse">Back to marketplace</Link>
      </div>
    );
  }

  const amount = scoped ? parseFloat(budget) || 0 : listing.priceValue;
  const rate = commissionRate(listing.type);
  const sellerGets = amount * (1 - rate);

  const pay = async (e) => {
    e.preventDefault();
    const next = {};
    if (scoped) {
      if (brief.trim().length < 20) next.brief = 'Describe the change you need.';
      if (!(parseFloat(budget) > 0)) next.budget = 'Enter a proposed budget.';
      if (isRevise && parseFloat(budget) > REVISE_CAP) next.budget = 'Revise orders are capped at ₦25,000.';
    }
    if (!terms) next.terms = 'Accept the escrow terms to continue.';
    setErrors(next);
    if (Object.keys(next).length !== 0) return;

    if (apiEnabled() && getToken()) {
      try {
        const kind = isRevise ? 'revise' : isHire ? 'hire' : 'purchase';
        const order = await checkoutListing(listing.id, {
          kind,
          brief: scoped ? brief.trim() : undefined,
          budget: scoped ? Math.round(parseFloat(budget)) : undefined,
        });
        if (order.paymentUrl) {
          window.location.assign(order.paymentUrl);
          return;
        }
        navigate(`/orders/${order.id}`);
        return;
      } catch (err) {
        setErrors({ terms: err.message || 'Could not start payment.' });
        return;
      }
    }
    navigate(`/login?next=${encodeURIComponent(`/checkout/${listing.id}${scoped ? `?mode=${isRevise ? 'revise' : 'hire'}` : ''}`)}`);
  };

  const isAgent = listing.type === 'agent';
  const title = isRevise ? 'Revise this pack' : isHire ? 'Hire for customization' : isAgent ? 'Buy hosted interviewer' : 'Checkout';

  if (done) {
    return (
      <div className="mk-page mk-narrow">
        <div className="co-done">
          <span className="co-done-icon"><Icon name="lock" /></span>
          <h1>{scoped ? 'Escrow funded: brief sent' : 'Payment held in escrow'}</h1>
          <p>
            {money(amount)} is held safely by Mworks. {scoped
              ? 'The seller has been sent your brief. Funds release only when you accept the delivered work. If they decline, you are refunded in full.'
              : 'The seller has been notified. Funds release to them only when you confirm delivery from your orders page.'}
          </p>
          <div className="co-done-ref">Order <b>{done}</b> · paid via {paymentMethods.find((m) => m.id === method).name}</div>
          <div className="co-done-actions">
            <Link to="/orders" className="mk-btn">Go to my orders</Link>
            <Link to="/browse" className="mk-btn ghost">Keep browsing</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mk-page mk-narrow">
      <Link to={`/listing/${listing.id}`} className="mk-back"><Icon name="arrow-left" className="sm" /> Back to listing</Link>
      <div className="mk-head">
        <div>
          <h1>{title}</h1>
          <p className="sub">
            {isRevise
              ? 'A capped, one-round edit. 48-hour target. Funds sit in escrow until you accept.'
              : isHire
                ? isAgent
                  ? 'Fund escrow for a custom rubric. Hosted interviewer access unlocks after payment. Funds release when you accept the work.'
                  : 'Send the seller a brief and fund escrow. Nothing is released until you accept the work.'
                : isAgent
                  ? 'Pay for a hosted license. After payment you get interviewer seats and a downloadable playbook.'
                  : 'Your payment is held in escrow until you confirm delivery.'}
          </p>
        </div>
      </div>

      <div className="co-grid">
        <form className="co-form" onSubmit={pay} noValidate>
          {scoped && (
            <div className="mk-card">
              <div className="mk-sec-title">{isRevise ? 'Revise brief' : 'Customization brief'}</div>
              <div className={'co-field' + (errors.brief ? ' bad' : '')}>
                <label htmlFor="brief">What do you need changed or added?</label>
                <textarea id="brief" rows="4" value={brief} onChange={(e) => setBrief(e.target.value)}
                  placeholder="e.g. Adapt the canvas to a payroll close process." />
                {errors.brief && <span className="co-err">{errors.brief}</span>}
              </div>
              <div className="co-two">
                <div className={'co-field' + (errors.budget ? ' bad' : '')}>
                  <label htmlFor="budget">Proposed budget (₦){isRevise ? ' · max 25,000' : ''}</label>
                  <input id="budget" type="number" min="0" max={isRevise ? REVISE_CAP : undefined}
                    value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="0" />
                  {errors.budget && <span className="co-err">{errors.budget}</span>}
                </div>
                <div className="co-field">
                  <label htmlFor="timeline">Timeline</label>
                  <select id="timeline" value={timeline} onChange={(e) => setTimeline(e.target.value)}>
                    <option>Under 1 week</option>
                    <option>1-2 weeks</option>
                    <option>2-4 weeks</option>
                    <option>Flexible</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          <div className="mk-card">
            <div className="mk-sec-title">Payment method</div>
          {paymentMethods.map((m) => (
              <label key={m.id} className={'co-pay' + (method === m.id ? ' on' : '') + (m.id !== 'paystack' ? ' dim' : '')}>
                <input
                  type="radio"
                  name="pay"
                  checked={method === m.id}
                  disabled={m.id !== 'paystack'}
                  onChange={() => setMethod(m.id)}
                />
                <span className="co-pay-name">{m.name}{m.id !== 'paystack' ? ' (soon)' : ''}</span>
                <span className="co-pay-desc">{m.desc}</span>
              </label>
            ))}
            <p className="co-secure">
              <Icon name="lock" className="sm" />
              Mworks never stores your card details. Payment is handled entirely by the gateway.
            </p>
          </div>

          <label className={'co-terms' + (errors.terms ? ' bad' : '')}>
            <input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} />
            <span>
              I understand funds are held in escrow and released to the seller only on my confirmation,
              and I agree to the <a href="/">escrow and refund terms</a>.
            </span>
          </label>
          {errors.terms && <span className="co-err">{errors.terms}</span>}

          <button type="submit" className="mk-btn wide" disabled={scoped && !(parseFloat(budget) > 0)}>
            <Icon name="lock" className="sm" />
            {scoped ? `Fund escrow: ${money(amount)}` : isAgent ? `Pay for hosted license: ${money(amount)}` : `Pay and fund escrow: ${money(amount)}`}
          </button>
        </form>

        <aside className="co-summary">
          <div className="mk-card">
            <div className="mk-sec-title">Order summary</div>
            <div className="co-item">
              <span className={`co-thumb ${listing.type}`}>
                <Icon name={listing.type === 'prompt' || listing.type === 'agent' ? 'bot' : listing.type === 'document' ? 'cap' : 'tag'} />
              </span>
              <div>
                <strong>{listing.title}</strong>
                <span className="co-item-sub">
                  {listing.type === 'agent'
                    ? 'Hosted AI interviewer'
                    : listing.type === 'prompt'
                      ? `${listing.promptCount}-prompt pack`
                      : listing.type === 'document'
                        ? 'Document pack'
                        : listing.platform} · {listing.seller.name}
                </span>
              </div>
            </div>

            <div className="co-lines">
              <div className="co-line">
                <span>{scoped ? (isRevise ? 'Revise budget' : 'Customization budget') : 'Item price'}</span>
                <span>{money(amount || 0)}</span>
              </div>
              <div className="co-line">
                <span>Buyer fee</span>
                <span>{money(0)}</span>
              </div>
              <div className="co-line total">
                <span>{scoped ? 'Funded to escrow' : 'Total charged'}</span>
                <span>{money(amount || 0)}</span>
              </div>
            </div>

            <div className="co-escrow">
              <Icon name="shield" className="sm" />
              <div>
                Held in escrow by Mworks. On release, the seller receives{' '}
                <b>{money(sellerGets || 0)}</b> after the {Math.round(rate * 100)}% commission.
              </div>
            </div>
            {scoped && <div className="co-tl-note">Estimated timeline: {timeline}</div>}
          </div>
        </aside>
      </div>
    </div>
  );
}
