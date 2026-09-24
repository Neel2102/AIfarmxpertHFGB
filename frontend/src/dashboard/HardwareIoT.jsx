import React, { useCallback, useEffect, useState } from "react";
import { Cpu, Wifi, AlertCircle, Loader2, Trash2, ThermometerSun, Droplets, FlaskConical, BarChart3 } from "lucide-react";
import "../styles/Dashboard/HardwareIoT.css";
import { useAuth } from "../contexts/AuthContext";

// The browser no longer calls the Blynk cloud directly. It used to fetch nine
// virtual pins with the farmer's auth token exposed in the page, which meant
// readings only existed while this tab was open — which is exactly why the
// Soil & Sensors page showed "--" while this page showed live values.
// Both pages now read the same backend telemetry endpoint.
import { API_BASE_URL } from '../services/apiBase';

const SENSORS = [
  { label: "Air Temperature", pin: "V0", unit: "°C", color: "#FF6B6B" },
  { label: "Air Humidity", pin: "V1", unit: "%", color: "#4ECDC4" },
  { label: "Soil Moisture", pin: "V2", unit: "%", color: "#45B7D1" },
  { label: "Soil Temperature", pin: "V3", unit: "°C", color: "#FF9F43" },
  { label: "Soil EC", pin: "V4", unit: "µS/cm", color: "#A8D8EA" },
  { label: "Soil pH", pin: "V5", unit: "pH", color: "#AA96DA" },
  { label: "Nitrogen (N)", pin: "V6", unit: "mg/kg", color: "#FCBAD3" },
  { label: "Phosphorus (P)", pin: "V7", unit: "mg/kg", color: "#FFFFD2" },
  { label: "Potassium (K)", pin: "V8", unit: "mg/kg", color: "#837E7C" },
];

// Canonical telemetry field for each virtual pin. Must match
// farmxpert/services/telemetry_service.py PIN_MAP.
const FIELD_BY_PIN = {
  V0: "air_temperature",
  V1: "air_humidity",
  V2: "soil_moisture",
  V3: "soil_temperature",
  V4: "soil_ec",
  V5: "soil_ph",
  V6: "nitrogen",
  V7: "phosphorus",
  V8: "potassium",
};

const SENSOR_RANGES = {
  V0: { min: 0, max: 50 },
  V1: { min: 0, max: 100 },
  V2: { min: 0, max: 100 },
  V3: { min: 0, max: 50 },
  V4: { min: 0, max: 5000 },
  V5: { min: 0, max: 14 },
  V6: { min: 0, max: 200 },
  V7: { min: 0, max: 200 },
  V8: { min: 0, max: 1000 },
};

const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

const parseNumeric = (v) => {
  if (v === null || v === undefined) return null;
  const s = String(v).trim();
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
};

const formatValue = (n) => {
  if (n === null || n === undefined) return "--";
  if (!Number.isFinite(n)) return "--";
  if (Math.abs(n) >= 1000) return String(Math.round(n));
  if (Math.abs(n) >= 100) return n.toFixed(0);
  if (Math.abs(n) >= 10) return n.toFixed(1);
  return n.toFixed(2);
};

const toPercent = (pin, n) => {
  const range = SENSOR_RANGES[pin] || { min: 0, max: 100 };
  if (n === null) return 0;
  const denom = range.max - range.min || 1;
  const pct = ((n - range.min) / denom) * 100;
  return clamp(pct, 0, 100);
};

