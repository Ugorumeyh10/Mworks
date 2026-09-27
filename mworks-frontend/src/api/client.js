import { getToken, getRefreshToken, setSession, clearSession } from './session.js';

const BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export function apiEnabled() {
  return Boolean(BASE);
}

export class ApiError extends Error {
  constructor(message, { status, code } = {}) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

let refreshInFlight = null;

async function tryRefresh() {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  if (!refreshInFlight) {
    refreshInFlight = fetch(`${BASE}/v1/auth/refresh`, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
      .then(async (res) => {
        const data = await res.json().catch(() => null);
        if (!res.ok || !data || !data.access_token) {
          clearSession();
          return false;
        }
        setSession(data);
        return true;
      })
      .catch(() => {
        clearSession();
        return false;
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

export async function api(path, { method = 'GET', body, auth = false, _retry = false } = {}) {
  if (!BASE) {
    throw new ApiError('API is not configured.', { status: 0, code: 'NO_API' });
  }
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const token = getToken();
  if (auth || token) {
    if (!token && auth) throw new ApiError('Sign in required.', { status: 401, code: 'UNAUTHENTICATED' });
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }
  if (res.status === 401 && auth && !_retry) {
    const ok = await tryRefresh();
    if (ok) return api(path, { method, body, auth, _retry: true });
    clearSession();
  } else if (res.status === 401 && auth) {
    clearSession();
  }
  if (!res.ok) {
    const message = (data && data.error) || 'Request could not be completed.';
    throw new ApiError(message, { status: res.status, code: data && data.code });
  }
  return data;
}
