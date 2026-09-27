import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { notifications as seed } from '../data/notifications.js';
import './Notifications.css';

const TYPE_ICON = {
  transaction: 'bag',
  verification: 'shield',
  dispute: 'x',
  review: 'star',
  job: 'briefcase',
  system: 'bell',
};
const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'unread', label: 'Unread' },
  { id: 'transaction', label: 'Transactions' },
  { id: 'verification', label: 'Verification' },
  { id: 'dispute', label: 'Disputes' },
];
const BUCKETS = [
  ['today', 'Today'],
  ['week', 'This week'],
  ['earlier', 'Earlier'],
];

export default function Notifications() {
  const [items, setItems] = useState(seed);
  const [filter, setFilter] = useState('all');

  const unread = items.filter((n) => !n.read).length;

  const markAll = () => setItems((xs) => xs.map((n) => ({ ...n, read: true })));
  const markRead = (id) => setItems((xs) => xs.map((n) => (n.id === id ? { ...n, read: true } : n)));

  const visible = useMemo(
    () =>
      items.filter((n) => {
        if (filter === 'all') return true;
        if (filter === 'unread') return !n.read;
        return n.type === filter;
      }),
    [items, filter],
  );

  return (
    <div className="mk-page mk-narrow">
      <div className="mk-head">
        <div>
          <h1>Notifications</h1>
          <p className="sub">{unread ? `${unread} unread` : 'You’re all caught up.'}</p>
        </div>
        <button className="mk-btn ghost sm" onClick={markAll} disabled={!unread}>Mark all read</button>
      </div>

      <div className="nt-filters">
        {FILTERS.map((f) => (
          <button key={f.id} className={'chip' + (filter === f.id ? ' on' : '')} onClick={() => setFilter(f.id)}>
            {f.label}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <div className="mk-empty">Nothing here.</div>
      ) : (
        BUCKETS.map(([key, label]) => {
          const rows = visible.filter((n) => n.bucket === key);
          if (rows.length === 0) return null;
          return (
            <div className="nt-group" key={key}>
              <div className="nt-group-label">{label}</div>
              <div className="mk-card nt-list">
                {rows.map((n) => (
                  <Link
                    to={n.href}
                    key={n.id}
                    className={'nt-row' + (n.read ? '' : ' unread')}
                    onClick={() => markRead(n.id)}
                  >
                    <span className={`nt-icon ${n.type}`}><Icon name={TYPE_ICON[n.type]} className="sm" /></span>
                    <div className="nt-body">
                      <div className="nt-title">{n.title}</div>
                      <div className="nt-text">{n.body}</div>
                      <div className="nt-time">{n.time}</div>
                    </div>
                    {!n.read && <span className="nt-dot" />}
                  </Link>
                ))}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