export default function HardwareIoT() {
  const { user } = useAuth();
  // The Blynk auth token is no longer kept in the browser at all. It is stored
  // server-side at registration and only the backend ever sends it to Blynk.
  const [hasDevice, setHasDevice] = useState(false);
  const [checkingDevice, setCheckingDevice] = useState(true);

  // Onboarding form state
  const [tokenInput, setTokenInput] = useState("");
  const [deviceNameInput, setDeviceNameInput] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [registerError, setRegisterError] = useState(null);

  // Sensor dashboard state
  const [sensorData, setSensorData] = useState({});
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Delete / disconnect current Blynk device
  const handleDeleteDevice = async () => {
    if (!window.confirm("Disconnect this Blynk device? You can add a new one after.")) return;

    // Delete from backend DB
    try {
      const token = localStorage.getItem('access_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      await fetch(`${API_BASE_URL}/blynk/delete-device`, {
        method: "DELETE",
        headers
      });
    } catch (e) {
      console.warn("Backend delete skipped:", e);
    }

    // Reset all frontend state
    setHasDevice(false);
    setCheckingDevice(false);
    setSensorData({});
    setLoading(false);
    setError(null);
    setTokenInput("");
    setDeviceNameInput("");
  };

  // Reset device state when the signed-in user changes.
  useEffect(() => {
    if (!user) {
      setHasDevice(false);
      setCheckingDevice(false);
      return;
    }
    setSensorData({});
    setLastUpdated(null);
    setLoading(true);
    setError(null);
    setTokenInput("");
    setDeviceNameInput("");
    setCheckingDevice(true);
  }, [user]);

  // Check if farmer already has a Blynk device registered
  useEffect(() => {
    const checkDevice = async () => {
      try {
        // Get auth token from localStorage
        const token = localStorage.getItem('access_token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

        const res = await fetch(`${API_BASE_URL}/blynk/check-device`, { headers });
        const contentType = res.headers.get('content-type') || '';
        if (res.ok && contentType.includes('application/json')) {
          const data = await res.json();
          if (!data.blynk_required && data.device) {
            setHasDevice(true);
          } else {
            setHasDevice(false);
          }
        } else {
          setHasDevice(false);
        }
      } catch {
        setHasDevice(false);
      } finally {
        setCheckingDevice(false);
      }
    };
    checkDevice();
  }, [user]);

  // Read the canonical telemetry endpoint. The backend polls Blynk with the
  // token stored at device registration, normalises the nine parameters and
  // persists them, so this page and Soil & Sensors always agree.
  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const response = await fetch(`${API_BASE_URL}/blynk/telemetry/live`, { headers });
      if (!response.ok) {
        throw new Error(`Telemetry request failed with status ${response.status}`);
      }
      const json = await response.json();

      if (!json.connected) {
        setHasDevice(false);
        setSensorData({});
        setError(null);
        return;
      }

      if (!json.has_data || !json.data) {
        setSensorData({});
        setError(json.message || "Device connected. Waiting for the first sensor reading.");
        return;
      }

      // Map the canonical field names back onto the virtual pins this page
      // renders. A missing value stays undefined so it renders as "--" rather
      // than a misleading 0.
      const d = json.data;
      const byPin = {};
      Object.entries(FIELD_BY_PIN).forEach(([pin, field]) => {
        if (d[field] !== null && d[field] !== undefined) byPin[pin] = d[field];
      });

      setSensorData(byPin);
      setLastUpdated(d.recorded_at || null);
      setError(
        json.status === "stale"
          ? "Showing the most recent stored reading; the device is not responding right now."
          : null
      );
    } catch (err) {
      console.error("Error fetching sensor data:", err);
      setError("Live sensor data is temporarily unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!hasDevice) return;
    fetchData();
    // The backend caches a Blynk poll for ~15s, so a 10s cadence here stays
    // live without hammering either the backend or the Blynk API.
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData, hasDevice]);

  // Handle token registration
  const handleRegisterDevice = async (e) => {
    e.preventDefault();
    if (!tokenInput.trim()) {
      setRegisterError("Please enter your Blynk Auth Token");
      return;
    }

    setIsRegistering(true);
    setRegisterError(null);

    try {
      // Get auth token from localStorage
      const token = localStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      };

      // Register with backend
      const res = await fetch(`${API_BASE_URL}/blynk/register-device`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          auth_token: tokenInput.trim(),
          device_name: deviceNameInput.trim() || "My Blynk Device",
        }),
      });

      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        throw new Error('Server unavailable. Please try again in a moment.');
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");

      // The token now lives only in the backend. Activate the dashboard and
      // let the next poll pull readings through the canonical endpoint.
      setTokenInput("");
      setHasDevice(true);
    } catch (err) {
      setRegisterError(err.message || "Failed to register device.");
    } finally {
      setIsRegistering(false);
    }
  };

  // ── Loading state ──
  if (checkingDevice) {
    return (
      <div className="hardware-iot-page">
        <div className="loading-state">Checking device status...</div>
      </div>
    );
  }

  // ── Onboarding: no token yet ──
  if (!hasDevice) {
    return (
      <div className="hardware-iot-page">
        <div className="hardware-iot-header">
          <div className="hardware-iot-header-left">
            <div className="hardware-iot-title">Live Farm Sensors</div>
            <div className="hardware-iot-subtitle">Connect your Blynk device to start monitoring.</div>
          </div>
          <div className="hardware-iot-status">
            <span className="status-indicator offline"></span>
            No Device
          </div>
        </div>

        <div className="blynk-setup-card">
          <div className="blynk-setup-icon">
            <Cpu size={28} />
            <Wifi size={18} className="blynk-wifi-pulse" />
          </div>
          <h3 className="blynk-setup-title">Connect Your Blynk Device</h3>
          <p className="blynk-setup-desc">
            Enter your Blynk Auth Token to activate real-time soil and weather monitoring from your IoT sensors.
          </p>

          <form onSubmit={handleRegisterDevice} className="blynk-setup-form">
            <div className="blynk-form-group">
              <label htmlFor="blynk-token-input">Blynk Auth Token <span className="blynk-required">*</span></label>
              <input
                id="blynk-token-input"
                type="text"
                placeholder="Enter your Blynk authentication token"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                disabled={isRegistering}
                autoFocus
              />
              <span className="blynk-form-hint">
                Find this in Blynk app → Device Settings → Auth Token
              </span>
            </div>

            <div className="blynk-form-group">
              <label htmlFor="blynk-device-name">Device Name <span className="blynk-optional">(optional)</span></label>
              <input
                id="blynk-device-name"
                type="text"
                placeholder="e.g. Field Sensor #1"
                value={deviceNameInput}
                onChange={(e) => setDeviceNameInput(e.target.value)}
                disabled={isRegistering}
              />
            </div>

            {registerError && (
              <div className="blynk-error">
                <AlertCircle size={14} />
                <span>{registerError}</span>
              </div>
            )}

            <button type="submit" className="blynk-submit-btn" disabled={isRegistering || !tokenInput.trim()}>
              {isRegistering ? (
                <><Loader2 className="blynk-spin" size={16} /><span>Connecting...</span></>
              ) : (
                <><Wifi size={16} /><span>Connect Device</span></>
              )}
            </button>
          </form>

          <div className="blynk-features">
            <span className="blynk-features-title">What you'll get:</span>
            <div className="blynk-features-grid">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}><ThermometerSun size={15} color="#10b981" /> Air temp & humidity</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}><Droplets size={15} color="#06b6d4" /> Soil moisture</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}><FlaskConical size={15} color="#a855f7" /> pH, EC, NPK</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}><BarChart3 size={15} color="#f59e0b" /> Historical trends</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── Dashboard: token exists, show sensors ──
  return (
    <div className="hardware-iot-page">
      <div className="hardware-iot-header">
        <div className="hardware-iot-header-left">
          <div className="hardware-iot-title">Live Farm Sensors</div>
          <div className="hardware-iot-subtitle">
            {lastUpdated
              ? `Last reading ${new Date(lastUpdated).toLocaleString()}`
              : "Real-time environmental and soil monitoring."}
          </div>
        </div>
        <div className="hardware-iot-header-right">
          <div className="hardware-iot-status">
            <span className={`status-indicator ${error ? "offline" : "online"}`}></span>
            {error ? "Offline" : "Live"}
          </div>
          <button className="blynk-delete-btn" onClick={handleDeleteDevice} title="Disconnect device">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {loading && !Object.keys(sensorData).length ? (
        <div className="loading-state">Loading sensor data...</div>
      ) : (
        <div className="sensors-grid">
          {SENSORS.map((sensor) =>
            (() => {
              const numeric = parseNumeric(sensorData[sensor.pin]);
              const percent = toPercent(sensor.pin, numeric);
              const display = numeric === null ? "--" : formatValue(numeric);
              return (
                <div
                  key={sensor.pin}
                  className="sensor-card"
                  style={{
                    "--accent": sensor.color,
                    "--gauge": `${percent}%`,
                  }}
                >
                  <div className="sensor-card-top">
                    <div className="sensor-label">{sensor.label}</div>
                  </div>

                  <div className="sensor-gauge" aria-label={`${sensor.label} gauge`}>
                    <div className="sensor-gauge-inner">
                      <div className="sensor-gauge-value">
                        {display}
                        <span className="sensor-unit">{sensor.unit}</span>
                      </div>
                      <div className="sensor-gauge-percent">{Math.round(percent)}%</div>
                    </div>
                  </div>
                </div>
              );
            })()
          )}
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}
