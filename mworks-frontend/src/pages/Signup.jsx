import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthAside, GoogleMark, MicrosoftMark } from '../components/AuthExtras.jsx';
import BrandMark from '../components/BrandMark.jsx';
import { signup } from '../api/auth.js';
import { apiEnabled } from '../api/client.js';
import './Auth.css';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const ROLES = [
  { id: 'buyer', title: 'Buy automations', desc: 'Discover, verify, and purchase automations, prompts, and prompt packs.' },
  { id: 'seller', title: 'Sell automations', desc: 'List your bots and prompts with verified performance metrics.' },
  { id: 'both', title: 'Both', desc: 'Buy and sell. Switch roles anytime from your profile.' },
];

const COUNTRIES = ['Nigeria', 'Ghana', 'Kenya', 'South Africa', 'Egypt', 'Rwanda', 'United Kingdom', 'United States', 'Other'];

function pwScore(pw) {
  let s = 0;
  if (pw.length >= 8) s++;
  if (pw.length >= 12) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw) && /[^A-Za-z0-9]/.test(pw)) s++;
  return Math.min(s, 4);
}
const PW_LABEL = ['Too short', 'Weak', 'Fair', 'Good', 'Strong'];

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '', email: '', country: 'Nigeria',
    password: '', confirm: '', role: 'buyer',
    terms: false, twoFactor: true,
  });
  const [errors, setErrors] = useState({});
  const [showPw, setShowPw] = useState(false);

  const set = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, [k]: v }));
    setErrors((x) => ({ ...x, [k]: undefined }));
  };

  const score = pwScore(form.password);

  const submit = (e) => {
    e.preventDefault();
    const next = {};
    if (form.name.trim().length < 2) next.name = 'Enter your full name.';
    if (!EMAIL_RE.test(form.email)) next.email = 'Enter a valid email address.';
    if (form.password.length < 8) next.password = 'Use at least 8 characters.';
    if (form.confirm !== form.password) next.confirm = 'Passwords do not match.';
    if (!form.terms) next.terms = 'You must accept the terms and data processing notice.';
    setErrors(next);
    if (Object.keys(next).length === 0) {
      if (!apiEnabled()) {
        navigate('/discover');
        return;
      }
      signup({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        country: form.country,
        role: form.role,
      }).then(() => navigate('/discover')).catch((err) => {
        setErrors({ email: err.message || 'Could not create the account.' });
      });
    }
  };

  return (
    <div className="auth">
      <main className="auth-main">
        <div className="auth-inner">
          <Link to="/" className="auth-brand">
            <BrandMark size={32} withWord />
          </Link>

          <h1>Create your account</h1>
          <p className="auth-sub">One profile for buying, selling, and getting hired. Verified by proof of work.</p>

          <div className="auth-social">
            <button type="button" className="social-btn" disabled title="Google sign-in is not available yet">
              <GoogleMark /> Sign up with Google
            </button>
            <button type="button" className="social-btn" disabled title="Microsoft sign-in is not available yet">
              <MicrosoftMark /> Sign up with Microsoft
            </button>
          </div>

          <div className="auth-divider">or</div>

          <form className="auth-form" onSubmit={submit} noValidate>
            <div className="field">
              <label>I want to</label>
              <div className="role-picker">
                {ROLES.map((r) => (
                  <button
                    type="button"
                    key={r.id}
                    className={'role-opt' + (form.role === r.id ? ' on' : '')}
                    onClick={() => setForm((f) => ({ ...f, role: r.id }))}
                    aria-pressed={form.role === r.id}
                  >
                    <span className="role-radio" />
                    <span className="role-text">
                      <strong>{r.title}</strong>
                      <span>{r.desc}</span>
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className={'field' + (errors.name ? ' invalid' : '')}>
              <label htmlFor="name">Full name</label>
              <input id="name" type="text" autoComplete="name" placeholder="Ada Obi"
                value={form.name} onChange={set('name')} />
              {errors.name && <span className="field-error">{errors.name}</span>}
            </div>

            <div className={'field' + (errors.email ? ' invalid' : '')}>
              <label htmlFor="email">Work email</label>
              <input id="email" type="email" autoComplete="email" placeholder="you@company.com"
                value={form.email} onChange={set('email')} />
              {errors.email && <span className="field-error">{errors.email}</span>}
            </div>

            <div className="field">
              <label htmlFor="country">Country</label>
              <select id="country" value={form.country} onChange={set('country')}>
                {COUNTRIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>

            <div className={'field' + (errors.password ? ' invalid' : '')}>
              <label htmlFor="password">Password</label>
              <div className="pw-wrap">
                <input id="password" type={showPw ? 'text' : 'password'} autoComplete="new-password"
                  placeholder="At least 8 characters" value={form.password} onChange={set('password')} />
                <button type="button" className="pw-toggle" onClick={() => setShowPw((v) => !v)}>
                  {showPw ? 'Hide' : 'Show'}
                </button>
              </div>
              <div className="pw-meter" aria-hidden="true">
                {[0, 1, 2, 3].map((i) => <span key={i} className={i < score ? 'on' : ''} />)}
              </div>
              {form.password
                ? <span className="field-error" style={{ color: 'var(--muted)' }}>{PW_LABEL[score]}</span>
                : null}
              {errors.password && <span className="field-error">{errors.password}</span>}
            </div>

            <div className={'field' + (errors.confirm ? ' invalid' : '')}>
              <label htmlFor="confirm">Confirm password</label>
              <input id="confirm" type={showPw ? 'text' : 'password'} autoComplete="new-password"
                placeholder="Re-enter your password" value={form.confirm} onChange={set('confirm')} />
              {errors.confirm && <span className="field-error">{errors.confirm}</span>}
            </div>

            <label className="check-row">
              <input type="checkbox" checked={form.twoFactor} onChange={set('twoFactor')} />
              Enable two-factor authentication after sign-up (recommended)
            </label>

            <label className={'check-row' + (errors.terms ? ' invalid' : '')}>
              <input type="checkbox" checked={form.terms} onChange={set('terms')} />
              <span>
                I agree to the <a href="/">Terms of Service</a> and consent to Mworks processing my
                data under the <a href="/">NDPA/NDPR Privacy Notice</a>.
              </span>
            </label>
            {errors.terms && <span className="field-error">{errors.terms}</span>}

            <button type="submit" className="auth-submit">Create account</button>
          </form>

          <p className="form-note">
            Identity verification is completed after sign-up, before you can transact.
          </p>

          <p className="auth-alt">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </main>

      <AuthAside variant="signup" />
    </div>
  );
}
