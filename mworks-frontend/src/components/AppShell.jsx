import { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import Icon from './Icon.jsx';
import BrandMark from './BrandMark.jsx';
import { unreadCount } from '../data/notifications.js';
import { getUser } from '../api/session.js';
import './AppShell.css';

const NAV_GROUPS = [
  {
    label: 'Marketplace',
    items: [
      { to: '/discover', label: 'Discover', icon: 'home', end: true },
      { to: '/browse', label: 'Browse', icon: 'search' },
      { to: '/blog', label: 'Blog', icon: 'book', end: true },
      { to: '/sell', label: 'Sell', icon: 'tag' },
    ],
  },
  {
    label: 'Work',
    items: [
      { to: '/jobs', label: 'Jobs', icon: 'briefcase' },
      { to: '/interviewer', label: 'Interviewer', icon: 'users' },
    ],
  },
  {
    label: 'Inbox',
    items: [
      { to: '/orders', label: 'Orders', icon: 'bag' },
      { to: '/messages', label: 'Messages', icon: 'message' },
    ],
  },
];
const BOTTOM_ITEMS = [
  { to: '/discover', icon: 'home', end: true },
  { to: '/browse', icon: 'search' },
  { to: '/jobs', icon: 'briefcase' },
  { to: '/orders', icon: 'bag' },
  { to: '/messages', icon: 'message' },
];

export default function AppShell() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const unread = unreadCount();
  const user = getUser();
  const displayName = user?.name || 'Guest';
  const avatar = (displayName.trim()[0] || 'G').toUpperCase();
  const roleLabel = user?.role === 'seller' ? 'Seller' : user?.role === 'both' ? 'Seller · Buyer' : user ? 'Buyer' : 'Sign in';

  const search = (e) => {
    e.preventDefault();
    navigate(query.trim() ? `/browse?q=${encodeURIComponent(query.trim())}` : '/browse');
  };

  return (
    <div className="shell">
      <aside className="sidebar">
        <Link to="/" className="brand">
          <BrandMark size={32} withWord />
        </Link>
        <nav className="side-nav">
          {NAV_GROUPS.map((group) => (
            <div className="side-group" key={group.label}>
              <span className="side-group-label">{group.label}</span>
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => 'side-link' + (isActive ? ' active' : '')}
                >
                  <Icon name={item.icon} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
          {user?.isAdmin && (
            <div className="side-group">
              <span className="side-group-label">Admin</span>
              <NavLink to="/blog/newsroom" className={({ isActive }) => 'side-link' + (isActive ? ' active' : '')}>
                <Icon name="book" />
                <span>Newsroom</span>
              </NavLink>
              <NavLink to="/sell/claims" className={({ isActive }) => 'side-link' + (isActive ? ' active' : '')}>
                <Icon name="shield" />
                <span>Trust review</span>
              </NavLink>
            </div>
          )}
        </nav>
        {user ? (
          <Link to="/settings/profile" className="side-footer">
            <div className="avatar">{avatar}</div>
            <div className="side-footer-text">
              <strong>{displayName}</strong>
              <span>{roleLabel}</span>
            </div>
          </Link>
        ) : (
          <Link to="/login" className="side-footer">
            <div className="avatar">?</div>
            <div className="side-footer-text">
              <strong>Sign in</strong>
              <span>Buyer · Seller</span>
            </div>
          </Link>
        )}
      </aside>

      <div className="main-col">
        <header className="topbar-desktop">
          <form className="search-box" onSubmit={search}>
            <Icon name="search" className="sm" />
            <input
              placeholder="Search automations, prompts, jobs..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </form>
          <div className="topbar-actions">
            <NavLink
              to="/assistant"
              className={({ isActive }) => 'icon-btn' + (isActive ? ' active' : '')}
              aria-label="Assistant"
              title="Assistant"
            >
              <Icon name="bot" />
            </NavLink>
            <NavLink
              to="/notifications"
              className={({ isActive }) => 'icon-btn' + (isActive ? ' active' : '')}
              aria-label={`Notifications${unread ? `, ${unread} unread` : ''}`}
            >
              <Icon name="bell" />
              {unread > 0 && <span className="icon-badge">{unread}</span>}
            </NavLink>
            <NavLink
              to="/settings/profile"
              className={({ isActive }) => 'icon-btn' + (isActive ? ' active' : '')}
              aria-label="Settings"
            >
              <Icon name="settings" />
            </NavLink>
          </div>
        </header>

        <main className="content">
          <Outlet />
        </main>
      </div>

      <nav className="bottom-nav">
        {BOTTOM_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => 'bottom-link' + (isActive ? ' active' : '')}
          >
            <Icon name={item.icon} />
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
