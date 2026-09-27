import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import {
  addInterviewerDoc,
  createInterviewerSession,
  fetchInterviewerDocs,
  fetchInterviewerLicense,
  fetchInterviewerLicenses,
  fetchInterviewerSessions,
  startInterviewerTrial,
} from '../api/interviewer.js';
import { fetchListings } from '../api/listings.js';
import { fetchMyListings } from '../api/orders.js';
import { fetchMyApplications } from '../api/jobs.js';
import { getToken } from '../api/session.js';
import './Jobs.css';

export default function InterviewerHub() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const authed = Boolean(getToken());
  const slug = params.get('listing') || 'ai-interviewer';
  const [license, setLicense] = useState(null);
  const [docs, setDocs] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [apps, setApps] = useState([]);
  const [agents, setAgents] = useState([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState('');
  const [jobSlug, setJobSlug] = useState('');
  const [applicationId, setApplicationId] = useState('');

  const load = (listingSlug = slug) => {
    fetchInterviewerLicense(listingSlug).then(setLicense).catch(() => setLicense(null));
    fetchInterviewerDocs(listingSlug).then(setDocs).catch(() => setDocs([]));
    fetchInterviewerSessions().then(setSessions).catch(() => setSessions([]));
    fetchMyApplications().then(setApps).catch(() => setApps([]));
    Promise.all([
      fetchListings({ type: 'agent' }),
      fetchMyListings().catch(() => []),
      fetchInterviewerLicenses().catch(() => []),
    ]).then(([live, mine, licensed]) => {
      const byId = new Map();
      (live || []).forEach((row) => byId.set(row.id, row));
      (mine || []).filter((row) => row.type === 'agent' && row.status === 'live').forEach((row) => byId.set(row.id, row));
      (licensed || []).forEach((row) => {
        if (!byId.has(row.listingId)) {
          byId.set(row.listingId, { id: row.listingId, title: row.listingId, type: 'agent' });
        }
      });
      setAgents([...byId.values()]);
    }).catch(() => setAgents([]));
  };

  useEffect(() => {
    if (!authed) return undefined;
    load(slug);
    return undefined;
  }, [authed, slug]);

  if (!authed) {
    return (
      <div className="mk-page mk-narrow">
        <h1>AI Interviewer</h1>
        <div className="mk-empty">
          <Link to="/login?next=/interviewer">Sign in</Link> to trial, buy, or run the interviewer.
        </div>
      </div>
    );
  }

  const trial = async () => {
    setError('');
    setBusy('trial');
    try {
      const row = await startInterviewerTrial(slug);
      setLicense(row);
    } catch (err) {
      setError(err.message || 'Could not start the trial.');
    } finally {
      setBusy('');
    }
  };

  const upload = async (file) => {
    if (!file) return;
    setError('');
    setBusy('doc');
    try {
      await addInterviewerDoc(file, slug);
      load(slug);
    } catch (err) {
      setError(err.message || 'Could not index that document.');
    } finally {
      setBusy('');
    }
  };

  const start = async () => {
    setError('');
    setNotice('');
    setBusy('session');
    try {
      const row = await createInterviewerSession({
        listing_slug: slug,
        job_slug: jobSlug || undefined,
        application_id: applicationId || undefined,
      });
      if (row.youAreCandidate) {
        navigate(`/interviewer/s/${row.id}`);
      } else {
        setNotice(`Invite sent to ${row.candidateName}. They open ${row.id} after they sign in and consent.`);
        load(slug);
      }
    } catch (err) {
      setError(err.message || 'Could not start a session.');
    } finally {
      setBusy('');
    }
  };

  return (
    <div className="mk-page mk-narrow">
      <div className="mk-head">
        <div>
          <h1>AI Interviewer</h1>
          <p className="sub">
            Companies trial, buy, hire, or download an agent from the marketplace, or list their own.
            The agent asks developers questions using profile, a CV excerpt, and uploaded docs. It always discloses it is AI.
          </p>
        </div>
        <Link to="/sell/new" className="mk-btn ghost">List an agent</Link>
      </div>

      {error && <p className="sf-err" role="alert">{error}</p>}
      {notice && <p className="pj-hint">{notice}</p>}

      <div className="mk-card">
        <div className="mk-sec-title">Agent</div>
        <label className="pj-field">
          Marketplace agent
          <select
            value={slug}
            onChange={(e) => {
              const next = e.target.value;
              setParams(next && next !== 'ai-interviewer' ? { listing: next } : {});
            }}
          >
            {(() => {
              const rows = agents.length ? [...agents] : [{ id: 'ai-interviewer', title: 'Mworks AI Interviewer' }];
              if (slug && !rows.some((a) => a.id === slug)) {
                rows.unshift({ id: slug, title: slug });
              }
              return rows.map((a) => (
                <option key={a.id} value={a.id}>{a.title || a.id}</option>
              ));
            })()}
          </select>
        </label>
      </div>

      <div className="mk-card">
        <div className="mk-sec-title">License</div>
        {license ? (
          <p className="jd-text">
            {license.plan === 'seller'
              ? `You listed this agent. Operator seat · ${license.turnsUsed}/${license.turnsCap} turns used · expires ${license.expiresAt}`
              : `${license.plan} · ${license.status} · ${license.turnsUsed}/${license.turnsCap} turns used · expires ${license.expiresAt}`}
          </p>
        ) : (
          <p className="jd-text">No license yet. Start a capped free trial or buy the hosted seat.</p>
        )}
        <div className="jd-applied-actions" style={{ justifyContent: 'flex-start', marginTop: 12 }}>
          {license?.plan !== 'seller' && (
            <button type="button" className="mk-btn sm" onClick={trial} disabled={busy === 'trial'}>
              {busy === 'trial' ? 'Starting…' : 'Start free trial'}
            </button>
          )}
          <Link to={`/listing/${slug}`} className="mk-btn ghost sm">Buy or hire</Link>
        </div>
      </div>

      <div className="mk-card">
        <div className="mk-sec-title">Company documents (RAG)</div>
        <p className="jd-apply-sub">Upload a role brief, rubric, or stack notes. Files are scanned first. They are not executed. Secrets are redacted before the model sees a chunk.</p>
        <label className="sf-file">
          <Icon name="upload" className="sm" />
          {busy === 'doc' ? 'Scanning…' : 'Upload txt, md, pdf, or docx'}
          <input type="file" accept=".pdf,.docx,.md,.txt" hidden onChange={(e) => upload(e.target.files?.[0])} />
        </label>
        {docs.length === 0 ? <p className="pj-hint">No docs indexed yet.</p> : docs.map((d) => (
          <div className="vrow" key={d.id}><span>{d.filename}</span><span>{d.chunks} chunks</span></div>
        ))}
      </div>

      <div className="mk-card">
        <div className="mk-sec-title">Start a session</div>
        <p className="jd-apply-sub">Leave applicant blank to practice on yourself. To invite a candidate, paste a job application id (JA-) from a role you posted.</p>
        <label className="pj-field">
          Job slug (optional)
          <input value={jobSlug} onChange={(e) => setJobSlug(e.target.value)} placeholder="rpa-dev-fintech" />
        </label>
        <label className="pj-field">
          Application id (optional)
          <input value={applicationId} onChange={(e) => setApplicationId(e.target.value)} placeholder="JA-XXXXXXXX" />
        </label>
        <button type="button" className="mk-btn sm" onClick={start} disabled={busy === 'session'}>
          {busy === 'session' ? 'Opening…' : applicationId ? 'Send invite' : 'Start AI interview'}
        </button>
      </div>

      <div className="mk-card">
        <div className="mk-sec-title">Sessions</div>
        {sessions.length === 0 ? (
          <p className="pj-hint">No sessions yet.</p>
        ) : sessions.map((s) => (
          <Link to={`/interviewer/s/${s.id}`} className="ma-row" key={s.id} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="ma-main">
              <strong>{s.jobTitle || (s.youAreCandidate && !s.youAreCompany ? 'Interview invite' : 'Practice session')}</strong>
              <span>
                {s.youAreCandidate ? 'You' : s.candidateName} · {s.status}
                {s.score != null ? ` · score ${s.score}` : s.consentRequired ? ' · waiting on consent' : ''}
              </span>
            </div>
          </Link>
        ))}
      </div>

      {apps.length > 0 && (
        <p className="pj-hint">Your applications: {apps.map((a) => `${a.jobId} (${a.id})`).join(', ')}</p>
      )}
    </div>
  );
}
