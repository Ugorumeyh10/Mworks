import { useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import JobsTabs from '../components/JobsTabs.jsx';
import { talentPool, trainingPartners, TRACKS, ALL_SKILLS } from '../data/jobs.js';
import './Talent.css';

export default function Talent() {
  const [params, setParams] = useSearchParams();
  const partnerParam = params.get('partner');
  const initialSource = partnerParam
    ? trainingPartners.find((p) => p.id === partnerParam)?.name || 'All'
    : 'All';

  const [source, setSource] = useState(initialSource);
  const [track, setTrack] = useState('All');
  const [skill, setSkill] = useState('All');
  const [minTrust, setMinTrust] = useState(80);
  const [openOnly, setOpenOnly] = useState(false);

  const SOURCES = ['All', 'Marketplace', ...trainingPartners.map((p) => p.name)];

  const results = useMemo(
    () =>
      talentPool.filter((t) => {
        if (source !== 'All' && t.source !== source) return false;
        if (track !== 'All' && t.track !== track) return false;
        if (skill !== 'All' && !t.skills.includes(skill)) return false;
        if (t.trustScore < minTrust) return false;
        if (openOnly && !t.openToWork) return false;
        return true;
      }),
    [source, track, skill, minTrust, openOnly],
  );

  const setSourceAndUrl = (s) => {
    setSource(s);
    const partner = trainingPartners.find((p) => p.name === s);
    if (partner) setParams({ partner: partner.id });
    else setParams({});
  };

  return (
    <div className="mk-page">
      <JobsTabs />

      <div className="mk-head">
        <div>
          <h1>Talent search</h1>
          <p className="sub">Filter marketplace practitioners and showcased graduates by training provider, skill, and trust score. Every profile carries a marketplace-earned trust score - not a self-reported CV.</p>
        </div>
      </div>

      <div className="tl-filters">
        <div className="tl-filter">
          <span className="tl-label">Source</span>
          <div className="tl-chips">
            {SOURCES.map((s) => (
              <button key={s} className={'chip' + (source === s ? ' on' : '')} onClick={() => setSourceAndUrl(s)}>{s}</button>
            ))}
          </div>
        </div>
        <div className="tl-filter">
          <span className="tl-label">Track</span>
          <div className="tl-chips">
            {['All', ...TRACKS].map((t) => (
              <button key={t} className={'chip' + (track === t ? ' on' : '')} onClick={() => setTrack(t)}>{t}</button>
            ))}
          </div>
        </div>
        <div className="tl-filter">
          <span className="tl-label">Skill</span>
          <select value={skill} onChange={(e) => setSkill(e.target.value)} className="tl-select">
            <option value="All">Any skill</option>
            {ALL_SKILLS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div className="tl-filter">
          <span className="tl-label">Minimum trust score - <b>{minTrust}</b></span>
          <input type="range" min="0" max="95" step="5" value={minTrust} onChange={(e) => setMinTrust(Number(e.target.value))} className="tl-range" />
        </div>
        <label className="tl-open">
          <input type="checkbox" checked={openOnly} onChange={(e) => setOpenOnly(e.target.checked)} />
          Open to work only
        </label>
      </div>

      <div className="tl-count">{results.length} {results.length === 1 ? 'person' : 'people'}</div>

      {results.length === 0 ? (
        <div className="mk-empty">No one matches these filters. Try lowering the trust score.</div>
      ) : (
        <div className="tl-grid">
          {results.map((t) => (
            <div className="mk-card tl-card" key={t.handle}>
              <div className="tl-card-top">
                <span className="avatar tl-avatar">{t.avatar}</span>
                <div>
                  <Link to={`/u/${t.handle}`} className="tl-name">{t.name}</Link>
                  <div className="tl-track">{t.track}</div>
                </div>
                {t.openToWork && <span className="mk-pill ok">Open to work</span>}
              </div>
              <div className="tl-stats">
                <span><b>{t.trustScore}</b> trust</span>
                <span><b>{t.projects}</b> projects</span>
                <span><Icon name="star" className="sm" /> {t.rating.toFixed(1)}</span>
              </div>
              <div className="tl-source">
                <Icon name={t.source === 'Marketplace' ? 'tag' : 'cap'} className="sm" />
                {t.source}
              </div>
              <div className="tl-skills">
                {t.skills.slice(0, 3).map((s) => <span className="chip" key={s}>{s}</span>)}
              </div>
              <div className="tl-actions">
                <Link to={`/u/${t.handle}`} className="mk-btn ghost sm">View profile</Link>
                <Link to="/messages" className="mk-btn sm">Message</Link>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="tl-partners-cta">
        <div>
          <strong>Hiring from a cohort?</strong>
          <span>Browse accredited training partners and their showcased graduates.</span>
        </div>
        <div className="tl-partners-links">
          {trainingPartners.map((p) => (
            <Link key={p.id} to={`/partners/${p.id}`} className="mk-btn ghost sm">{p.name}</Link>
          ))}
        </div>
      </div>
    </div>
  );
}
