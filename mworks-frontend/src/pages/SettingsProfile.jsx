import { useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { currentUser } from '../data/profile.js';
import './Settings.css';

const NOTIF_CATEGORIES = [
  { id: 'transactions', label: 'Transaction & escrow updates' },
  { id: 'verification', label: 'Verification results' },
  { id: 'disputes', label: 'Disputes' },
  { id: 'reviews', label: 'New reviews' },
  { id: 'jobs', label: 'Job Agent activity' },
  { id: 'product', label: 'Product news' },
];

function SavedFlash({ show }) {
  if (!show) return null;
  return <span className="settings-saved"><Icon name="check-circle" className="sm" /> Saved</span>;
}

export default function SettingsProfile() {
  const u = currentUser;

  const [profile, setProfile] = useState({
    name: u.name,
    headline: u.headline,
    location: u.location,
    skills: u.skills.join(', '),
    links: u.links.map((l) => l.url).join(', '),
  });
  const [roles, setRoles] = useState(new Set(u.roles));
  const [prefs, setPrefs] = useState(
    Object.fromEntries(NOTIF_CATEGORIES.map((c) => [c.id, { email: true, inApp: true }])),
  );
  const [savedProfile, setSavedProfile] = useState(false);
  const [savedPrefs, setSavedPrefs] = useState(false);

  const setP = (k) => (e) => { setProfile((x) => ({ ...x, [k]: e.target.value })); setSavedProfile(false); };
  const toggleRole = (r) => {
    setRoles((prev) => {
      const next = new Set(prev);
      if (next.has(r)) { if (next.size > 1) next.delete(r); }
      else next.add(r);
      return next;
    });
    setSavedProfile(false);
  };
  const togglePref = (cat, ch) => {
    setPrefs((x) => ({ ...x, [cat]: { ...x[cat], [ch]: !x[cat][ch] } }));
    setSavedPrefs(false);
  };

  const idVerified = u.identity.status === 'verified';

  return (
    <div className="mk-page mk-narrow">
      <div className="mk-head">
        <div>
          <h1>Profile &amp; settings</h1>
          <p className="sub">Manage your public profile, roles, identity, and notifications.</p>
        </div>
        <Link to={`/u/${u.handle}`} className="mk-btn ghost sm">View public profile</Link>
      </div>

      {/* Public profile */}
      <form className="mk-card settings-card" onSubmit={(e) => { e.preventDefault(); setSavedProfile(true); }}>
        <div className="settings-card-head">
          <div className="mk-sec-title">Public profile</div>
          <SavedFlash show={savedProfile} />
        </div>
        <div className="set-field">
          <label htmlFor="name">Display name</label>
          <input id="name" type="text" value={profile.name} onChange={setP('name')} />
        </div>
        <div className="set-field">
          <label htmlFor="headline">Headline</label>
          <input id="headline" type="text" value={profile.headline} onChange={setP('headline')} />
        </div>
        <div className="set-field">
          <label htmlFor="location">Location</label>
          <input id="location" type="text" value={profile.location} onChange={setP('location')} />
        </div>
        <div className="set-field">
          <label htmlFor="skills">Skills</label>
          <input id="skills" type="text" value={profile.skills} onChange={setP('skills')} placeholder="Comma separated" />
        </div>
        <div className="set-field">
          <label htmlFor="links">Links</label>
          <input id="links" type="text" value={profile.links} onChange={setP('links')} placeholder="Comma separated URLs" />
        </div>
        <button type="submit" className="mk-btn sm">Save profile</button>
      </form>

      {/* Roles */}
      <div className="mk-card settings-card">
        <div className="mk-sec-title">How you use Mworks</div>
        <p className="set-note">Switch roles anytime - your trust score, reviews, and transaction history carry across all of them.</p>
        <label className="set-toggle-row">
          <span><strong>Buy</strong><span>Discover and purchase automations and prompt packs</span></span>
          <button type="button" className={'set-switch' + (roles.has('buyer') ? ' on' : '')} onClick={() => toggleRole('buyer')} aria-pressed={roles.has('buyer')} />
        </label>
        <label className="set-toggle-row">
          <span><strong>Sell</strong><span>List your own automations and prompts for sale</span></span>
          <button type="button" className={'set-switch' + (roles.has('seller') ? ' on' : '')} onClick={() => toggleRole('seller')} aria-pressed={roles.has('seller')} />
        </label>
        <div className="set-links">
          <span className="set-link-muted">Post jobs as an employer - <em>available in a later release</em></span>
          <span className="set-link-muted">Register a training organisation - <em>available in a later release</em></span>
        </div>
      </div>

      {/* Identity */}
      <div className="mk-card settings-card">
        <div className="settings-card-head">
          <div className="mk-sec-title">Identity verification</div>
          <span className={'mk-pill ' + (idVerified ? 'ok' : 'warn')}>
            <Icon name="shield" className="sm" />
            {idVerified ? `Verified · ${u.identity.verifiedOn}` : 'Pending review'}
          </span>
        </div>
        <p className="set-note">
          Verified identity is required before you can transact. It also unlocks a reputation-points bonus and a badge on your public profile.
        </p>
        <div className="set-checks">
          {u.identity.checks.map((c) => (
            <div className="set-check" key={c.label}>
              <Icon name={c.status === 'done' ? 'check-circle' : 'clock'} className={'sm ' + c.status} />
              {c.label}
            </div>
          ))}
        </div>
        <button className="mk-btn ghost sm" disabled>Manage verification</button>
      </div>

      {/* Reputation */}
      <div className="mk-card settings-card">
        <div className="mk-sec-title">Reputation &amp; trust</div>
        <div className="set-rep">
          <div className="set-rep-tile"><b>{u.trustScore}</b><span>Trust score</span></div>
          <div className="set-rep-tile"><b>{u.points.toLocaleString('en-NG')}</b><span>Reputation points</span></div>
        </div>
        <div className="set-rep-break">
          {u.pointsBreakdown.map((b) => (
            <div className="set-rep-row" key={b.label}>
              <span>{b.label}</span>
              <span>+{b.value.toLocaleString('en-NG')}</span>
            </div>
          ))}
        </div>
        <p className="set-note">
          <Icon name="lock" className="sm" />
          Reputation points are non-redeemable and non-transferable - they signal trust, they are not a currency.
        </p>
      </div>

      {/* Notification preferences */}
      <div className="mk-card settings-card">
        <div className="settings-card-head">
          <div className="mk-sec-title">Notification preferences</div>
          <SavedFlash show={savedPrefs} />
        </div>
        <div className="set-pref-head">
          <span>Category</span>
          <span className="set-pref-cols"><span><Icon name="mail" className="sm" /> Email</span><span><Icon name="bell" className="sm" /> In-app</span></span>
        </div>
        {NOTIF_CATEGORIES.map((c) => (
          <div className="set-pref-row" key={c.id}>
            <span>{c.label}</span>
            <span className="set-pref-cols">
              <input type="checkbox" checked={prefs[c.id].email} onChange={() => togglePref(c.id, 'email')} />
              <input type="checkbox" checked={prefs[c.id].inApp} onChange={() => togglePref(c.id, 'inApp')} />
            </span>
          </div>
        ))}
        <button className="mk-btn sm" onClick={() => setSavedPrefs(true)}>Save preferences</button>
      </div>
    </div>
  );
}
