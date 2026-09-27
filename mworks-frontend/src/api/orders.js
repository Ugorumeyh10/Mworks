import { api, apiEnabled } from './client.js';

export async function fetchOrders(role = 'buying') {
  return api(`/v1/orders?role=${encodeURIComponent(role)}`, { auth: true });
}

export async function fetchOrder(id) {
  return api(`/v1/orders/${encodeURIComponent(id)}`, { auth: true });
}

export async function confirmLocalPayment(reference) {
  return api('/v1/payments/local/confirm', { method: 'POST', body: { reference }, auth: true });
}

export async function verifyPayment(id) {
  return api(`/v1/payments/verify/${encodeURIComponent(id)}`, { method: 'POST', auth: true });
}

export async function confirmDelivery(id) {
  return api(`/v1/orders/${encodeURIComponent(id)}/confirm`, { method: 'POST', auth: true });
}

export async function markDelivered(id, objectKey) {
  return api(`/v1/orders/${encodeURIComponent(id)}/deliver`, {
    method: 'POST',
    body: { object_key: objectKey },
    auth: true,
  });
}

export async function fetchMyListings() {
  return api('/v1/me/listings', { auth: true });
}

export async function fetchOrderDownload(id) {
  return api(`/v1/orders/${encodeURIComponent(id)}/download`, { auth: true });
}

export async function fetchOrderContent(id) {
  return api(`/v1/orders/${encodeURIComponent(id)}/content`, { auth: true });
}

export { apiEnabled };
