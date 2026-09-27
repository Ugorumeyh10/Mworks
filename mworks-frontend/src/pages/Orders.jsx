import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { money, STATE_LABEL, STATE_TONE } from '../data/marketplace.js';
import { fetchOrders } from '../api/orders.js';
import { getToken } from '../api/session.js';
import './Orders.css';

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'pending_payment', label: 'Awaiting payment' },
  { id: 'funds_held', label: 'In escrow' },
  { id: 'delivered', label: 'To confirm' },
  { id: 'completed', label: 'Completed' },
  { id: 'disputed', label: 'Disputed' },
  { id: 'hire', label: 'Hires' },
];

export default function Orders() {
  const [filter, setFilter] = useState('all');
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const authed = Boolean(getToken());

  useEffect(() => {
    if (!authed) return undefined;
    let live = true;
    fetchOrders('buying')
      .then((data) => {
        if (live) setRows(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        if (live) setError(err.message || 'Could not load orders.');
      });
    return () => {
      live = false;
    };
  }, [authed]);

  if (!authed) {
    return (
      <div className="mk-page">
        <h1>My orders</h1>
        <div className="mk-empty">
          <Link to="/login?next=/orders">Sign in</Link> to see purchases held in escrow.
        </div>
      </div>
    );
  }

  const visible = rows.filter((o) => {
    if (filter === 'all') return true;
    if (filter === 'hire') return o.kind === 'hire';
    return o.state === filter;
  });

  return (
    <div className="mk-page">
      <div className="mk-head">
        <div>
          <h1>My orders</h1>
          <p className="sub">Purchases and customization hires. Funds stay in escrow until you confirm.</p>
        </div>
        <Link to="/browse" className="mk-btn ghost sm">Browse marketplace</Link>
      </div>

      <div className="ord-filters">
        {FILTERS.map((f) => (
          <button key={f.id} className={'chip' + (filter === f.id ? ' on' : '')} onClick={() => setFilter(f.id)}>
            {f.label}
          </button>
        ))}
      </div>

      {error && <div className="mk-empty">{error}</div>}

      {!error && visible.length === 0 ? (
        <div className="mk-empty">Nothing here yet.</div>
      ) : (
        <div className="mk-card ord-list">
          {visible.map((o) => (
            <Link to={`/orders/${o.id}`} className="ord-row" key={o.id}>
              <span className="avatar sm">{o.counterparty?.avatar || '?'}</span>
              <div className="ord-main">
                <strong>{o.title}</strong>
                <span>
                  {o.kind === 'revise' ? 'Revise' : o.kind === 'hire' ? 'Hire' : 'Purchase'}
                  {' · '}{o.counterparty?.name || 'Seller'}
                  {' · '}{o.placedAt} · {o.id}
                </span>
              </div>
              <span className="ord-amount">{money(o.amount)}</span>
              <span className={`mk-pill ${STATE_TONE[o.state] || 'info'}`}>{STATE_LABEL[o.state] || o.state}</span>
              <Icon name="chevron-right" className="sm ord-chev" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
