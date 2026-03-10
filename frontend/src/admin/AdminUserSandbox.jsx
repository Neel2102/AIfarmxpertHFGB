/**
 * AdminUserSandbox — Admin-only view of a specific farmer's IoT telemetry and AI token usage.
 * Accessed via /admin/sandbox/:userId  (linked from the AdminSandbox user drawer).
 */
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Zap, Activity, Droplets, Thermometer, Wind, Cpu, RefreshCw, AlertCircle, ArrowLeft } from 'lucide-react';
import '../styles/Dashboard/UserSandbox.css';

const API_BASE_URL = '/api';

// ── Helpers ────────────────────────────────────────────────────────────────────

function authHeaders() {
  const t = localStorage.getItem('access_token') || localStorage.getItem('session_token') || localStorage.getItem('token');
  return { 'Authorization': `Bearer ${t}`, 'Content-Type': 'application/json' };
}

// ── Token Usage Card ──────────────────────────────────────────────────────────

function TokenUsageCard({ data, loading, error }) {
  if (loading) return <div className="sandbox-card sandbox-skeleton">Loading token usage…</div>;
  if (error)   return <div className="sandbox-card sandbox-error"><AlertCircle size={16}/> {error}</div>;
  if (!data)   return null;

  const pct   = Math.min(100, data.usage_percent || 0);
  const color = pct > 80 ? '#ef4444' : pct > 50 ? '#f59e0b' : '#22c55e';

  return (
    <div className="sandbox-card sandbox-token-card">
      <div className="sandbox-card-header">
        <div className="sandbox-card-title">
          <Zap size={20} className="sandbox-icon-token" />
          AI Token Usage
        </div>
        <div className="sandbox-badge">{data.period}</div>
      </div>

      <div className="token-usage-main">
        <div className="token-big-number">
          {(data.tokens_used || 0).toLocaleString()}
          <span className="token-label">tokens used</span>
        </div>
        <div className="token-quota">of {(data.tokens_quota || 100000).toLocaleString()} quota</div>
      </div>

      <div className="token-progress-wrap">
        <div className="token-progress-bar">
          <div className="token-progress-fill" style={{ width: `${pct}%`, background: color }} />
        </div>
        <span className="token-progress-label" style={{ color }}>{pct}%</span>
      </div>

      <div className="token-stats-grid">
        <div className="token-stat">
          <div className="token-stat-value">{(data.tokens_remaining || 0).toLocaleString()}</div>
          <div className="token-stat-label">Remaining</div>
        </div>
        <div className="token-stat">
          <div className="token-stat-value">{data.api_calls || 0}</div>
          <div className="token-stat-label">API Calls</div>
        </div>
        <div className="token-stat">
          <div className="token-stat-value">${(data.estimated_cost_usd || 0).toFixed(4)}</div>
          <div className="token-stat-label">Est. Cost</div>
        </div>
        <div className="token-stat">
          <div className="token-stat-value" style={{ fontSize: '0.7rem' }}>{data.model || 'Gemini'}</div>
          <div className="token-stat-label">Model</div>
        </div>
      </div>
    </div>
  );
}

// ── Soil Telemetry Card ────────────────────────────────────────────────────────

const SENSORS = [
  { key: 'air_temperature',   label: 'Air Temp',      unit: '°C',    icon: Thermometer, color: '#FF6B6B' },
  { key: 'air_humidity',      label: 'Air Humidity',  unit: '%',     icon: Wind,        color: '#4ECDC4' },
  { key: 'soil_moisture',     label: 'Soil Moisture', unit: '%',     icon: Droplets,    color: '#45B7D1' },
  { key: 'soil_temperature',  label: 'Soil Temp',     unit: '°C',    icon: Thermometer, color: '#FF9F43' },
  { key: 'soil_ph',           label: 'Soil pH',       unit: 'pH',    icon: Activity,    color: '#AA96DA' },
  { key: 'nitrogen',          label: 'Nitrogen (N)',   unit: 'mg/kg', icon: Cpu,         color: '#FCBAD3' },
  { key: 'phosphorus',        label: 'Phosphorus (P)',unit: 'mg/kg', icon: Cpu,         color: '#FFFFD2' },
  { key: 'potassium',         label: 'Potassium (K)', unit: 'mg/kg', icon: Cpu,         color: '#94a3b8' },
  { key: 'soil_ec',           label: 'Soil EC',       unit: 'µS/cm', icon: Zap,         color: '#A8D8EA' },
];

const fmt = (v) => {
  if (v === null || v === undefined) return '--';
  const n = Number(v);
  return isFinite(n) ? (Math.abs(n) >= 100 ? n.toFixed(0) : n.toFixed(1)) : '--';
};

