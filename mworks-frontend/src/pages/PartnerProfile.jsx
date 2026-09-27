import { Link, useParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { getPartner } from '../data/jobs.js';
import './Partners.css';

export default function PartnerProfile() {
  const { id } = useParams();
  const p = getPartner(id);

  if (!p) {
    return (
      <div className="mk-page mk-narrow">
        <Link to="/talent" className="mk-back"><Icon name="arrow-left" className="sm" /> Talent</Link>
        <div className="mk-empty">No training partner found.</div>
      </div>
    );
  }

  const hired = p.students.filter((s) => s.hired).length;

  return (
    <div className="mk-page">
      <Link to="/talent" className="mk-back"><Icon name="arrow-left" className="sm" /> Talent</Link>

      <div className="mk-card pt-header">
        <span className="avatar org pt-logo">{p.avatar}</span>
        <div className="pt-id">
          <div className="pt-name-row">
            <h1>{p.name}</h1>
            {p.accredited && <span className="mk-pill ok"><Icon name="cap" className="sm" /> Accredited training partner</span>}
          </div>
          <div className="pt-meta">
            <span>{p.type}</span>
            <span><Icon name="pin" className="sm" /> {p.location}</span>
            <span><Icon name="users" className="sm" /> {p.cohorts} cohorts</span>
          </div>
          <p className="pt-blurb">{p.blurb}</p>
        </div>
      </div>

      <div className="mk-tiles pt-tiles">
        <div className="mk-tile"><b>{p.students.length}</b><span>Showcased graduates</span></div>
        <div className="mk-tile"><b>{hired}</b><span>Hired via Mworks</span></div>
        <div className="mk-tile"><b>{Math.round(p.students.reduce((n, s) => n + s.trustScore, 0) / p.students.length)}</b><span>Avg. trust score</span></div>
      </div>

      <div className="pt-showcase-head">
        <h2>Showcased graduates</h2>
        <Link to={`/talent?partner=${p.id}`} className="mk-btn ghost sm">Filter all talent from {p.name}</Link>
      </div>

      <div className="pt-students">
        {p.students.map((s) => (
          <div className="mk-card pt-student" key={s.handle}>
            <div className="pt-student-top">
              <span className="avatar pt-student-avatar">{s.avatar}</span>
              <div>
                <Link to={`/u/${s.handle}`} className="pt-student-name">{s.name}</Link>
                <div className="pt-student-track">{s.track}</div>
              </div>
              {s.hired && <span className="mk-pill info">Hired</span>}
            </div>
            <div className="pt-student-stats">
              <span><b>{s.trustScore}</b> trust</span>
              <span><b>{s.projects}</b> marketplace projects</span>
              <span><Icon name="star" className="sm" /> {s.rating.toFixed(1)}</span>
            </div>
            <Link to={`/u/${s.handle}`} className="mk-btn ghost sm">View verified profile</Link>
          </div>
        ))}
      </div>

      <div className="pt-apply-cta">
        <div>
          <strong>Run a training programme?</strong>
          <span>Showcase your top graduates against their verified marketplace record.</span>
        </div>
        <Link to="/partners/apply" className="mk-btn sm">Become a training partner</Link>
      </div>
    </div>
  );
}
