import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import {
  answerInterviewer,
  consentInterviewer,
  fetchInterviewerSession,
} from '../api/interviewer.js';
import { getToken } from '../api/session.js';
import './Jobs.css';

export default function InterviewerLive() {
  const { id } = useParams();
  const navigate = useNavigate();
  const authed = Boolean(getToken());
  const [session, setSession] = useState(null);
  const [missing, setMissing] = useState(false);
  const [consent, setConsent] = useState(false);
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const logRef = useRef(null);

  const load = () => {
    fetchInterviewerSession(id)
      .then(setSession)
      .catch(() => setMissing(true));
  };

  useEffect(() => {
    if (!authed) {
      navigate(`/login?next=/interviewer/s/${id}`);
      return undefined;
    }
    load();
    return undefined;
  }, [authed, id, navigate]);

  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [session?.turns?.length]);

  if (!authed) {
    return <p className="body-text">Sign in to continue…</p>;
  }

  if (missing) {
    return (
      <div className="mk-page mk-narrow">
        <Link to="/interviewer" className="mk-back">Interviewer console</Link>
        <div className="mk-empty">This interview was not found.</div>
      </div>
    );
  }

  if (!session) return <p className="body-text">Loading interview…</p>;

  const agree = async () => {
    setError('');
    setBusy(true);
    try {
      const row = await consentInterviewer(id, true);
      setSession(row);
    } catch (err) {
      setError(err.message || 'Consent is required.');
    } finally {
      setBusy(false);
    }
  };

  const send = async () => {
    if (busy || text.trim().length < 2) return;
    setError('');
    setBusy(true);
    try {
      const row = await answerInterviewer(id, text.trim());
      setSession(row);
      setText('');
    } catch (err) {
      setError(err.message || 'Could not send that answer.');
    } finally {
      setBusy(false);
    }
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const scored = session.status === 'scored';
  const statusLabel = scored
    ? `Scored ${session.score}`
    : session.consentRequired
      ? 'Awaiting consent'
      : 'In progress';

  return (
    <div className="mk-page iv-page">
      <div className="iv-top">
        <Link to="/interviewer" className="mk-back"><Icon name="arrow-left" className="sm" /> Interviewer console</Link>
        <span className={`mk-pill ${scored ? 'ok' : ''}`}>{statusLabel}</span>
      </div>

      <div className="iv-rail" role="note">
        <span className="iv-rail-stripe" aria-hidden="true" />
        <Icon name="bot" />
        <p>
          <strong>AI interviewer.</strong> Not a human.{' '}
          {session.companyName && session.companyName !== session.candidateName
            ? `${session.companyName} reads the transcript and a human decides any hire.`
            : 'A human reviewer reads the scorecard.'}
          {' '}{session.docsHint}
          {!session.consentRequired && !scored && ` ${session.turnsLeft} turns left on this license.`}
        </p>
      </div>

      <h1 className="iv-title">{session.jobTitle || 'Practice interview'}</h1>

      {session.consentRequired && !session.youAreCandidate && (
        <div className="mk-card iv-gate">
          <div className="mk-sec-title">Waiting on consent</div>
          <p className="jd-apply-sub">
            {session.candidateName || 'The candidate'} must sign in, tick consent, and start. There is no silent recording and no fake human interviewer.
          </p>
        </div>
      )}

      {session.consentRequired && session.youAreCandidate && (
        <div className="mk-card iv-gate">
          <div className="mk-sec-title">Before you start</div>
          <p className="jd-apply-sub">
            Recording this chat requires your consent. There is no silent recording and no fake human interviewer.
          </p>
          <label className="jd-check">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            I consent. I understand this interviewer is an AI using my Mworks profile, optional CV excerpt, and company docs.
          </label>
          {error && <p className="sf-err" role="alert">{error}</p>}
          <button type="button" className="mk-btn" disabled={!consent || busy} onClick={agree}>
            {busy ? 'Starting…' : 'Begin interview'}
          </button>
        </div>
      )}

      {!session.consentRequired && (
        <div className={'iv-grid' + (scored ? ' with-score' : '')}>
          <div className="iv-room">
            <div className="iv-log" ref={logRef}>
              {(session.turns || []).map((t, i) => (
                <div key={`${t.role}-${i}`} className={'iv-turn' + (t.role === 'agent' ? ' agent' : ' human')}>
                  {t.role === 'agent' && <span className="iv-avatar" aria-hidden="true"><Icon name="bot" className="sm" /></span>}
                  <div className="iv-bubble">
                    <span className="iv-who">{t.role === 'agent' ? 'AI Interviewer' : session.youAreCandidate ? 'You' : session.candidateName}</span>
                    {t.text}
                  </div>
                </div>
              ))}
              {busy && <p className="iv-typing">AI Interviewer is thinking…</p>}
            </div>

            {!scored && session.youAreCandidate && (
              <div className="iv-composer">
                <textarea
                  rows="2"
                  placeholder="Answer in your own words. Enter to send. Do not paste secrets."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={onKey}
                />
                <button type="button" className="mk-btn" disabled={busy || text.trim().length < 2} onClick={send} aria-label="Send answer">
                  <Icon name="send" className="sm" />
                </button>
              </div>
            )}
            {!scored && !session.youAreCandidate && (
              <p className="iv-wait">Waiting for {session.candidateName || 'the candidate'} to answer. You cannot send replies as the company.</p>
            )}
            {error && !session.consentRequired && <p className="sf-err" role="alert">{error}</p>}
          </div>

          {scored && (
            <aside className="iv-score">
              <div className="iv-score-num">
                <b>{session.score}</b>
                <span>/ 100 · human review required</span>
              </div>
              {session.summary && <p className="jd-text">{session.summary}</p>}
              {(session.scorecard || []).map((row) => (
                <div className="vrow" key={row.label}>
                  <span>{row.label}</span>
                  <span className={String(row.status).toLowerCase().includes('miss') ? 'bad' : 'ok'}>{row.status}</span>
                </div>
              ))}
            </aside>
          )}
        </div>
      )}
    </div>
  );
}
