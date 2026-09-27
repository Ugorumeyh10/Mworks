import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchTheftClaims, resolveTheftClaim } from '../api/listings.js';
import { getToken, getUser } from '../api/session.js';
import './Sell.css';

export default function TrustClaims() {
  const user = getUser();
  const authed = Boolean(getToken());
  const [rows, setRows] = useState([]);
  const [notes, setNotes] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');

  const load = () => {
    fetchTheftClaims().then(setRows).catch((err) => {
      setRows([]);
      setError(err.message || 'Could not load claims.');
    });
  };

  useEffect(() => {
    if (!authed || !user?.isAdmin) return undefined;
    load();
    return undefined;
  }, [authed, user?.isAdmin]);

  if (!authed || !user?.isAdmin) {
    return (
      <div className="mk-page">
        <h1>Theft review</h1>
        <div className="mk-empty">Admin access is required.</div>
      </div>
    );
  }

  const decide = async (id, status) => {
    const resolution = (notes[id] || '').trim();
    if (resolution.length < 8) {
      setError('Write a short resolution note.');
      return;
    }
    setError('');
    setBusy(`${status}-${id}`);
    try {
      await resolveTheftClaim(id, { status, resolution });
      load();
    } catch (err) {
      setError(err.message || 'Could not resolve that claim.');
    } finally {
      setBusy('');
    }
  };

  return (
    <div className="mk-page">
      <div className="mk-head">
        <div>
          <h1>Theft review</h1>
          <p className="sub">Human review only. Upholding a claim rejects the listing. Rejecting a claim can restore a pending-review listing.</p>
        </div>
        <Link to="/sell" className="mk-btn ghost">Seller workspace</Link>
      </div>
      {error && <p className="sf-err" role="alert">{error}</p>}
      {rows.length === 0 ? (
        <div className="mk-empty">No claims in the queue.</div>
      ) : rows.map((row) => (
        <div className="mk-card sell-listing" key={row.id}>
          <div className="sell-listing-title">
            {row.listingTitle}
            <span className={`mk-pill ${row.status === 'open' ? 'warn' : row.status === 'upheld' ? 'bad' : 'ok'}`}>{row.status}</span>
          </div>
          <p className="body-text">{row.reason}</p>
          {row.resolution && <p className="pj-hint">Resolution: {row.resolution}</p>}
          {row.status === 'open' && (
            <div className="sell-dispute">
              <textarea
                rows="2"
                placeholder="Resolution note for the audit log."
                value={notes[row.id] || ''}
                onChange={(e) => setNotes((prev) => ({ ...prev, [row.id]: e.target.value }))}
              />
              <button type="button" className="mk-btn sm" disabled={Boolean(busy)} onClick={() => decide(row.id, 'upheld')}>
                Uphold (takedown)
              </button>
              <button type="button" className="mk-btn ghost sm" disabled={Boolean(busy)} onClick={() => decide(row.id, 'rejected')}>
                Reject claim
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
