import React, { useEffect, useState } from "react";
import { Cpu, Wifi, CheckCircle, AlertCircle, Loader2, Trash2 } from "lucide-react";
import "../styles/Dashboard/HardwareIoT.css";

const BLYNK_CLOUD_URL = "https://blr1.blynk.cloud/external/api/get";
const API_BASE_URL = process.env.REACT_APP_API_URL || "";

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

const SENSOR_RANGES = {
  V0: { min: 0, max: 50 },
  V1: { min: 0, max: 100 },
  V2: { min: 0, max: 100 },
  V3: { min: 0, max: 50 },
  V4: { min: 0, max: 5000 },
  V5: { min: 0, max: 14 },
  V6: { min: 0, max: 200 },
  V7: { min: 0, max: 200 },
  V8: { min: 0, max: 200 },
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
  // Token state — check localStorage first, then API
  const [blynkToken, setBlynkToken] = useState(() => localStorage.getItem("blynk_token") || "");
  const [hasDevice, setHasDevice] = useState(!!localStorage.getItem("blynk_token"));
  const [checkingDevice, setCheckingDevice] = useState(true);

  // Onboarding form state
  const [tokenInput, setTokenInput] = useState("");
  const [deviceNameInput, setDeviceNameInput] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [registerError, setRegisterError] = useState(null);

  // Sensor dashboard state
  const [sensorData, setSensorData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Delete / disconnect current Blynk device
  const handleDeleteDevice = async () => {
    if (!window.confirm("Disconnect this Blynk device? You can add a new one after.")) return;

    // Delete from backend DB
    try {
      await fetch(`${API_BASE_URL}/api/blynk/delete-device`, { method: "DELETE" });
    } catch (e) {
      console.warn("Backend delete skipped:", e);
    }

    // Reset all frontend state
    localStorage.removeItem("blynk_token");
    setBlynkToken("");
    setHasDevice(false);
    setCheckingDevice(false);
    setSensorData({});
    setLoading(false);
    setError(null);
    setTokenInput("");
    setDeviceNameInput("");
  };

  // Check if farmer already has a Blynk device registered
  useEffect(() => {
    const checkDevice = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/blynk/check-device`);
        const contentType = res.headers.get('content-type') || '';
        if (res.ok && contentType.includes('application/json')) {
          const data = await res.json();
          if (!data.blynk_required && data.device) {
            setHasDevice(true);
          } else if (!blynkToken) {
            setHasDevice(false);
          }
        } else if (!blynkToken) {
          setHasDevice(false);
        }
      } catch {
        // If API fails but we have a local token, still show dashboard
        if (blynkToken) setHasDevice(true);
      } finally {
        setCheckingDevice(false);
      }
    };
    checkDevice();
  }, [blynkToken]);

  // Fetch sensor data when we have a token
  const fetchData = async () => {
    if (!blynkToken) return;
    try {
      const baseUrl = `${BLYNK_CLOUD_URL}?token=${blynkToken}`;
      const promises = SENSORS.map(async (sensor) => {
        const response = await fetch(`${baseUrl}&${sensor.pin}`);
        if (!response.ok) throw new Error(`Failed to fetch ${sensor.label}`);
        const value = await response.text();
        return { [sensor.pin]: value };
      });

      const results = await Promise.all(promises);
      const newData = results.reduce((acc, curr) => ({ ...acc, ...curr }), {});
      setSensorData(newData);
      setLoading(false);
      setError(null);

      // Auto-save to soil_tests table (every fetch cycle)
      try {
        await fetch(`${API_BASE_URL}/api/soil-tests/save`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            air_temperature: parseNumeric(newData.V0),
            air_humidity: parseNumeric(newData.V1),
            soil_moisture: parseNumeric(newData.V2),
            soil_temperature: parseNumeric(newData.V3),
            soil_ec: parseNumeric(newData.V4),
            soil_ph: parseNumeric(newData.V5),
            nitrogen: parseNumeric(newData.V6),
            phosphorus: parseNumeric(newData.V7),
            potassium: parseNumeric(newData.V8),
            source: "blynk",
          }),
        });
      } catch (saveErr) {
        console.warn("Auto-save to soil_tests skipped:", saveErr);
      }
    } catch (err) {
      console.error("Error fetching sensor data:", err);
      setError("Failed to fetch sensor data. Please check connection.");
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!hasDevice || !blynkToken) return;
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [hasDevice, blynkToken]);

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
      // Register with backend
      const res = await fetch(`${API_BASE_URL}/api/blynk/register-device`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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

      // Save token locally and activate dashboard
      localStorage.setItem("blynk_token", tokenInput.trim());
      setBlynkToken(tokenInput.trim());
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
              <span>🌡️ Air temp & humidity</span>
              <span>💧 Soil moisture</span>
              <span>🧪 pH, EC, NPK</span>
              <span>📊 Historical trends</span>
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
          <div className="hardware-iot-subtitle">Real-time environmental and soil monitoring.</div>
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
