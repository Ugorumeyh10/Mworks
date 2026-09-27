import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { currentUser } from '../data/profile.js';
import {
  applyToJob,
  fetchInterview,
  fetchJob,
  fetchJobApplicants,
  fetchScorecard,
  fetchVideoQuestions,
  startInterview,
  submitInterview,
  submitVideoAnswer,
} from '../api/jobs.js';
import { createInterviewerSession, fetchInterviewerLicenses } from '../api/interviewer.js';
import { uploadKindFile } from '../api/listings.js';
import { getToken, getUser } from '../api/session.js';
import './Jobs.css';

export default function JobDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const sessionUser = getUser();
  const u = {
    name: sessionUser?.name || currentUser.name,
    trustScore: sessionUser?.trust ?? currentUser.trustScore,
    stats: currentUser.stats,
    skills: currentUser.skills,
  };

  const [job, setJob] = useState(null);
  const [missing, setMissing] = useState(false);
  const [shareHistory, setShareHistory] = useState(true);
  const [note, setNote] = useState('');
  const [cvFile, setCvFile] = useState(null);
  const [applied, setApplied] = useState(false);
  const [fitReason, setFitReason] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');

  const [task, setTask] = useState(null);
  const [work, setWork] = useState('');
  const [scorecard, setScorecard] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [videoFile, setVideoFile] = useState(null);
  const [questionId, setQuestionId] = useState('');
  const [consent, setConsent] = useState(false);
  const [videoStatus, setVideoStatus] = useState('');
  const [applicants, setApplicants] = useState(null);
  const [inviteMsg, setInviteMsg] = useState('');

  const authed = Boolean(getToken());

  useEffect(() => {
    let live = true;
    setMissing(false);
    fetchJob(id).then((row) => {
      if (!live) return;
      if (row) setJob(row);
      else setMissing(true);
    }).catch(() => {
      if (live) setMissing(true);
    });
    return () => { live = false; };
  }, [id]);

  useEffect(() => {
    if (!authed || !id) return undefined;
    let live = true;
    fetchInterview(id).then((row) => { if (live) setTask(row); }).catch(() => {});
    fetchScorecard(id).then((row) => { if (live) setScorecard(row); }).catch(() => {});
    fetchVideoQuestions(id).then((rows) => {
      if (!live) return;
      setQuestions(rows || []);
      if (rows?.[0]?.id) setQuestionId(rows[0].id);
    }).catch(() => {});
    fetchJobApplicants(id).then((rows) => { if (live) setApplicants(rows || []); }).catch(() => { if (live) setApplicants(null); });
    return () => { live = false; };
  }, [authed, id]);

  if (missing) {
    return (
      <div className="mk-page mk-narrow">
        <Link to="/jobs/board" className="mk-back"><Icon name="arrow-left" className="sm" /> Job board</Link>
        <div className="mk-empty">This role is no longer listed.</div>
      </div>
    );
  }

  if (!job) {
    return <p className="body-text">Loading role…</p>;
  }

  const meetsBar = u.trustScore >= job.minTrust;

  const submit = async () => {
    if (!authed) {
      navigate(`/login?next=/jobs/board/${job.id}`);
      return;
    }
    setError('');
    setBusy('apply');
    try {
      let cv_object_key;
      if (cvFile) {
        cv_object_key = await uploadKindFile(cvFile, 'cv');
      }
      const row = await applyToJob(job.id, {
        note: note.trim() || undefined,
        share_history: shareHistory,
        via: 'manual',
        cv_object_key,
      });
      setFitReason(row.reason || '');
      setApplied(true);
    } catch (err) {
      if (err.status === 400) {
        setApplied(true);
      } else {
        setError(err.message || 'Could not send the application.');
      }
    } finally {
      setBusy('');
    }
  };

  const beginInterview = async () => {
    setError('');
    setBusy('interview');
    try {
      const row = await startInterview(job.id);
      setTask(row);
    } catch (err) {
      setError(err.message || 'Could not start the work sample.');
    } finally {
      setBusy('');
    }
  };

  const inviteApplicant = async (applicationId) => {
    setError('');
    setInviteMsg('');
    setBusy(`invite-${applicationId}`);
    try {
      const licenses = await fetchInterviewerLicenses().catch(() => []);
      const active = (licenses || []).find((row) => row.status === 'active');
      const row = await createInterviewerSession({
        listing_slug: active?.listingId || 'ai-interviewer',
        job_slug: job.id,
        application_id: applicationId,
      });
      setInviteMsg(`Invite sent to ${row.candidateName}. They open ${row.id} after they sign in and consent.`);
      setApplicants((prev) => (prev || []).map((a) => (
        a.id === applicationId ? { ...a, status: a.status === 'applied' ? 'interview' : a.status, interviewSessionId: row.id } : a
      )));
    } catch (err) {
      setError(err.message || 'Could not send that invite. Start a trial or buy the interviewer first.');
    } finally {
      setBusy('');
    }
  };

  const finishInterview = async () => {
    setError('');
    setBusy('interview');
    try {
      const row = await submitInterview(job.id, { prompt_text: work.trim() });
      setScorecard(row);
      setTask((prev) => ({ ...(prev || {}), status: row.status }));
    } catch (err) {
      setError(err.message || 'Could not score the work sample.');
    } finally {
      setBusy('');
    }
  };

  const sendVideo = async () => {
    setError('');
    setVideoStatus('');
    if (!consent) {
      setError('Tick the consent box. Recordings are never stored without it.');
      return;
    }
    if (!videoFile || !questionId) {
      setError('Choose a question and attach an mp4 or webm file.');
      return;
    }
    setBusy('video');
    try {
      const object_key = await uploadKindFile(videoFile, 'interview_video');
      const row = await submitVideoAnswer(job.id, {
        question_id: questionId,
        object_key,
        consent: true,
      });
      setVideoStatus(`Stored until ${row.retainUntil}. A human reviewer sees the transcript.`);
    } catch (err) {
      setError(err.message || 'Could not store the recording.');
    } finally {
      setBusy('');
    }
  };

  return (
    <div className="mk-page mk-narrow">
      <Link to="/jobs/board" className="mk-back"><Icon name="arrow-left" className="sm" /> Job board</Link>

      <div className="jd-head">
        <span className="avatar org jd-logo">{job.companyAvatar}</span>
        <div>
          <h1>{job.title}</h1>
          <div className="jd-company">
            {job.company}
            {job.verifiedEmployer && <span className="jb-verified"><Icon name="check-circle" className="sm" /> Verified employer</span>}
            {job.source && <span className="mk-pill">Sourced</span>}
          </div>
          <div className="jd-meta">
            <span className="mk-pill info">{job.type}</span>
            <span><Icon name="pin" className="sm" /> {job.location}</span>
            <span><Icon name="wallet" className="sm" /> {job.salary}</span>
            <span><Icon name="clock" className="sm" /> {job.posted}</span>
          </div>
        </div>
      </div>

      <div className="mk-card">
        <div className="mk-sec-title">About the role</div>
        <div className="jd-text">{job.description}</div>
        {(job.responsibilities || []).length > 0 && (
          <>
            <div className="mk-sec-title" style={{ marginTop: 16 }}>Responsibilities</div>
            <ul className="jd-list">
              {job.responsibilities.map((r) => <li key={r}>{r}</li>)}
            </ul>
          </>
        )}
        <div className="mk-sec-title" style={{ marginTop: 16 }}>Required skills</div>
        <div className="jb-skills">{(job.skills || []).map((s) => <span className="chip" key={s}>{s}</span>)}</div>
      </div>

      <div className="mk-card">
        <div className="mk-sec-title">About {job.company}</div>
        <div className="jd-text">{job.about}</div>
        {job.sourceUrl && (
          <p className="jd-text" style={{ marginTop: 12 }}>
            <a href={job.sourceUrl} target="_blank" rel="noopener noreferrer">Original posting</a>
          </p>
        )}
      </div>

      {applied ? (
        <div className="mk-card jd-applied">
          <span className="jd-applied-icon"><Icon name="check-circle" /></span>
          <h2>Application sent</h2>
          <p>
            {job.company} received your Mworks profile with a verified trust score of <b>{u.trustScore}</b>
            {shareHistory ? ', your full transaction history,' : ''} and your completion rate of {u.stats.completionRate}%.
            {fitReason ? ` Rank reason: ${fitReason}.` : ''} You can track it under My applications.
          </p>
          <div className="jd-applied-actions">
            <Link to="/jobs/applications" className="mk-btn">My applications</Link>
            <Link to="/jobs/board" className="mk-btn ghost">Back to board</Link>
          </div>
        </div>
      ) : (
        <div className="mk-card jd-apply">
          <div className="mk-sec-title">Apply with your Mworks profile</div>
          <p className="jd-apply-sub">
            Ranking uses marketplace evidence first: trust, sales, verified skills, and your note.
            A CV is optional extra signal. It is scanned locally and is not sent to a model.
          </p>

          <div className="jd-share">
            <div className="jd-share-row"><span>Name</span><span>{u.name}</span></div>
            <div className="jd-share-row">
              <span>Verified trust score</span>
              <span className={meetsBar ? 'ok' : 'warn'}>
                {u.trustScore} {meetsBar ? '· meets the ' : '· below the '}{job.minTrust}+ bar
              </span>
            </div>
            <div className="jd-share-row"><span>Completion rate</span><span>{u.stats.completionRate}%</span></div>
            <div className="jd-share-row"><span>Completed sales / projects</span><span>{u.stats.sales}</span></div>
            <div className="jd-share-row"><span>Verified skills</span><span>{u.skills.slice(0, 3).join(', ')}</span></div>
          </div>

          <label className="jd-check">
            <input type="checkbox" checked={shareHistory} onChange={(e) => setShareHistory(e.target.checked)} />
            Share my full transaction history with this employer
          </label>

          {!meetsBar && (
            <p className="jd-warn">
              <Icon name="shield" className="sm" />
              Your trust score is below this employer's preferred minimum. You can still apply - some employers relax the bar for strong profiles.
            </p>
          )}

          <textarea
            className="jd-note"
            rows="3"
            placeholder="Optional note to the employer…"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />

          <label className="sf-file">
            <Icon name="upload" className="sm" />
            {cvFile ? cvFile.name : 'Optional CV (pdf, docx, txt)'}
            <input
              type="file"
              accept=".pdf,.docx,.md,.txt"
              hidden
              onChange={(e) => setCvFile(e.target.files?.[0] || null)}
            />
          </label>

          {error && <p className="sf-err" role="alert">{error}</p>}
          <button className="mk-btn wide" onClick={submit} disabled={busy === 'apply'}>
            {busy === 'apply' ? 'Sending…' : authed ? 'Submit application' : 'Sign in to apply'}
          </button>
        </div>
      )}

      {authed && (
        <div className="mk-card jd-hire">
          <div className="mk-sec-title">Timed automation work sample</div>
          <p className="jd-apply-sub">
            {task?.prompt || 'A static scorecard runs tests on your prompt or flow. Your file is never executed on the API.'}
          </p>
          {task?.timeLimitSec ? <p className="pj-hint">Time box: {Math.round(task.timeLimitSec / 60)} minutes.</p> : null}
          {(!task || task.status === 'ready') && (
            <button className="mk-btn sm" type="button" onClick={beginInterview} disabled={busy === 'interview'}>
              {busy === 'interview' ? 'Starting…' : 'Start work sample'}
            </button>
          )}
          {task?.status === 'in_progress' && (
            <>
              <textarea
                className="jd-note"
                rows="6"
                placeholder="Paste a prompt, flow XML, or short script. Include how you would automate and test it."
                value={work}
                onChange={(e) => setWork(e.target.value)}
              />
              <button className="mk-btn sm" type="button" onClick={finishInterview} disabled={busy === 'interview' || work.trim().length < 12}>
                {busy === 'interview' ? 'Scoring…' : 'Submit for scorecard'}
              </button>
            </>
          )}
          {scorecard && (
            <div className="jd-scorecard">
              <strong>Score {scorecard.score} · {scorecard.status}</strong>
              {(scorecard.scorecard || []).map((row) => (
                <div className="vrow" key={row.label}>
                  <span>{row.label}</span>
                  <span className={String(row.status).toLowerCase().includes('fail') || row.status === 'Missed' || row.status === 'Exceeded' ? 'bad' : 'ok'}>
                    {row.status}{row.detail ? ` · ${row.detail}` : ''}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {authed && applicants && (
        <div className="mk-card jd-hire">
          <div className="mk-sec-title">Invite to AI Interviewer</div>
          <p className="jd-apply-sub">
            Send a disclosed AI interview. The candidate must consent. Scorecards land on this application for a human to review.
          </p>
          {inviteMsg && <p className="pj-hint">{inviteMsg}</p>}
          {error && applicants && <p className="sf-err" role="alert">{error}</p>}
          {applicants.length === 0 ? (
            <p className="pj-hint">No applications yet.</p>
          ) : applicants.map((a) => (
            <div className="ma-row" key={a.id} style={{ alignItems: 'center' }}>
              <div className="ma-main">
                <strong>{a.name}</strong>
                <span>
                  {a.fit}% fit · trust {a.trust}
                  {a.interviewScore != null ? ` · AI ${a.interviewScore}` : ''}
                </span>
                {a.interviewSummary && <span className="jd-apply-sub">{a.interviewSummary}</span>}
              </div>
              {a.interviewSessionId ? (
                <Link to={`/interviewer/s/${a.interviewSessionId}`} className="mk-btn ghost sm">Open session</Link>
              ) : (
                <button
                  type="button"
                  className="mk-btn sm"
                  disabled={busy === `invite-${a.id}`}
                  onClick={() => inviteApplicant(a.id)}
                >
                  {busy === `invite-${a.id}` ? 'Inviting…' : 'Invite'}
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {authed && (
        <div className="mk-card jd-hire">
          <div className="mk-sec-title">AI Interviewer</div>
          <p className="jd-apply-sub">
            Companies trial, buy, hire, or download this agent. If you were invited, open the console, consent, then answer.
            It always says it is an AI.
          </p>
          <Link to="/interviewer" className="mk-btn sm">Open interviewer</Link>
        </div>
      )}

      {authed && (
        <div className="mk-card jd-hire">
          <div className="mk-sec-title">Async video questions</div>
          <p className="jd-apply-sub">
            Apply first, then record on your own time. You must consent. Retention follows NDPR (default 90 days).
            A live AI interviewer is a separate product. It is never silently recorded and never pretends to be a human.
          </p>
          <label className="pj-field">
            Question
            <select value={questionId} onChange={(e) => setQuestionId(e.target.value)}>
              {questions.map((q) => (
                <option key={q.id} value={q.id}>{q.prompt}</option>
              ))}
            </select>
          </label>
          <label className="sf-file">
            <Icon name="upload" className="sm" />
            {videoFile ? videoFile.name : 'Upload mp4 or webm'}
            <input
              type="file"
              accept="video/mp4,video/webm,.mp4,.webm"
              hidden
              onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
            />
          </label>
          <label className="jd-check">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            I consent to Mworks storing this recording and a transcript for hiring review, then deleting it after the retention period. No live interviewer will impersonate a human.
          </label>
          {videoStatus && <p className="pj-hint">{videoStatus}</p>}
          {error && applied && <p className="sf-err" role="alert">{error}</p>}
          <button className="mk-btn sm" type="button" onClick={sendVideo} disabled={busy === 'video'}>
            {busy === 'video' ? 'Uploading…' : 'Store recording'}
          </button>
        </div>
      )}
    </div>
  );
}
