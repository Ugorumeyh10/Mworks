import { api } from './client.js';

export async function fetchBlogPosts(category) {
  const qs = category && category !== 'All' ? `?category=${encodeURIComponent(category)}` : '';
  try {
    return await api(`/v1/blog${qs}`);
  } catch {
    return [];
  }
}

export async function fetchBlogPost(slug) {
  return api(`/v1/blog/${encodeURIComponent(slug)}`);
}

export async function fetchBlogAdminPosts() {
  return api('/v1/blog/admin/posts', { auth: true });
}

export async function createBlogPost(payload) {
  return api('/v1/blog', { method: 'POST', body: payload, auth: true });
}

export async function publishBlogPost(slug) {
  return api(`/v1/blog/${encodeURIComponent(slug)}/publish`, { method: 'POST', auth: true });
}

export async function unpublishBlogPost(slug) {
  return api(`/v1/blog/${encodeURIComponent(slug)}/unpublish`, { method: 'POST', auth: true });
}

export async function runNewsAgent() {
  return api('/v1/blog/agent/run', { method: 'POST', auth: true });
}