function SoilTelemetryCard({ data, loading, error, onRefresh, lastUpdated }) {
  if (loading) return <div className="sandbox-card sandbox-skeleton">Loading sensor data…</div>;

  return (
    <div className="sandbox-card sandbox-soil-card">
      <div className="sandbox-card-header">
        <div className="sandbox-card-title">
          <Activity size={20} className="sandbox-icon-soil" />
          Live Soil Telemetry
        </div>
        <div className="sandbox-soil-header-right">
          {lastUpdated && (
            <span className="sandbox-timestamp">{new Date(lastUpdated).toLocaleTimeString()}</span>
          )}
          <button className="sandbox-refresh-btn" onClick={onRefresh} title="Refresh">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {error && (
        <div className="sandbox-sensor-notice">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {!data && !error && (
        <div className="sandbox-sensor-notice">
          No sensor readings recorded for this user yet. Ask them to connect a Blynk device.
        </div>
      )}

      {data && (
        <div className="sandbox-sensors-grid">
          {SENSORS.map(s => {
            const Icon = s.icon;
            return (
              <div key={s.key} className="sandbox-sensor-chip" style={{ '--chip-color': s.color }}>
                <Icon size={14} className="sandbox-sensor-icon" />
                <div className="sandbox-sensor-info">
                  <div className="sandbox-sensor-label">{s.label}</div>
                  <div className="sandbox-sensor-value">
                    {fmt(data[s.key])}<span className="sandbox-sensor-unit"> {s.unit}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Main AdminUserSandbox Component ───────────────────────────────────────────

export default function AdminUserSandbox() {
  const { userId } = useParams();           // /admin/sandbox/:userId
  const navigate   = useNavigate();

  const [targetUser, setTargetUser] = useState(null);
  const [userLoading, setUserLoading] = useState(true);

  const [tokenData, setTokenData]       = useState(null);
  const [tokenLoading, setTokenLoading] = useState(true);
  const [tokenError, setTokenError]     = useState(null);

  const [soilData, setSoilData]         = useState(null);
  const [soilLoading, setSoilLoading]   = useState(true);
  const [soilError, setSoilError]       = useState(null);
  const [soilTimestamp, setSoilTimestamp] = useState(null);

  // Admin role guard
  const isAdmin = (() => {
    try {
      const stored = JSON.parse(localStorage.getItem('user') || '{}');
      return (stored.role || '').toLowerCase() === 'admin';
    } catch { return false; }
  })();

  // Resolve user info from admin API
  useEffect(() => {
    if (!userId) return;
    setUserLoading(true);
    fetch(`${API_BASE_URL}/admin/users/${userId}`, { headers: authHeaders() })
      .then(r => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then(d => { setTargetUser(d); setUserLoading(false); })
      .catch(() => { setUserLoading(false); });
  }, [userId]);

  // Fetch token usage for this specific user
  useEffect(() => {
    if (!userId) return;
    setTokenLoading(true);
    // Use admin token-usage endpoint with explicit user_id param
    fetch(`${API_BASE_URL}/auth/token-usage?target_user_id=${userId}`, { headers: authHeaders() })
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(d => { setTokenData(d); setTokenLoading(false); })
      .catch(e => { setTokenError(String(e)); setTokenLoading(false); });
  }, [userId]);

  // Fetch live telemetry for this specific user
  const fetchSoil = useCallback(async () => {
    if (!userId) return;
    setSoilLoading(true);
    try {
      const res  = await fetch(`${API_BASE_URL}/soil-tests/user-live?user_id=${userId}`, { headers: authHeaders() });
      const json = await res.json();
      if (json.has_data && json.data) {
        setSoilData(json.data);
        setSoilTimestamp(json.timestamp || new Date().toISOString());
        setSoilError(null);
      } else {
        setSoilData(null);
        setSoilError(json.message || 'No data available');
      }
    } catch {
      setSoilError('Failed to fetch sensor readings');
    } finally {
      setSoilLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchSoil();
    const iv = setInterval(fetchSoil, 15000);
    return () => clearInterval(iv);
  }, [fetchSoil]);

  // Guard: must be admin
  if (!isAdmin) {
    return (
      <div className="sandbox-page">
        <div className="sandbox-card sandbox-error">
          <AlertCircle size={20} />
          Admin access required. You are not authorised to view this page.
        </div>
      </div>
    );
  }

  const displayName = targetUser
    ? (targetUser.full_name || targetUser.username || `User #${userId}`)
    : (userLoading ? 'Loading…' : `User #${userId}`);

  return (
    <div className="sandbox-page">
      {/* Back button */}
      <button
        onClick={() => navigate('/admin')}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
          color: '#94a3b8', borderRadius: 10, padding: '8px 16px',
          cursor: 'pointer', fontSize: '0.85rem', marginBottom: 20,
        }}
      >
        <ArrowLeft size={16} /> Back to Admin Dashboard
      </button>

      {/* Hero */}
      <div className="sandbox-hero">
        <div className="sandbox-hero-content">
          <div className="sandbox-kicker">Admin View</div>
          <h1 className="sandbox-title">User Sandbox</h1>
          <p className="sandbox-subtitle">
            Viewing IoT telemetry and AI usage for farmer — <strong style={{ color: '#e2e8f0' }}>{displayName}</strong>
          </p>
        </div>
        <div className="sandbox-user-badge">
          <div className="sandbox-avatar">
            {displayName[0]?.toUpperCase() || 'U'}
          </div>
          <div>
            <div className="sandbox-user-name">{displayName}</div>
            <div className="sandbox-user-role">User ID #{userId}</div>
          </div>
        </div>
      </div>

      {/* Cards */}
      <div className="sandbox-grid">
        <TokenUsageCard data={tokenData} loading={tokenLoading} error={tokenError} />
        <SoilTelemetryCard
          data={soilData}
          loading={soilLoading}
          error={soilError}
          onRefresh={fetchSoil}
          lastUpdated={soilTimestamp}
        />
      </div>
    </div>
  );
}
