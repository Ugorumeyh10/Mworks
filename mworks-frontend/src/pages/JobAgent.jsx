import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import JobsTabs from '../components/JobsTabs.jsx';
import { agentApply, agentDismiss, fetchJobAgent, fetchJobAgentActivity, fetchMyApplications, updateJobAgent } from '../api/jobs.js';
import { getToken } from '../api/session.js';
import './JobAgent.css';

const REVIEW_BAND = 10;

export default function JobAgent() {
  const authed = Boolean(getToken());
  const [enabled, setEnabled] = useState(true);
  const [threshold, setThreshold] = useState(85);
  const [activity, setActivity] = useState([]);
  const [appliedIds, setAppliedIds] = useState({});
  const [dismissed, setDismissed] = useState({});
  const [tab, setTab] = useState('applied');
  const [error, setError] = useState('');

  const load = async () => {
    const [prefs, rows, apps] = await Promise.all([
      fetchJobAgent(),
      fetchJobAgentActivity(),
      fetchMyApplications(),
    ]);
    setEnabled(Boolean(prefs.enabled));
    setThreshold(prefs.threshold || 85);
    setActivity(rows);
    const applied = {};
    (apps || []).forEach((a) => { applied[a.jobId] = true; });
    setAppliedIds(applied);
  };

  useEffect(() => {
    if (!authed) return undefined;
    load().catch(() => setActivity([]));
    return undefined;
  }, [authed]);

  const persist = async (next) => {
    try {
      const saved = await updateJobAgent(next);
      setEnabled(saved.enabled);
      setThreshold(saved.threshold);
    } catch (err) {
      setError(err.message || 'Could not save Job Agent settings.');
    }
  };

  const buckets = useMemo(() => {
    const out = { applied: [], review: [], skipped: [] };
    for (const a of activity) {
      if (dismissed[a.id] || dismissed[a.jobId]) {
        out.skipped.push({ ...a, dismissed: true });
        continue;
      }
      if (appliedIds[a.jobId] || a.fit >= threshold) {
        out.applied.push(a);
        continue;
      }
      if (a.fit >= threshold - REVIEW_BAND) {
        out.review.push(a);
        continue;
      }
      out.skipped.push(a);
    }
    return out;
  }, [activity, threshold, appliedIds, dismissed]);

  const TABS = [
    ['applied', 'Applied', buckets.applied.length],
    ['review', 'Needs your review', buckets.review.length],
    ['skipped', 'Skipped', buckets.skipped.length],
  ];
  const rows = buckets[tab];

  const apply = async (jobId) => {
    setError('');
    try {
      await agentApply(jobId);
      setAppliedIds((o) => ({ ...o, [jobId]: true }));
    } catch (err) {
      if (err.status === 400) setAppliedIds((o) => ({ ...o, [jobId]: true }));
      else setError(err.message || 'Could not apply.');
    }
  };

  const dismiss = async (jobId) => {
    setError('');
    try {
      await agentDismiss(jobId);
      setDismissed((o) => ({ ...o, [jobId]: true }));
    } catch (err) {
      setError(err.message || 'Could not dismiss this role.');
    }
  };

  if (!authed) {
    return (
      <div className="mk-page">
        <JobsTabs />
        <div className="mk-empty"><Link to="/login?next=/jobs">Sign in</Link> to configure the Job Agent.</div>
      </div>
    );
  }

  return (
    <div className="mk-page">
      <JobsTabs />

      <div className="mk-head">
        <div>
          <h1>Job Agent</h1>
          <p className="sub">Scores live board roles - including jobs the ingest bot just posted from public career boards - against your verified profile and applies above your threshold.</p>
        </div>
      </div>

      {error && <p className="sf-err" role="alert">{error}</p>}

      <div className="mk-card ja-config">
        <div className="ja-config-row">
          <div className="ttext">
            <strong>Automatic search &amp; apply</strong>
            <span>{enabled ? 'On - the agent applies on your behalf above the threshold' : 'Off - the agent only scores and lists roles'}</span>
          </div>
          <button
            className={'toggle' + (enabled ? ' on' : '')}
            onClick={() => persist({ enabled: !enabled, threshold })}
            aria-pressed={enabled}
          />
        </div>

        <div className={'ja-threshold' + (enabled ? '' : ' disabled')}>
          <div className="ja-threshold-head">
            <span><Icon name="sliders" className="sm" /> Fit threshold</span>
            <b>{threshold}%</b>
          </div>
          <input
            type="range"
            min="60"
            max="95"
            step="5"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            onMouseUp={(e) => persist({ enabled, threshold: Number(e.target.value) })}
            onTouchEnd={(e) => persist({ enabled, threshold: Number(e.currentTarget.value) })}
            disabled={!enabled}
            className="ja-range"
          />
          <p className="ja-threshold-note">
            Applies automatically at <b>{threshold}%</b> fit or higher. Roles from {threshold - REVIEW_BAND}–{threshold - 1}% wait for your confirmation; below {threshold - REVIEW_BAND}% are logged as skipped, not hidden.
          </p>
        </div>
      </div>

      <div className="ja-tabs">
        {TABS.map(([id, label, n]) => (
          <button key={id} className={'ja-tab' + (tab === id ? ' on' : '')} onClick={() => setTab(id)}>
            {label} <span className="ja-tab-n">{n}</span>
          </button>
        ))}
      </div>

      {rows.length === 0 ? (
        <div className="mk-empty">Nothing in this list at a {threshold}% threshold.</div>
      ) : (
        <div className="ja-list">
          {rows.map((a) => (
            <div className="mk-card ja-item" key={a.id}>
              <div className="ja-item-main">
                <div className="ja-item-top">
                  <Link to={`/jobs/board/${a.jobId}`} className="ja-item-title">{a.title}</Link>
                  <span className={'ja-fit ' + (a.fit >= threshold ? 'hi' : a.fit >= threshold - REVIEW_BAND ? 'mid' : 'lo')}>{a.fit}% fit</span>
                </div>
                <div className="ja-item-sub">{a.company} · {a.track} · {a.at}</div>
                <p className="ja-item-reason">{a.reason}</p>
              </div>

              {tab === 'review' && (
                <div className="ja-item-actions">
                  <button className="mk-btn sm" onClick={() => apply(a.jobId)}>Apply anyway</button>
                  <button className="mk-btn ghost sm" onClick={() => dismiss(a.jobId)}>Dismiss</button>
                </div>
              )}
              {tab === 'applied' && appliedIds[a.jobId] && (
                <span className="mk-pill ok">On your applications</span>
              )}
              {tab === 'skipped' && (
                <Link to={`/jobs/board/${a.jobId}`} className="mk-btn ghost sm">Review role</Link>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="source-note">
        <Icon name="globe" className="sm" />
        Scored from the live Mworks job board, including roles the ingest bot pulls from public career boards. Every application carries your verified trust score.
      </div>
    </div>
  );
}
