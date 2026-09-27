import { api } from './client.js';
import { setSession } from './session.js';

export async function login(email, password) {
  const data = await api('/v1/auth/login', { method: 'POST', body: { email, password } });
  setSession(data);
  return data.user;
}

export async function signup(payload) {
  const data = await api('/v1/auth/signup', { method: 'POST', body: payload });
  setSession(data);
  return data.user;
}
