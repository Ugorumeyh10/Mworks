import { api, apiEnabled } from './client.js';
import { initialAssistantMessages } from '../data/sampleData.js';

export async function fetchAssistantMessages() {
  if (!apiEnabled()) return initialAssistantMessages;
  return api('/v1/assistant/messages', { auth: true });
}

export async function sendAssistantMessage(text) {
  return api('/v1/assistant/messages', { method: 'POST', body: { text }, auth: true });
}
