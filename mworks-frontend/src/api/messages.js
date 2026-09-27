import { api, apiEnabled } from './client.js';
import { conversations as fallback } from '../data/sampleData.js';

export async function fetchConversations() {
  if (!apiEnabled()) return fallback;
  return api('/v1/conversations', { auth: true });
}

export async function fetchMessages(id) {
  if (!apiEnabled()) return [];
  return api(`/v1/conversations/${encodeURIComponent(id)}/messages`, { auth: true });
}

export async function sendMessage(id, text) {
  return api(`/v1/conversations/${encodeURIComponent(id)}/messages`, {
    method: 'POST',
    body: { text },
    auth: true,
  });
}
