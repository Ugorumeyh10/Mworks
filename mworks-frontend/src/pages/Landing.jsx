import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import BrandMark from '../components/BrandMark.jsx';
import Popup from '../components/Popup.jsx';
import MarketplaceCard from '../components/MarketplaceCard.jsx';
import { listings as seedListings } from '../data/marketplace.js';
import { fetchListings } from '../api/listings.js';
import './Landing.css';

const STATS = [
  { to: 2400, suffix: '+', l: 'automations listed' },
  { to: 1.9, prefix: '₦', suffix: 'B', decimals: 1, l: 'paid out to builders' },
  { to: 18, suffix: 'k', l: 'jobs matched' },
  { to: 96, l: 'avg. seller trust score' },
];

const STEPS = [
  {
    icon: 'search',
    t: 'Discover',
    d: 'Browse a ranked feed of automations, prompts and training cohorts from verified sellers.',
  },
  {
    icon: 'card',
    t: 'Buy or hire',
    d: 'Checkout through escrow, or post a contract and let vetted builders come to you.',
  },
  {
    icon: 'send',
    t: 'Deploy and apply',
    d: 'Run it in minutes, or hand the keyboard to the Job Agent and let it apply on your behalf.',
  },
];

const FEATURES = [
  {
    icon: 'home',
    t: 'Marketplace',
    d: 'Battle-tested RPA and AI automations with real metrics, reviews and a verified-outcome badge.',
    to: '/discover',
    cta: 'Browse the feed',
  },
  {
    icon: 'briefcase',
    t: 'Job Agent',
    d: 'Set your filters once. The agent sources roles daily and applies while you sleep.',
    to: '/jobs',
    cta: 'Open Job Agent',
  },
  {
    icon: 'bot',
    t: 'AI Interviewer',
    d: 'Companies trial, buy, hire, or download a disclosed AI interviewer. It asks developers using profile, CV excerpts, and your docs.',
    to: '/listing/ai-interviewer',
    cta: 'Trial or buy',
  },
  {
    icon: 'bot',
    t: 'Assistant',
    d: 'Ask what to buy, how to deploy, or which contract to take. Answers grounded in your activity.',
    to: '/assistant',
    cta: 'Ask the Assistant',
  },
  {
    icon: 'book',
    t: 'Blog',
    d: 'Playbooks and tech news. A newsroom agent publishes from public feeds, with pictures and video when the source has them.',
    to: '/blog',
    cta: 'Read the newsroom',
  },
];

const TRACKS = [
  { icon: 'wallet', t: 'Finance ops', d: 'Reconciliation, invoicing, and close-cycle bots that already run in production.', c: 'Finance' },
  { icon: 'message', t: 'Support AI', d: 'Prompt packs and triage flows with originality checks, not recycled templates.', c: 'Customer Support' },
  { icon: 'users', t: 'People and hiring', d: 'Screening automations plus an AI Interviewer companies can trial or buy.', c: 'HR & Recruiting' },
  { icon: 'shield', t: 'Escrow by default', d: 'Funds sit with Mworks until you accept delivery. Disputes stay on-platform.', c: null },
];

function useCountUp(to, { duration = 1100, decimals = 0 } = {}) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) {
      setValue(to);
      return undefined;
    }
    let frame;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - p) ** 3;
      setValue(to * eased);
      if (p < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [to, duration]);
  return decimals ? value.toFixed(decimals) : Math.round(value).toLocaleString('en-NG');
}

function StatCell({ to, prefix = '', suffix = '', decimals = 0, l, delay }) {
  const n = useCountUp(to, { decimals });
  return (
    <div className={`lp-stat reveal ${delay}`}>
      <b>
        {prefix}
        {n}
        {suffix}
      </b>
      <span>{l}</span>
    </div>
  );
}

