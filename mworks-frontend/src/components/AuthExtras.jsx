import Icon from './Icon.jsx';

export function GoogleMark() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M21.35 11.1h-9.17v2.98h5.27c-.23 1.4-1.62 4.1-5.27 4.1-3.17 0-5.76-2.62-5.76-5.86s2.59-5.86 5.76-5.86c1.8 0 3.01.77 3.7 1.43l2.52-2.43C16.9 3.44 14.76 2.5 12.18 2.5 6.98 2.5 2.8 6.68 2.8 11.88s4.18 9.38 9.38 9.38c5.42 0 9-3.8 9-9.16 0-.62-.07-1.08-.16-1.4z" />
    </svg>
  );
}

export function MicrosoftMark() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M3 3h8.5v8.5H3V3zm9.5 0H21v8.5h-8.5V3zM3 12.5h8.5V21H3v-8.5zm9.5 0H21V21h-8.5v-8.5z" />
    </svg>
  );
}

const COPY = {
  login: {
    heading: 'Verified performance, not just profiles.',
    points: [
      'Every automation is sandbox-tested before it earns a Verified badge.',
      'Your trust score follows you into jobs and hiring.',
      'Escrow holds funds until you confirm delivery.',
    ],
  },
  signup: {
    heading: 'Buy, sell, and get hired on proof of work.',
    points: [
      'List automations and prompt packs with real efficiency metrics.',
      'Hire vetted builders, or let the Job Agent apply for you.',
      'Under 5 minutes from sign-up to your first listing.',
    ],
  },
};

export function AuthAside({ variant = 'login' }) {
  const copy = COPY[variant] ?? COPY.login;
  return (
    <aside className="auth-aside">
      <img className="auth-aside-img" src="/keyboard-hero.jpg" alt="" aria-hidden="true" />
      <div className="auth-aside-top">Mworks: RPA / AI marketplace</div>
      <div className="auth-aside-mid">
        <h2>{copy.heading}</h2>
        <ul className="auth-aside-list">
          {copy.points.map((p) => (
            <li key={p}>
              <Icon name="check-circle" className="sm" />
              {p}
            </li>
          ))}
        </ul>
      </div>
      <div className="auth-aside-foot">
        Protected by encryption in transit and at rest. We comply with the Nigeria Data
        Protection Act (NDPA/NDPR). You control what profile data is shared.
      </div>
    </aside>
  );
}
