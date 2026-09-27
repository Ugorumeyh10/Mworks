import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import JobsTabs from '../components/JobsTabs.jsx';
import { APP_STATUS } from '../data/jobs.js';
import { fetchMyApplications } from '../api/jobs.js';
import { getToken } from '../api/session.js';
import './Jobs.css';

export default function MyApplications() {
  const authed = Boolean(getToken());
  const [rows, setRows] = useState([]);

  useEffect(() => {
    if (!authed) return undefined;
    fetchMyApplications().then(setRows).catch(() => setRows([]));
    return undefined;
  }, [authed]);

  if (!authed) {
    return (
      <div className="mk-page">
        <JobsTabs />
        <div className="mk-empty"><Link to="/login?next=/jobs/applications">Sign in</Link> to see your applications.</div>
      </div>
    );
  }

  return (
    <div className="mk-page">
      <JobsTabs />

      <div className="mk-head">
        <div>
          <h1>My applications</h1>
          <p className="sub">Roles you applied to manually or via the Job Agent.</p>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="mk-empty">You haven’t applied to any roles yet. <Link to="/jobs/board" className="mk-inline-link">Browse the board.</Link></div>
      ) : (
        <div className="mk-card ma-list">
          {rows.map((a) => {
            const st = APP_STATUS[a.status] || APP_STATUS.applied;
            return (
              <Link to={`/jobs/board/${a.jobId}`} className="ma-row" key={a.id}>
                <div className="ma-main">
                  <strong>{a.title}</strong>
                  <span>{a.company} · applied {a.appliedAt}</span>
                </div>
                <span className={'ma-via ' + a.via}>
                  <Icon name={a.via === 'agent' ? 'bot' : 'user'} className="sm" />
                  {a.via === 'agent' ? 'Job Agent' : 'Manual'}
                </span>
                <span className="ma-fit">{a.fit}% fit{a.interviewScore != null ? ` · AI ${a.interviewScore}` : ''}</span>
                <span className={`mk-pill ${st.tone}`}>{st.label}</span>
                <Icon name="chevron-right" className="sm ma-chev" />
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
