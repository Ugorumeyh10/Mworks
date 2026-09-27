import { Link, NavLink } from 'react-router-dom';
import Icon from './Icon.jsx';
import './JobsTabs.css';

const TABS = [
  { to: '/jobs/board', label: 'Job board', end: false },
  { to: '/jobs', label: 'Job Agent', end: true },
  { to: '/jobs/applications', label: 'My applications', end: true },
];

export default function JobsTabs() {
  return (
    <div className="jt">
      <nav className="jt-tabs">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            end={t.end}
            className={({ isActive }) => 'jt-tab' + (isActive ? ' on' : '')}
          >
            {t.label}
          </NavLink>
        ))}
      </nav>
      <div className="jt-actions">
        <Link to="/talent" className="mk-btn ghost sm"><Icon name="users" className="sm" /> Find talent</Link>
        <Link to="/jobs/post" className="mk-btn sm"><Icon name="plus" className="sm" /> Post a job</Link>
      </div>
    </div>
  );
}
