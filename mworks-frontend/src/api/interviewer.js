import { api } from './client.js';
import { uploadKindFile } from './listings.js';

export async function fetchInterviewerListing(slug = 'ai-interviewer') {
  return api(`/v1/listings/${encodeURIComponent(slug)}`);
}

export async function startInterviewerTrial(slug = 'ai-interviewer') {
  return api(`/v1/listings/${encodeURIComponent(slug)}/trial`, { method: 'POST', auth: true });
}

export async function fetchInterviewerLicense(slug = 'ai-interviewer') {
  return api(`/v1/interviewer/license?listing_slug=${encodeURIComponent(slug)}`, { auth: true });
}

export async function fetchInterviewerLicenses() {
  return api('/v1/interviewer/licenses', { auth: true });
}

export async function fetchInterviewerDocs(slug = 'ai-interviewer') {
  return api(`/v1/interviewer/docs?listing_slug=${encodeURIComponent(slug)}`, { auth: true });
}

export async function addInterviewerDoc(file, slug = 'ai-interviewer') {
  const object_key = await uploadKindFile(file, 'rag_doc');
  return api(`/v1/interviewer/docs?listing_slug=${encodeURIComponent(slug)}`, { method: 'POST', body: { object_key }, auth: true });
}

export async function createInterviewerSession(payload = {}) {
  return api('/v1/interviewer/sessions', { method: 'POST', body: payload, auth: true });
}

export async function fetchInterviewerSessions() {
  return api('/v1/interviewer/sessions', { auth: true });
}

export async function fetchInterviewerSession(id) {
  return api(`/v1/interviewer/sessions/${encodeURIComponent(id)}`, { auth: true });
}

export async function consentInterviewer(id, consent) {
  return api(`/v1/interviewer/sessions/${encodeURIComponent(id)}/consent`, {
    method: 'POST',
    body: { consent },
    auth: true,
  });
}

export async function answerInterviewer(id, text) {
  return api(`/v1/interviewer/sessions/${encodeURIComponent(id)}/turns`, {
    method: 'POST',
    body: { text },
    auth: true,
  });
}
