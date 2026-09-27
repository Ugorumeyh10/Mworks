import { useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import './Partners.css';

const ORG_TYPES = ['Bootcamp', 'Academy', 'Corporate training arm', 'University programme'];

export default function PartnerApply() {
  const [f, setF] = useState({
    org: '', type: 'Bootcamp', accreditation: '', location: '',
    website: '', focus: '', gradsPerYear: '', contact: '', attest: false,
  });
  const [errors, setErrors] = useState({});
  const [done, setDone] = useState(false);

  const set = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setF((x) => ({ ...x, [k]: v }));
    setErrors((x) => ({ ...x, [k]: undefined }));
  };

  const submit = (e) => {
    e.preventDefault();
    const next = {};
    if (f.org.trim().length < 2) next.org = 'Enter your organisation name.';
    if (f.location.trim().length < 2) next.location = 'Add a location.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.contact)) next.contact = 'Enter a valid contact email.';
    if (!f.attest) next.attest = 'You must confirm this to apply.';
    setErrors(next);
    if (Object.keys(next).length === 0) setDone(true);
  };

  if (done) {
    return (
      <div className="mk-page mk-narrow">
        <div className="jd-applied">
          <span className="jd-applied-icon"><Icon name="cap" /></span>
          <h2>Application received</h2>
          <p>
            We’ll verify <strong>{f.org}</strong>’s accreditation and get back to {f.contact} within a few business days.
            Once approved you can create an organisation profile and add graduates - each linked to their verified marketplace record.
          </p>
          <div className="jd-applied-actions">
            <Link to="/talent" className="mk-btn">Browse talent</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mk-page mk-narrow">
      <Link to="/talent" className="mk-back"><Icon name="arrow-left" className="sm" /> Talent</Link>
      <div className="mk-head">
        <div>
          <h1>Become a training partner</h1>
          <p className="sub">Accredited bootcamps, academies, and corporate training arms can showcase top graduates against their verified marketplace record.</p>
        </div>
      </div>

      <div className="mk-card pa-note">
        <Icon name="shield" className="sm" />
        <div>
          Showcased students must carry a genuine, marketplace-earned trust score - not your say-so. Organisation accreditation is verified before your profile goes live.
          A partner subscription covers the organisation profile and showcase page; an optional placement fee applies only if a showcased student is hired through a Mworks job.
        </div>
      </div>

      <form className="pj-form" onSubmit={submit} noValidate>
        <div className={'pj-field' + (errors.org ? ' bad' : '')}>
          <label htmlFor="org">Organisation name</label>
          <input id="org" type="text" value={f.org} onChange={set('org')} />
          {errors.org && <span className="pj-err">{errors.org}</span>}
        </div>

        <div className="pj-two">
          <div className="pj-field">
            <label htmlFor="type">Type</label>
            <select id="type" value={f.type} onChange={set('type')}>
              {ORG_TYPES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div className={'pj-field' + (errors.location ? ' bad' : '')}>
            <label htmlFor="location">Location</label>
            <input id="location" type="text" value={f.location} onChange={set('location')} placeholder="City, country" />
            {errors.location && <span className="pj-err">{errors.location}</span>}
          </div>
        </div>

        <div className="pj-two">
          <div className="pj-field">
            <label htmlFor="accreditation">Accreditation body</label>
            <input id="accreditation" type="text" value={f.accreditation} onChange={set('accreditation')} placeholder="e.g. NUC, NBTE, industry body" />
          </div>
          <div className="pj-field">
            <label htmlFor="website">Website</label>
            <input id="website" type="text" value={f.website} onChange={set('website')} placeholder="yourschool.com" />
          </div>
        </div>

        <div className="pj-two">
          <div className="pj-field">
            <label htmlFor="focus">Focus areas</label>
            <input id="focus" type="text" value={f.focus} onChange={set('focus')} placeholder="e.g. RPA, data engineering" />
          </div>
          <div className="pj-field">
            <label htmlFor="gradsPerYear">Graduates / year</label>
            <input id="gradsPerYear" type="number" min="0" value={f.gradsPerYear} onChange={set('gradsPerYear')} />
          </div>
        </div>

        <div className={'pj-field' + (errors.contact ? ' bad' : '')}>
          <label htmlFor="contact">Contact email</label>
          <input id="contact" type="email" value={f.contact} onChange={set('contact')} placeholder="partnerships@yourschool.com" />
          {errors.contact && <span className="pj-err">{errors.contact}</span>}
        </div>

        <label className={'pj-attest' + (errors.attest ? ' bad' : '')}>
          <input type="checkbox" checked={f.attest} onChange={set('attest')} />
          <span>I confirm our organisation is accredited and that we will only showcase students who have completed genuine marketplace work.</span>
        </label>
        {errors.attest && <span className="pj-err">{errors.attest}</span>}

        <div className="pj-submit">
          <button type="submit" className="mk-btn">Submit application</button>
          <Link to="/talent" className="mk-btn ghost">Cancel</Link>
        </div>
      </form>
    </div>
  );
}
