const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1') as string;
let accessToken = localStorage.getItem('admin_access_token') || '';

export function setAccessToken(token: string) {
  accessToken = token;
  localStorage.setItem('admin_access_token', token);
}

export function clearAccessToken() {
  accessToken = '';
  localStorage.removeItem('admin_access_token');
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

async function handleResponse<T>(res: Response, path: string): Promise<T> {
  if (res.status === 401) {
    // Token expired — clear it and try to re-login with dev token
    clearAccessToken();
    const devToken = import.meta.env.VITE_ADMIN_DEV_TOKEN;
    const email = import.meta.env.VITE_ADMIN_EMAIL || 'admin@example.com';
    if (devToken) {
      try {
        const loginRes = await fetch(`${BASE_URL}/auth/dev-login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, full_name: 'Admin', admin_token: devToken }),
        });
        if (loginRes.ok) {
          const data = await loginRes.json();
          setAccessToken(data.access_token);
          return undefined as unknown as T; // caller should retry
        }
      } catch {
        // fall through
      }
    }
    // Could not re-login — reload to show login page
    window.location.reload();
    throw new Error('Session expired');
  }
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

export async function apiGet<T>(path: string): Promise<T> {
  let res = await fetch(`${BASE_URL}${path}`, { headers: headers() });
  if (res.status === 401) {
    await handleResponse(res, path); // refreshes token
    res = await fetch(`${BASE_URL}${path}`, { headers: headers() }); // retry with new token
  }
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

export async function apiPost<T>(path: string, payload: unknown): Promise<T> {
  let res = await fetch(`${BASE_URL}${path}`, { method: 'POST', headers: headers(), body: JSON.stringify(payload) });
  if (res.status === 401) {
    await handleResponse(res, path);
    res = await fetch(`${BASE_URL}${path}`, { method: 'POST', headers: headers(), body: JSON.stringify(payload) });
  }
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

export async function apiDelete<T>(path: string): Promise<T> {
  let res = await fetch(`${BASE_URL}${path}`, { method: 'DELETE', headers: headers() });
  if (res.status === 401) {
    await handleResponse(res, path);
    res = await fetch(`${BASE_URL}${path}`, { method: 'DELETE', headers: headers() });
  }
  if (!res.ok) throw new Error(`DELETE ${path} failed: ${res.status}`);
  return res.json();
}

export async function googleLogin(idToken: string) {
  const res = await fetch(`${BASE_URL}/auth/google/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!res.ok) throw new Error('Google login failed');
  const data = await res.json();
  setAccessToken(data.access_token);
  return data;
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
