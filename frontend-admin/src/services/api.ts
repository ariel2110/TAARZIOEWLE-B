const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1') as string;
let accessToken = localStorage.getItem('admin_access_token') || '';

export function setAccessToken(token: string) {
  accessToken = token;
  localStorage.setItem('admin_access_token', token);
}

function headers(extra?: Record<string, string>) {
  const base: Record<string, string> = { 'Content-Type': 'application/json', ...(extra || {}) };
  if (accessToken) {
    base['Authorization'] = `Bearer ${accessToken}`;
  } else {
    base['X-Admin-Token'] = import.meta.env.VITE_ADMIN_DEV_TOKEN || 'dev-admin-token';
    base['X-Admin-Email'] = import.meta.env.VITE_ADMIN_EMAIL || 'admin@example.com';
  }
  return base;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { headers: headers() });
  if (!res.ok) throw new Error(`GET ${path} failed`);
  return res.json();
}

export async function apiPost<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { method: 'POST', headers: headers(), body: JSON.stringify(payload) });
  if (!res.ok) throw new Error(`POST ${path} failed`);
  return res.json();
}

export async function devLogin(email: string, fullName: string, adminToken: string) {
  const res = await fetch(`${BASE_URL}/auth/dev-login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, full_name: fullName, admin_token: adminToken }),
  });
  if (!res.ok) throw new Error('Dev login failed');
  const data = await res.json();
  setAccessToken(data.access_token);
  return data;
}
