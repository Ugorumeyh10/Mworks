import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import JobsTabs from '../components/JobsTabs.jsx';
import { TRACKS, JOB_TYPES } from '../data/jobs.js';
import { fetchJobs } from '../api/jobs.js';
import './Jobs.css';

export default function JobBoard() {
  const [track, setTrack] = useState('All');
  const [type, setType] = useState('All');
  const [minTrust, setMinTrust] = useState(0);
  const [q, setQ] = useState('');
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    let live = true;
    fetchJobs({
      track: track === 'All' ? undefined : track,
      type: type === 'All' ? undefined : type,
      q: q.trim() || undefined,
      min_trust: minTrust || undefined,
    }).then((rows) => {
      if (live) setJobs(rows);
    }).catch(() => {
      if (live) setJobs([]);
    });
    return () => { live = false; };
  }, [track, type, minTrust, q]);

  const results = useMemo(() => jobs, [jobs]);

  return (
    <div className="mk-page">
      <JobsTabs />

      <div className="mk-head">
        <div>
          <h1>Job board</h1>
          <p className="sub">RPA and AI roles from verified employers plus a live ingest bot that watches public career boards. Apply with your Mworks profile - your trust score travels with the application.</p>
        </div>
      </div>

      <div className="jb-filters">
        <div className="jb-search">
          <Icon name="search" className="sm" />
          <input placeholder="Search title, company, skill…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="mk-seg">
          {['All', ...JOB_TYPES].map((t) => (
            <button key={t} className={type === t ? 'on' : ''} onClick={() => setType(t)}>{t}</button>
          ))}
        </div>
      </div>

      <div className="jb-chiprow">
        {['All', ...TRACKS].map((t) => (
          <button key={t} className={'chip' + (track === t ? ' on' : '')} onClick={() => setTrack(t)}>{t}</button>
        ))}
        <span className="jb-chiprow-sep" />
        {[0, 70, 80, 85].map((v) => (
          <button key={v} className={'chip' + (minTrust === v ? ' on' : '')} onClick={() => setMinTrust(v)}>
            {v === 0 ? 'Any trust' : `Trust ${v}+`}
          </button>
        ))}
      </div>

      <div className="jb-count">{results.length} open role{results.length === 1 ? '' : 's'}</div>

      {results.length === 0 ? (
        <div className="mk-empty">No roles match these filters.</div>
      ) : (
        <div className="jb-list">
          {results.map((j) => (
            <Link to={`/jobs/board/${j.id}`} className="mk-card jb-card" key={j.id}>
              <span className="avatar org jb-logo">{j.companyAvatar}</span>
              <div className="jb-main">
                <div className="jb-title-row">
                  <strong>{j.title}</strong>
                  <span className="mk-pill info">{j.type}</span>
                </div>
                <div className="jb-company">
                  {j.company}
                  {j.verifiedEmployer && <span className="jb-verified"><Icon name="check-circle" className="sm" /> Verified employer</span>}
                  {j.source && <span className="mk-pill">Sourced</span>}
                </div>
                <div className="jb-meta">
                  <span><Icon name="pin" className="sm" /> {j.location}</span>
                  <span><Icon name="wallet" className="sm" /> {j.salary}</span>
                </div>
                <div className="jb-skills">
                  {j.skills.map((s) => <span className="chip" key={s}>{s}</span>)}
                </div>
              </div>
              <div className="jb-side">
                <span className="mk-pill">{j.minTrust}+ trust</span>
                <span className="jb-applicants">{j.applicants} applied</span>
                <span className="jb-posted">{j.posted}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