export default function Landing() {
  const [escrow, setEscrow] = useState(false);
  const [track, setTrack] = useState('All');
  const [listings, setListings] = useState(seedListings);

  useEffect(() => {
    let live = true;
    fetchListings().then((rows) => {
      if (live && Array.isArray(rows) && rows.length) setListings(rows);
    });
    return () => {
      live = false;
    };
  }, []);

  const cats = useMemo(
    () => ['All', ...new Set(listings.filter((l) => l.verified).map((l) => l.category))],
    [listings],
  );
  const featured = useMemo(() => {
    const pool = listings.filter((l) => l.verified);
    return (track === 'All' ? pool : pool.filter((l) => l.category === track)).slice(0, 6);
  }, [track, listings]);

  return (
    <div className="lp">
      <header className="lp-nav">
        <Link to="/" className="lp-brand">
          <BrandMark size={32} withWord />
        </Link>
        <nav className="lp-nav-links">
          <a href="#how">How it works</a>
          <a href="#market">Product</a>
          <a href="#cards">Listings</a>
          <Link to="/blog">Blog</Link>
          <Link to="/login">Sign in</Link>
          <Link to="/signup" className="lp-nav-cta">Get started</Link>
        </nav>
      </header>

      <section className="lp-hero">
        <img className="lp-hero-img" src="/keyboard-hero.jpg" alt="Silver keyboard with a green Apply now key" />
        <div className="lp-hero-scrim" />
        <div className="lp-hero-pattern" aria-hidden="true" />
        <div className="lp-hero-inner">
          <p className="lp-eyebrow reveal">RPA / AI marketplace</p>
          <h1 className="reveal reveal-d1">
            Automate the work.
            <br />
            Win the job.
          </h1>
          <p className="lp-lede reveal reveal-d2">
            Buy and sell proven automations, hire vetted builders, and let the Job Agent
            apply on your behalf. Every listing earned its badge in a sandbox, not a pitch deck.
          </p>
          <div className="lp-cta-row reveal reveal-d3">
            <Link to="/discover" className="lp-btn">Enter marketplace</Link>
            <Link to="/jobs" className="lp-btn ghost">Browse jobs</Link>
            <button type="button" className="lp-btn ghost" onClick={() => setEscrow(true)}>
              How escrow works
            </button>
          </div>
        </div>
      </section>

      <section className="lp-stats">
        {STATS.map((s, i) => (
          <StatCell key={s.l} {...s} delay={`reveal-d${i + 1}`} />
        ))}
      </section>

      <section id="how" className="lp-section">
        <p className="lp-kicker">How it works</p>
        <h2>From feed to deployed in three steps</h2>
        <div className="lp-steps">
          {STEPS.map((s, i) => (
            <div key={s.t} className={`lp-step reveal reveal-d${i + 1}`}>
              <span className="lp-step-num">{String(i + 1).padStart(2, '0')}</span>
              <span className="lp-step-icon"><Icon name={s.icon} /></span>
              <h3>{s.t}</h3>
              <p>{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="tracks" className="lp-section lp-section-alt">
        <p className="lp-kicker">Tracks</p>
        <h2>Built for the work Nigerian ops teams actually run</h2>
        <div className="lp-tracks">
          {TRACKS.map((t, i) => (
            <button
              type="button"
              key={t.t}
              className={`lp-track reveal reveal-d${i + 1}`}
              onClick={() => {
                if (t.c) {
                  setTrack(t.c);
                  document.getElementById('cards')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                  setEscrow(true);
                }
              }}
            >
              <span className="lp-track-icon"><Icon name={t.icon} className="lg" /></span>
              <h3>{t.t}</h3>
              <p>{t.d}</p>
              <span className="lp-track-cta">{t.c ? `See ${t.c}` : 'Open escrow guide'}</span>
            </button>
          ))}
        </div>
      </section>

      <section id="cards" className="lp-section">
        <div className="lp-section-head">
          <div>
            <p className="lp-kicker">Live listings</p>
            <h2>Verified automations, ready to buy</h2>
          </div>
          <div className="lp-filters" role="tablist" aria-label="Listing categories">
            {cats.map((c) => (
              <button
                key={c}
                type="button"
                role="tab"
                aria-selected={track === c}
                className={'chip' + (track === c ? ' on' : '')}
                onClick={() => setTrack(c)}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
        <div className="lp-cards">
          {featured.map((listing) => (
            <MarketplaceCard key={listing.id} listing={listing} />
          ))}
        </div>
        {featured.length === 0 && (
          <p className="mk-empty">No verified listings in this track yet. Try another filter.</p>
        )}
      </section>

      <section id="market" className="lp-section lp-section-alt">
        <p className="lp-kicker">Product</p>
        <h2>One workspace for building, buying and getting hired</h2>
        <div className="lp-features">
          {FEATURES.map((f, i) => (
            <div key={f.t} className={`lp-feature reveal reveal-d${i + 1}`}>
              <span className="lp-feature-icon"><Icon name={f.icon} className="lg" /></span>
              <h3>{f.t}</h3>
              <p>{f.d}</p>
              <Link to={f.to} className="lp-feature-link">
                {f.cta} <Icon name="arrow-left" className="sm lp-flip" />
              </Link>
            </div>
          ))}
        </div>
      </section>

      <section className="lp-band">
        <div>
          <h2>Ready to press the key?</h2>
          <p>Join the builders and buyers already running Mworks.</p>
        </div>
        <Link to="/signup" className="lp-btn">Get started</Link>
      </section>

      <footer className="lp-footer">
        <Link to="/" className="lp-brand">
          <BrandMark size={28} withWord />
        </Link>
        <p>© {new Date().getFullYear()} Mworks. RPA/AI marketplace.</p>
        <div className="lp-footer-links">
          <Link to="/discover">Marketplace</Link>
          <Link to="/jobs">Jobs</Link>
          <Link to="/blog">Blog</Link>
          <Link to="/assistant">Assistant</Link>
        </div>
      </footer>

      <Popup
        open={escrow}
        title="Escrow, in one minute"
        onClose={() => setEscrow(false)}
        actions={(
          <>
            <button type="button" className="lp-btn ghost" onClick={() => setEscrow(false)}>Close</button>
            <Link to="/browse" className="lp-btn" onClick={() => setEscrow(false)}>Browse listings</Link>
          </>
        )}
      >
        <p>1. You pay. Mworks holds the funds. The seller never sees your card.</p>
        <p>2. The builder delivers. You review the work against the brief.</p>
        <p>3. You accept, and funds release. If something is off, open a dispute on-platform.</p>
      </Popup>
    </div>
  );
}
