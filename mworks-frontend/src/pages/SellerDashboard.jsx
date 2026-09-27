import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { money, commissionRate, STATE_LABEL, STATE_TONE } from '../data/marketplace.js';
import { fileTheftClaim, publishListing, uploadDeliveryFile } from '../api/listings.js';
import { fetchMyListings, fetchOrders, markDelivered } from '../api/orders.js';
import { getToken, getUser } from '../api/session.js';
import './Sell.css';

const STATUS = {
  live: { tone: 'ok', label: 'Verified - live' },
  verified: { tone: 'ok', label: 'Verified - live' },
  in_review: { tone: 'warn', label: 'In review' },
  pending_review: { tone: 'warn', label: 'Near-copy review' },
  draft: { tone: 'info', label: 'Draft' },
  rejected: { tone: 'bad', label: 'Needs changes' },
};

function typeLabel(type) {
  if (type === 'prompt') return 'Prompt pack';
  if (type === 'document') return 'Document pack';
  if (type === 'agent') return 'AI interviewer';
  return 'Automation';
}

function lastCheck(listing) {
  const log = listing.verificationLog || [];
  return log.length ? log[log.length - 1] : null;
}

export default function SellerDashboard() {
  const [mine, setMine] = useState([]);
  const [sales, setSales] = useState([]);
  const [files, setFiles] = useState({});
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [dispute, setDispute] = useState({});
  const authed = Boolean(getToken());
  const isAdmin = Boolean(getUser()?.isAdmin);

  const load = () => {
    fetchMyListings().then(setMine).catch(() => setMine([]));
    fetchOrders('selling').then(setSales).catch(() => setSales([]));
  };

  useEffect(() => {
    if (!authed) return undefined;
    load();
    return undefined;
  }, [authed]);

  const verify = async (id) => {
    setError('');
    setBusy(`pub-${id}`);
    try {
      const row = await publishListing(id);
      if (row.status !== 'live') {
        setError('Verification did not pass. Check the log on this listing.');
      }
      load();
    } catch (err) {
      setError(err.message || 'Could not run verification.');
    } finally {
      setBusy('');
    }
  };

  const deliver = async (id) => {
    const file = files[id];
    if (!file) {
      setError('Upload the delivered pack before marking this order delivered.');
      return;
    }
    setError('');
    setBusy(`del-${id}`);
    try {
      const objectKey = await uploadDeliveryFile(file);
      await markDelivered(id, objectKey);
      setFiles((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      load();
    } catch (err) {
      setError(err.message || 'Could not upload the delivered pack.');
    } finally {
      setBusy('');
    }
  };

  const disputeListing = async (id) => {
    const reason = (dispute[id] || '').trim();
    if (reason.length < 20) {
      setError('Explain the original work in at least 20 characters.');
      return;
    }
    setError('');
    setBusy(`claim-${id}`);
    try {
      await fileTheftClaim(id, reason);
      setDispute((prev) => ({ ...prev, [id]: '' }));
      load();
    } catch (err) {
      setError(err.message || 'Could not queue that dispute.');
    } finally {
      setBusy('');
    }
  };

  if (!authed) {
    return (
      <div className="mk-page">
        <h1>Seller workspace</h1>
        <div className="mk-empty">
          <Link to="/login?next=/sell">Sign in</Link> with a seller account to manage listings.
        </div>
      </div>
    );
  }

  const escrowNet = sales
    .filter((s) => s.state === 'funds_held' || s.state === 'delivered')
    .reduce((sum, s) => sum + s.amount * (1 - commissionRate(s.type)), 0);

  return (
    <div className="mk-page">
      <div className="mk-head">
        <div>
          <h1>Seller workspace</h1>
          <p className="sub">Listings go live after originality or sandbox checks. Hire and revise orders need an uploaded delivery pack.</p>
        </div>
        <Link to="/sell/new" className="mk-btn"><Icon name="plus" className="sm" /> New listing</Link>
        {isAdmin && <Link to="/sell/claims" className="mk-btn ghost">Trust review</Link>}
      </div>

      <div className="mk-tiles">
        <div className="mk-tile"><b>{money(escrowNet)}</b><span>Held in escrow</span></div>
        <div className="mk-tile"><b>{mine.length}</b><span>Listings</span></div>
        <div className="mk-tile"><b>{sales.length}</b><span>Sales</span></div>
      </div>

      {error && <p className="sf-err sell-banner-err" role="alert">{error}</p>}

      <h2 className="sell-h2">My listings</h2>
      {mine.length === 0 ? (
        <div className="mk-empty">No listings yet. <Link to="/sell/new" className="mk-inline-link">Create your first one.</Link></div>
      ) : (
        mine.map((l) => {
          const st = STATUS[l.status] || STATUS.draft;
          const publishing = busy === `pub-${l.id}`;
          const check = lastCheck(l);
          const canVerify = l.status === 'in_review' || l.status === 'draft' || l.status === 'rejected';
          return (
            <div className="mk-card sell-listing" key={l.id}>
              <div className="sell-listing-top">
                <div>
                  <div className="sell-listing-title">
                    {l.title}
                    <span className="mk-pill info">{typeLabel(l.type)}</span>
                  </div>
                  <div className="sell-listing-meta">
                    {money(l.priceValue)}
                    {check && (
                      <span className={`verify-status ${String(check.status).toLowerCase()}`}>
                        {check.label}: {check.status}
                      </span>
                    )}
                  </div>
                </div>
                <div className="sell-listing-right">
                  <span className={`mk-pill ${st.tone}`}>{st.label}</span>
                  {canVerify && (
                    <>
                      <Link to={`/listing/${l.id}`} className="mk-btn ghost sm">Preview</Link>
                      <button type="button" className="mk-btn sm" onClick={() => verify(l.id)} disabled={Boolean(busy)}>
                        {publishing ? 'Checking…' : 'Run verification'}
                      </button>
                    </>
                  )}
                  {l.status === 'live' && (
                    <>
                      <Link to={`/listing/${l.id}`} className="mk-btn ghost sm">View</Link>
                      {l.type === 'agent' && (
                        <Link to={`/interviewer?listing=${l.id}`} className="mk-btn sm">Open console</Link>
                      )}
                    </>
                  )}
                </div>
              </div>
              {(l.status === 'rejected' || l.status === 'pending_review') && (
                <div className="sell-dispute">
                  <textarea
                    rows="2"
                    placeholder="Dispute: describe your original pack for human review."
                    value={dispute[l.id] || ''}
                    onChange={(e) => setDispute((prev) => ({ ...prev, [l.id]: e.target.value }))}
                  />
                  <button type="button" className="mk-btn ghost sm" onClick={() => disputeListing(l.id)} disabled={Boolean(busy)}>
                    {busy === `claim-${l.id}` ? 'Sending…' : 'Queue human review'}
                  </button>
                </div>
              )}
            </div>
          );
        })
      )}

      <h2 className="sell-h2">Recent sales</h2>
      <div className="mk-card sell-table">
        {sales.length === 0 ? (
          <div className="mk-empty">No sales yet.</div>
        ) : sales.map((s) => {
          const net = s.amount * (1 - commissionRate(s.type));
          const tone = STATE_TONE[s.state] || 'info';
          const label = STATE_LABEL[s.state] || s.state;
          const delivering = busy === `del-${s.id}`;
          return (
            <div className="sale-row" key={s.id}>
              <span className="avatar sm">{s.counterparty?.avatar || '?'}</span>
              <div className="sale-main">
                <strong>{s.title}</strong>
                <span>{s.counterparty?.name || 'Buyer'} · {s.placedAt} · {s.id}</span>
              </div>
              <div className="sale-money">
                <b>{money(s.amount)}</b>
                <span>you net {money(net)}</span>
              </div>
              <span className={`mk-pill ${tone}`}>{label}</span>
              {s.state === 'funds_held' ? (
                <div className="sale-deliver">
                  <label className="sf-file sm">
                    <Icon name="upload" className="sm" />
                    {files[s.id]?.name || 'Upload pack'}
                    <input
                      type="file"
                      accept=".pdf,.docx,.md,.txt,.xml,.zip"
                      hidden
                      onChange={(e) => setFiles((prev) => ({ ...prev, [s.id]: e.target.files?.[0] }))}
                    />
                  </label>
                  <button type="button" className="mk-btn sm" onClick={() => deliver(s.id)} disabled={Boolean(busy) || !files[s.id]}>
                    {delivering ? 'Uploading…' : 'Mark delivered'}
                  </button>
                </div>
              ) : (
                <span className="sale-spacer" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
