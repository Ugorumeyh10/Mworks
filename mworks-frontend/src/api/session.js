const TOKEN_KEY = 'mw_access';
const REFRESH_KEY = 'mw_refresh';
const USER_KEY = 'mw_user';

export function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY) || '';
  } catch {
    return '';
  }
}

export function getRefreshToken() {
  try {
    return sessionStorage.getItem(REFRESH_KEY) || '';
  } catch {
    return '';
  }
}

export function getUser() {
  try {
    const raw = sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setSession({ access_token, refresh_token, user }) {
  sessionStorage.setItem(TOKEN_KEY, access_token);
  if (refresh_token) sessionStorage.setItem(REFRESH_KEY, refresh_token);
  if (user) sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_KEY);
  sessionStorage.removeItem(USER_KEY);
}
