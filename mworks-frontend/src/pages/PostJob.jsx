import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { TRACKS, JOB_TYPES } from '../data/jobs.js';
import { createJob } from '../api/jobs.js';
import { apiEnabled } from '../api/client.js';
import { getToken } from '../api/session.js';
import './Jobs.css';

export default function PostJob() {
  const navigate = useNavigate();
  const [f, setF] = useState({
    title: '', track: '', type: 'Full-time', location: '',
    salaryMin: '', salaryMax: '', competitive: false,
    skills: '', minTrust: 75, description: '', responsibilities: '',
    successFee: true,
  });
  const [errors, setErrors] = useState({});
  const [posted, setPosted] = useState(null);
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setF((x) => ({ ...x, [k]: v }));
    setErrors((x) => ({ ...x, [k]: undefined }));
  };

  const submit = async (e) => {
    e.preventDefault();
    const next = {};
    if (f.title.trim().length < 6) next.title = 'Give the role a clear title.';
    if (!f.track) next.track = 'Pick a track.';
    if (f.location.trim().length < 2) next.location = 'Add a location or “Remote”.';
    if (!f.competitive && !(parseFloat(f.salaryMin) > 0)) next.salaryMin = 'Add a salary, or mark it competitive.';
    if (f.description.trim().length < 40) next.description = 'Describe the role in a bit more detail.';
    setErrors(next);
    if (Object.keys(next).length) return;
    if (!getToken()) {
      navigate('/login?next=/jobs/post');
      return;
    }
    if (!apiEnabled()) {
      setPosted({ title: f.title, id: null });
      return;
    }
    setBusy(true);
    try {
      const row = await createJob({
        title: f.title.trim(),
        track: f.track,
        type: f.type,
        location: f.location.trim(),
        salary_min: f.competitive ? null : Number(f.salaryMin),
        salary_max: f.competitive || !f.salaryMax ? null : Number(f.salaryMax),
        competitive: f.competitive,
        skills: f.skills.split(',').map((s) => s.trim()).filter(Boolean),
        min_trust: Number(f.minTrust),
        description: f.description.trim(),
        responsibilities: f.responsibilities.split('\n').map((s) => s.trim()).filter(Boolean),
        success_fee: f.successFee,
      });
      setPosted(row);
    } catch (err) {
      setErrors({ description: err.message || 'Could not post this role.' });
    } finally {
      setBusy(false);
    }
  };

  if (posted) {
    return (
      <div className="mk-page mk-narrow">
        <div className="jd-applied">
          <span className="jd-applied-icon"><Icon name="check-circle" /></span>
          <h2>{posted.status === 'live' ? 'Role is live' : 'Posted for review'}</h2>
          <p>
            <strong>{posted.title || f.title}</strong>
            {posted.status === 'live'
              ? ' is on the job board. Applicants arrive with a verified trust score.'
              : ' will go live once your employer account is verified.'}
          </p>
          <div className="jd-applied-actions">
            <Link to={posted.id ? `/jobs/board/${posted.id}` : '/jobs/board'} className="mk-btn">View role</Link>
            <button className="mk-btn ghost" onClick={() => { setPosted(null); setF((x) => ({ ...x, title: '', description: '', responsibilities: '' })); }}>
              Post another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mk-page mk-narrow">
      <Link to="/jobs/board" className="mk-back"><Icon name="arrow-left" className="sm" /> Job board</Link>
      <div className="mk-head">
        <div>
          <h1>Post a job</h1>
          <p className="sub">Reach vetted RPA and AI practitioners. Applicants arrive with a verified trust score and marketplace history.</p>
        </div>
      </div>

      <div className="mk-card pj-fees">
        <Icon name="card" className="sm" />
        <div>
          <b>₦15,000</b> flat listing fee per role, charged on publish.
          <label className="pj-fee-opt">
            <input type="checkbox" checked={f.successFee} onChange={set('successFee')} />
            Add an optional 5% success fee if you hire through Mworks (recommended - boosts ranking)
          </label>
        </div>
      </div>

      <form className="pj-form" onSubmit={submit} noValidate>
        <div className={'pj-field' + (errors.title ? ' bad' : '')}>
          <label htmlFor="title">Role title</label>
          <input id="title" type="text" value={f.title} onChange={set('title')} placeholder="e.g. RPA Developer - Fintech Ops" />
          {errors.title && <span className="pj-err">{errors.title}</span>}
        </div>

        <div className="pj-two">
          <div className={'pj-field' + (errors.track ? ' bad' : '')}>
            <label htmlFor="track">Track</label>
            <select id="track" value={f.track} onChange={set('track')}>
              <option value="">Select…</option>
              {TRACKS.map((t) => <option key={t}>{t}</option>)}
            </select>
            {errors.track && <span className="pj-err">{errors.track}</span>}
          </div>
          <div className="pj-field">
            <label>Employment type</label>
            <div className="mk-seg">
              {JOB_TYPES.map((t) => (
                <button type="button" key={t} className={f.type === t ? 'on' : ''} onClick={() => setF((x) => ({ ...x, type: t }))}>{t}</button>
              ))}
            </div>
          </div>
        </div>

        <div className={'pj-field' + (errors.location ? ' bad' : '')}>
          <label htmlFor="location">Location</label>
          <input id="location" type="text" value={f.location} onChange={set('location')} placeholder="e.g. Lagos, NG · Hybrid  /  Remote (Nigeria)" />
          {errors.location && <span className="pj-err">{errors.location}</span>}
        </div>

        <div className="pj-field">
          <label>Compensation (₦ / month)</label>
          <div className="pj-salary">
            <input type="number" min="0" placeholder="Min" value={f.salaryMin} onChange={set('salaryMin')} disabled={f.competitive} />
            <span>–</span>
            <input type="number" min="0" placeholder="Max" value={f.salaryMax} onChange={set('salaryMax')} disabled={f.competitive} />
            <label className="pj-competitive">
              <input type="checkbox" checked={f.competitive} onChange={set('competitive')} /> Competitive
            </label>
          </div>
          {errors.salaryMin && <span className="pj-err">{errors.salaryMin}</span>}
        </div>

        <div className="pj-field">
          <label htmlFor="skills">Required skills</label>
          <input id="skills" type="text" value={f.skills} onChange={set('skills')} placeholder="Comma separated, e.g. Power Automate, SQL, Reconciliation" />
        </div>

        <div className="pj-field">
          <label htmlFor="minTrust">Minimum trust score - <b>{f.minTrust}</b></label>
          <input id="minTrust" type="range" min="0" max="95" step="5" value={f.minTrust} onChange={set('minTrust')} className="pj-range" />
          <span className="pj-hint">Applicants below this still see the role, but are flagged to you. It never blocks applications.</span>
        </div>

        <div className={'pj-field' + (errors.description ? ' bad' : '')}>
          <label htmlFor="description">Description</label>
          <textarea id="description" rows="4" value={f.description} onChange={set('description')} placeholder="What the person will own and who they work with." />
          {errors.description && <span className="pj-err">{errors.description}</span>}
        </div>

        <div className="pj-field">
          <label htmlFor="responsibilities">Responsibilities</label>
          <textarea id="responsibilities" rows="4" value={f.responsibilities} onChange={set('responsibilities')} placeholder="One per line" />
        </div>

        <p className="pj-note">
          <Icon name="shield" className="sm" />
          Employer accounts are verified before any posting goes live - this keeps scam recruiters off the board.
        </p>

        <div className="pj-submit">
          <button type="submit" className="mk-btn" disabled={busy}>{busy ? 'Submitting…' : 'Submit role'}</button>
          <Link to="/jobs/board" className="mk-btn ghost">Cancel</Link>
        </div>
      </form>
    </div>
  );
}
