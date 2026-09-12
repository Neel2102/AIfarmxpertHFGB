/**
 * Access-token lifecycle shared by every API caller.
 *
 * The backend issues a 30-minute access token plus a 7-day refresh token.
 * AuthContext exposed a `refreshToken()` function but nothing ever called it,
 * and the refresh endpoint itself rejected the frontend's JSON body, so the
 * access token could never be renewed. Half an hour into any session every
 * request started coming back 401 and the app reported "we couldn't load your
 * farm information" instead of restoring the session.
 *
 * This module owns that lifecycle in one place:
 *   - refreshes the access token when it is expired or about to expire,
 *   - collapses concurrent refreshes into a single in-flight request,
 *   - clears the session and notifies the app when the refresh token is dead.
 */

import { API_BASE_URL } from './apiBase';

/** Fired on `window` when the session cannot be renewed and must be re-established. */
export const SESSION_EXPIRED = 'farmxpert:session-expired';

// Refresh this long before actual expiry, so a request never races the clock.
const REFRESH_SKEW_MS = 60 * 1000;

let inFlightRefresh = null;

/** Decode a JWT payload. Returns null for anything that is not a readable JWT. */
export function decodeJwt(token) {
  try {
    const parts = (token || '').split('.');
    if (parts.length < 2) return null;
    let base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4 !== 0) base64 += '=';
    const json = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function isExpired(token, skewMs = REFRESH_SKEW_MS) {
  const payload = decodeJwt(token);
  // A token we cannot read is not treated as expired here: the backend also
  // accepts opaque session tokens, and only it can judge those.
  if (!payload || !payload.exp) return false;
  return payload.exp * 1000 - skewMs <= Date.now();
}

export function clearSession() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('session_token');
  localStorage.removeItem('user');
}

function notifyExpired() {
  clearSession();
  window.dispatchEvent(new CustomEvent(SESSION_EXPIRED));
}

/**
 * Exchange the stored refresh token for a new access token.
 * Returns the new access token, or null when the session cannot be renewed.
 * Concurrent callers share one request.
 */
export function refreshAccessToken() {
  if (inFlightRefresh) return inFlightRefresh;

  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) {
    notifyExpired();
    return Promise.resolve(null);
  }

  inFlightRefresh = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // A body, not a query parameter — a token in the URL ends up in access
        // logs, proxies and browser history.
        body: JSON.stringify({ refresh_token: refresh }),
      });

      if (!response.ok) {
        // 401/422 mean the refresh token is invalid or expired: the session is
        // genuinely over. Anything else is likely a transient server problem,
        // so keep the session and let the caller surface the error.
        if (response.status === 401 || response.status === 403 || response.status === 422) {
          notifyExpired();
        }
        return null;
      }

      const data = await response.json();
      if (!data?.access_token) {
        notifyExpired();
        return null;
      }

      localStorage.setItem('access_token', data.access_token);
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
      if (data.user) localStorage.setItem('user', JSON.stringify(data.user));
      return data.access_token;
    } catch (e) {
      // Network failure — do not destroy a session that may still be valid.
      console.warn('Token refresh failed:', e);
      return null;
    } finally {
      inFlightRefresh = null;
    }
  })();

  return inFlightRefresh;
}

/**
 * The access token to send with a request, refreshed first if it is expired or
 * within the skew window. Returns null when the caller is not signed in.
 */
export async function getValidAccessToken() {
  const token = localStorage.getItem('access_token');
  if (!token) return null;
  if (!isExpired(token)) return token;
  return await refreshAccessToken();
}

/** Authorization header for a request, refreshing the token when needed. */
export async function authHeader() {
  const token = await getValidAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * fetch() that keeps the session alive: it attaches a fresh access token, and
 * retries once against a one-off 401 (for example when the token expired
 * between the check and the request reaching the server).
 */
export async function authFetch(url, options = {}) {
  const buildInit = (token) => {
    const headers = { ...(options.headers || {}) };
    if (token) headers.Authorization = `Bearer ${token}`;
    return { ...options, headers };
  };

  let token = await getValidAccessToken();
  let response = await fetch(url, buildInit(token));

  if (response.status === 401 && localStorage.getItem('refresh_token')) {
    const renewed = await refreshAccessToken();
    if (renewed) {
      response = await fetch(url, buildInit(renewed));
    } else {
      notifyExpired();
    }
  }
  return response;
}
