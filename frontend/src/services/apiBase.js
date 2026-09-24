/**
 * The single API base-URL rule for the whole frontend.
 *
 * Convention
 * ----------
 *   REACT_APP_BACKEND_URL = the backend ORIGIN only, e.g.
 *       http://localhost:8000
 *       https://aifarmxperthfgb.onrender.com
 *
 *   API_BASE_URL          = that origin + "/api"
 *   endpoints             = "/auth/login", "/blynk/telemetry/live", ...
 *
 * Every caller must use API_BASE_URL and an endpoint WITHOUT its own "/api"
 * prefix. Mixing the two conventions is what produced the /api/api/... requests.
 *
 * The value is normalised defensively because the deployed env var is the one
 * thing this code cannot verify: a trailing slash, or a value that already ends
 * in "/api", is tolerated rather than silently producing a broken URL.
 */

const RAW = (process.env.REACT_APP_BACKEND_URL || '').trim();

function buildApiBase(raw) {
  if (!raw) return '/api';                 // same-origin / dev proxy
  let origin = raw.replace(/\/+$/, '');    // strip trailing slashes
  if (/\/api$/i.test(origin)) {
    // Already includes the /api suffix — do not add a second one.
    return origin;
  }
  return `${origin}/api`;
}

/** Backend origin with no path, e.g. "https://aifarmxperthfgb.onrender.com". */
export const BACKEND_ORIGIN = RAW.replace(/\/+$/, '').replace(/\/api$/i, '');

/** Base for all API calls, e.g. "https://aifarmxperthfgb.onrender.com/api". */
export const API_BASE_URL = buildApiBase(RAW);

/** Authorization header for the stored access token, or {} when signed out. */
export function authHeaders() {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default API_BASE_URL;
