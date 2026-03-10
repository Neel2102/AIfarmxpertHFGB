import React, { useEffect, useState, useCallback } from 'react';
import { Zap, Activity, Droplets, Thermometer, Wind, Cpu, RefreshCw, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Dashboard/UserSandbox.css';

const API_BASE_URL = '/api';

// ── Token Usage Card ──────────────────────────────────────────────────────────

function TokenUsageCard({ data, loading, error }) {
  if (loading) return <div className="sandbox-card sandbox-skeleton">Loading token usage...</div>;
  if (error) return <div className="sandbox-card sandbox-error"><AlertCircle size={16}/> {error}</div>;
  if (!data) return null;

  const pct = Math.min(100, data.usage_percent || 0);
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

      {/* Progress bar */}
      <div className="token-progress-wrap">
        <div className="token-progress-bar">
          <div
            className="token-progress-fill"
            style={{ width: `${pct}%`, background: color }}
          />
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

// ── Soil Telemetry Card ──────────────────────────────────────────────────────

const SENSORS = [
  { key: 'air_temperature',  label: 'Air Temp',    unit: '°C',    icon: Thermometer, color: '#FF6B6B' },
  { key: 'air_humidity',     label: 'Air Humidity', unit: '%',    icon: Wind,        color: '#4ECDC4' },
  { key: 'soil_moisture',    label: 'Soil Moisture',unit: '%',    icon: Droplets,    color: '#45B7D1' },
  { key: 'soil_temperature', label: 'Soil Temp',   unit: '°C',    icon: Thermometer, color: '#FF9F43' },
  { key: 'soil_ph',          label: 'Soil pH',     unit: 'pH',    icon: Activity,    color: '#AA96DA' },
  { key: 'nitrogen',         label: 'Nitrogen (N)', unit: 'mg/kg', icon: Cpu,        color: '#FCBAD3' },
  { key: 'phosphorus',       label: 'Phosphorus (P)',unit:'mg/kg', icon: Cpu,        color: '#FFFFD2' },
  { key: 'potassium',        label: 'Potassium (K)', unit:'mg/kg', icon: Cpu,        color: '#94a3b8' },
  { key: 'soil_ec',          label: 'Soil EC',     unit: 'µS/cm', icon: Zap,         color: '#A8D8EA' },
];

function fmt(v) {
  if (v === null || v === undefined) return '--';
  const n = Number(v);
  if (!isFinite(n)) return '--';
  return Math.abs(n) >= 100 ? n.toFixed(0) : n.toFixed(1);
}

function SoilTelemetryCard({ data, loading, error, onRefresh, lastUpdated }) {
  if (loading) return <div className="sandbox-card sandbox-skeleton">Loading sensor data...</div>;

  return (
    <div className="sandbox-card sandbox-soil-card">
      <div className="sandbox-card-header">
        <div className="sandbox-card-title">
          <Activity size={20} className="sandbox-icon-soil" />
          Live Soil Telemetry
        </div>
        <div className="sandbox-soil-header-right">
          {lastUpdated && (
            <span className="sandbox-timestamp">
              {new Date(lastUpdated).toLocaleTimeString()}
            </span>
          )}
          <button className="sandbox-refresh-btn" onClick={onRefresh} title="Refresh">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {error && (
        <div className="sandbox-sensor-notice">
          <AlertCircle size={14} /> {error}. Showing last known values below.
        </div>
      )}

      {!data && !error && (
        <div className="sandbox-sensor-notice">
          No sensor readings yet. Connect your Blynk device from the Hardware IoT tab to start collecting data.
        </div>
      )}

      {data && (
        <div className="sandbox-sensors-grid">
          {SENSORS.map(s => {
            const val = data[s.key];
            const Icon = s.icon;
            return (
              <div
                key={s.key}
                className="sandbox-sensor-chip"
                style={{ '--chip-color': s.color }}
              >
                <Icon size={14} className="sandbox-sensor-icon" />
                <div className="sandbox-sensor-info">
                  <div className="sandbox-sensor-label">{s.label}</div>
                  <div className="sandbox-sensor-value">
                    {fmt(val)}<span className="sandbox-sensor-unit"> {s.unit}</span>
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

// ── Main UserSandbox Component ────────────────────────────────────────────────

export default function UserSandbox() {
  const { user } = useAuth();

  const [tokenData, setTokenData]   = useState(null);
  const [tokenLoading, setTokenLoading] = useState(true);
  const [tokenError, setTokenError] = useState(null);

  const [soilData, setSoilData]     = useState(null);
  const [soilLoading, setSoilLoading] = useState(true);
  const [soilError, setSoilError]   = useState(null);
  const [soilTimestamp, setSoilTimestamp] = useState(null);

  const authHeaders = () => {
    const t = localStorage.getItem('access_token');
    return { 'Authorization': `Bearer ${t}`, 'Content-Type': 'application/json' };
  };

  // Fetch token usage
  useEffect(() => {
    if (!user) return;
    setTokenLoading(true);
    fetch(`${API_BASE_URL}/auth/token-usage`, { headers: authHeaders() })
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(d => { setTokenData(d); setTokenLoading(false); })
      .catch(e => { setTokenError(String(e)); setTokenLoading(false); });
  }, [user]);

  // Fetch soil telemetry
  const fetchSoil = useCallback(async () => {
    if (!user) return;
    setSoilLoading(true);
    try {
      const url = `${API_BASE_URL}/soil-tests/user-live?user_id=${user.id}`;
      const res = await fetch(url, { headers: authHeaders() });
      const json = await res.json();
      if (json.has_data && json.data) {
        setSoilData(json.data);
        setSoilTimestamp(json.timestamp || new Date().toISOString());
        setSoilError(null);
      } else {
        setSoilData(null);
        setSoilError(json.message || 'No data available');
      }
    } catch (e) {
      setSoilError('Failed to fetch sensor readings');
    } finally {
      setSoilLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchSoil();
    const iv = setInterval(fetchSoil, 15000); // refresh every 15s
    return () => clearInterval(iv);
  }, [fetchSoil]);

  return (
    <div className="sandbox-page">
      {/* Header */}
      <div className="sandbox-hero">
        <div className="sandbox-hero-content">
          <div className="sandbox-kicker">My Workspace</div>
          <h1 className="sandbox-title">User Sandbox</h1>
          <p className="sandbox-subtitle">
            Your personal AI usage dashboard and live farm sensor feed
          </p>
        </div>
        <div className="sandbox-user-badge">
          <div className="sandbox-avatar">
            {(user?.full_name || user?.username || 'U')[0].toUpperCase()}
          </div>
          <div>
            <div className="sandbox-user-name">{user?.full_name || user?.username}</div>
            <div className="sandbox-user-role">{user?.role || 'Farmer'}</div>
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
