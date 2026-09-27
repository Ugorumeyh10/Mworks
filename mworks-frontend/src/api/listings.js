import { api, apiEnabled } from './client.js';
import { listings as fallbackListings, getListing as fallbackGet } from '../data/marketplace.js';

export async function fetchListings(params = {}) {
  if (!apiEnabled()) return fallbackListings;
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== 'all' && v !== false) qs.set(k, String(v));
  });
  const suffix = qs.toString() ? `?${qs}` : '';
  try {
    return await api(`/v1/listings${suffix}`);
  } catch {
    return [];
  }
}

export async function fetchListing(id) {
  if (!apiEnabled()) return fallbackGet(id) || null;
  try {
    return await api(`/v1/listings/${encodeURIComponent(id)}`);
  } catch (err) {
    if (err.status === 404) {
      return fallbackListings.find((row) => row.id === id) || null;
    }
    return fallbackGet(id) || null;
  }
}

export async function createListing(payload) {
  return api('/v1/listings', { method: 'POST', body: payload, auth: true });
}

export async function publishListing(id) {
  return api(`/v1/listings/${encodeURIComponent(id)}/publish`, { method: 'POST', auth: true });
}

export async function checkoutListing(id, payload) {
  return api(`/v1/listings/${encodeURIComponent(id)}/checkout`, { method: 'POST', body: payload, auth: true });
}

const MIME = {
  pdf: 'application/pdf',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  md: 'text/markdown',
  txt: 'text/plain',
  xml: 'application/xml',
  zip: 'application/zip',
  mp4: 'video/mp4',
  webm: 'video/webm',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  png: 'image/png',
  webp: 'image/webp',
  gif: 'image/gif',
};

export function listingFileKind(type) {
  return type === 'automation' ? 'package' : 'document';
}

export async function uploadListingFile(file, type) {
  const ext = (file.name.split('.').pop() || '').toLowerCase();
  const contentType = file.type || MIME[ext] || 'application/octet-stream';
  const kind = listingFileKind(type);
  return uploadObject(file, kind, contentType);
}

export async function uploadDeliveryFile(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase();
  const contentType = file.type || MIME[ext] || 'application/octet-stream';
  return uploadObject(file, 'delivery', contentType);
}

export async function uploadKindFile(file, kind) {
  const ext = (file.name.split('.').pop() || '').toLowerCase();
  const contentType = file.type || MIME[ext] || 'application/octet-stream';
  return uploadObject(file, kind, contentType);
}

export async function fileTheftClaim(id, reason) {
  return api(`/v1/listings/${encodeURIComponent(id)}/theft-claim`, {
    method: 'POST',
    body: { reason },
    auth: true,
  });
}

export async function fetchTheftClaims() {
  return api('/v1/admin/theft-claims', { auth: true });
}

export async function resolveTheftClaim(id, payload) {
  return api(`/v1/admin/theft-claims/${encodeURIComponent(id)}/resolve`, {
    method: 'POST',
    body: payload,
    auth: true,
  });
}

async function uploadObject(file, kind, contentType) {
  const signed = await api('/v1/uploads/presign', {
    method: 'POST',
    body: { filename: file.name, content_type: contentType, kind, size_bytes: file.size },
    auth: true,
  });
  const put = await fetch(signed.put_url, {
    method: 'PUT',
    headers: signed.headers || { 'Content-Type': contentType },
    body: file,
  });
  if (!put.ok) {
    throw new Error('The pack file could not be uploaded.');
  }
  await api('/v1/uploads/commit', {
    method: 'POST',
    body: { object_key: signed.object_key },
    auth: true,
  });
  return signed.object_key;
}
