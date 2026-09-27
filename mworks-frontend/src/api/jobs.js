import { api, apiEnabled } from './client.js';
import { jobPostings, myApplications, agentDefaults, agentActivity } from '../data/jobs.js';

export async function fetchJobs(params = {}) {
  if (!apiEnabled()) return jobPostings;
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== 'All' && v !== 0) qs.set(k, String(v));
  });
  const suffix = qs.toString() ? `?${qs}` : '';
  try {
    return await api(`/v1/jobs${suffix}`);
  } catch {
    return jobPostings;
  }
}

export async function fetchJob(id) {
  if (!apiEnabled()) return jobPostings.find((j) => j.id === id) || null;
  try {
    return await api(`/v1/jobs/${encodeURIComponent(id)}`);
  } catch (err) {
    if (err.status === 404) return jobPostings.find((j) => j.id === id) || null;
    return jobPostings.find((j) => j.id === id) || null;
  }
}

export async function createJob(payload) {
  return api('/v1/jobs', { method: 'POST', body: payload, auth: true });
}

export async function applyToJob(id, payload) {
  return api(`/v1/jobs/${encodeURIComponent(id)}/apply`, { method: 'POST', body: payload, auth: true });
}

export async function fetchMyApplications() {
  if (!apiEnabled()) return myApplications;
  try {
    return await api('/v1/me/applications', { auth: true });
  } catch {
    return [];
  }
}

export async function fetchJobAgent() {
  if (!apiEnabled()) return agentDefaults;
  try {
    return await api('/v1/me/job-agent', { auth: true });
  } catch {
    return agentDefaults;
  }
}

export async function updateJobAgent(payload) {
  return api('/v1/me/job-agent', { method: 'PATCH', body: payload, auth: true });
}

export async function fetchJobAgentActivity() {
  if (!apiEnabled()) return agentActivity;
  try {
    return await api('/v1/me/job-agent/activity', { auth: true });
  } catch {
    return [];
  }
}

export async function agentApply(jobId) {
  return api(`/v1/me/job-agent/activity/${encodeURIComponent(jobId)}/apply`, { method: 'POST', auth: true });
}

export async function agentDismiss(jobId) {
  return api(`/v1/me/job-agent/activity/${encodeURIComponent(jobId)}/dismiss`, { method: 'POST', auth: true });
}

export async function fetchInterview(id) {
  return api(`/v1/jobs/${encodeURIComponent(id)}/interview`, { auth: true });
}

export async function startInterview(id) {
  return api(`/v1/jobs/${encodeURIComponent(id)}/interview/start`, { method: 'POST', auth: true });
}

export async function submitInterview(id, payload) {
  return api(`/v1/jobs/${encodeURIComponent(id)}/interview/submit`, { method: 'POST', body: payload, auth: true });
}

export async function fetchScorecard(id) {
  return api(`/v1/jobs/${encodeURIComponent(id)}/interview/scorecard`, { auth: true });
}

export async function fetchJobApplicants(id) {
  return api(`/v1/jobs/${encodeURIComponent(id)}/applicants`, { auth: true });
}

export async function fetchVideoQuestions(id) {
  return api(`/v1/jobs/${encodeURIComponent(id)}/video-questions`, { auth: true });
}

export async function submitVideoAnswer(id, payload) {
  return api(`/v1/jobs/${encodeURIComponent(id)}/video-answers`, { method: 'POST', body: payload, auth: true });
}
