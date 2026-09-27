import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthAside, GoogleMark, MicrosoftMark } from '../components/AuthExtras.jsx';
import BrandMark from '../components/BrandMark.jsx';
import { login } from '../api/auth.js';
import { apiEnabled } from '../api/client.js';
import './Auth.css';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Login() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get('next') || '/discover';
  const [form, setForm] = useState({ email: '', password: '', remember: true });
  const [errors, setErrors] = useState({});
  const [showPw, setShowPw] = useState(false);

  const set = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, [k]: v }));
    setErrors((x) => ({ ...x, [k]: undefined }));
  };

  const submit = async (e) => {
    e.preventDefault();
    const fieldErrors = {};
    if (!EMAIL_RE.test(form.email)) fieldErrors.email = 'Enter a valid email address.';
    if (form.password.length < 8) fieldErrors.password = 'Password must be at least 8 characters.';
    setErrors(fieldErrors);
    if (Object.keys(fieldErrors).length !== 0) return;
    if (!apiEnabled()) {
      navigate('/discover');
      return;
    }
    try {
      await login(form.email.trim(), form.password);
      navigate(next.startsWith('/') ? next : '/discover');
    } catch (err) {
      setErrors({ password: err.message || 'Email or password is incorrect.' });
    }
  };

  return (
    <div className="auth">
      <main className="auth-main">
        <div className="auth-inner">
          <Link to="/" className="auth-brand">
            <BrandMark size={32} withWord />
          </Link>

          <h1>Welcome back</h1>
          <p className="auth-sub">Sign in to manage your listings, transactions, and job activity.</p>

          <div className="auth-social">
            <button type="button" className="social-btn" disabled title="Google sign-in is not available yet">
              <GoogleMark /> Continue with Google
            </button>
            <button type="button" className="social-btn" disabled title="Microsoft sign-in is not available yet">
              <MicrosoftMark /> Continue with Microsoft
            </button>
          </div>

          <div className="auth-divider">or</div>

          <form className="auth-form" onSubmit={submit} noValidate>
            <div className={'field' + (errors.email ? ' invalid' : '')}>
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                value={form.email}
                onChange={set('email')}
              />
              {errors.email && <span className="field-error">{errors.email}</span>}
            </div>

            <div className={'field' + (errors.password ? ' invalid' : '')}>
              <div className="field-label-row">
                <label htmlFor="password">Password</label>
                <Link to="/login" className="link" style={{ fontSize: 12.5 }}>Forgot password?</Link>
              </div>
              <div className="pw-wrap">
                <input
                  id="password"
                  type={showPw ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={set('password')}
                />
                <button type="button" className="pw-toggle" onClick={() => setShowPw((v) => !v)}>
                  {showPw ? 'Hide' : 'Show'}
                </button>
              </div>
              {errors.password && <span className="field-error">{errors.password}</span>}
            </div>

            <label className="check-row">
              <input type="checkbox" checked={form.remember} onChange={set('remember')} />
              Keep me signed in on this device
            </label>

            <button type="submit" className="auth-submit">Sign in</button>
          </form>

          <p className="form-note">
            Two-factor authentication is prompted here when enabled on your account.
          </p>

          <p className="auth-alt">
            New to Mworks? <Link to="/signup">Create an account</Link>
          </p>
        </div>
      </main>

      <AuthAside variant="login" />
    </div>
  );
}
