import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  LogOut, Save, User as UserIcon,
  ShieldCheck, KeyRound, Activity,
  Sprout, Droplets, Truck
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth, FARM_PROFILE_UPDATED } from '../contexts/AuthContext';
import '../styles/Dashboard/SettingsPage.css';

const safeString = (v) => (typeof v === 'string' ? v : v == null ? '' : String(v));

const SettingsPage = () => {
  const navigate = useNavigate();
  const { user, updateProfile, logout, fetchFarmProfile, updateFarmProfile } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');

  const initial = useMemo(() => {
    const u = user || {};
    return {
      name: safeString(u.name || u.full_name || u.username || ''),
      email: safeString(u.email || ''),
      phone: safeString(u.phone || u.mobile || ''),
      location: safeString(u.location || ''),
      role: safeString(u.role || 'User'),
    };
  }, [user]);

  const [form, setForm] = useState(initial);
  const [farmData, setFarmData] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loadingFarm, setLoadingFarm] = useState(false);

  useEffect(() => {
    setForm(initial);
  }, [initial]);

  useEffect(() => {
    const loadFarm = async () => {
      setLoadingFarm(true);
      try {
        const data = await fetchFarmProfile();
        // Fall back to an empty object so a farmer who has never saved a farm
        // can still fill the form in — previously farmData stayed null and the
        // save silently skipped the farm entirely.
        setFarmData(data || {});
      } finally {
        setLoadingFarm(false);
      }
    };
    loadFarm();

    // Pick up a farm saved elsewhere (e.g. from the Farm Map).
    const onFarmUpdated = (e) => { if (e.detail) setFarmData(e.detail); };
    window.addEventListener(FARM_PROFILE_UPDATED, onFarmUpdated);
    return () => window.removeEventListener(FARM_PROFILE_UPDATED, onFarmUpdated);
  }, [fetchFarmProfile]);

  const handleChange = (key) => (e) => {
    setForm((p) => ({ ...p, [key]: e.target.value }));
  };

  const handleFarmChange = (key) => (e) => {
    const raw = e.target.value;
    // latitude/longitude are numeric columns — send a number, or null when the
    // field is cleared, rather than an empty string.
    const value = (key === 'latitude' || key === 'longitude')
      ? (raw === '' ? null : Number(raw))
      : raw;
    setFarmData(p => ({ ...(p || {}), [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        full_name: form.name,
        name: form.name,
        email: form.email,
        phone: form.phone,
        location: form.location,
      };

      const res = await updateProfile(payload);
      if (!res?.success) throw new Error(res?.error || 'Failed to update profile');

      if (farmData) {
        const farmRes = await updateFarmProfile(farmData);
        if (!farmRes?.success) throw new Error(farmRes?.error || 'Failed to update farm profile');
        // Replace the form with what the database actually stored, so the UI
        // can never show a value the backend rejected or normalised.
        if (farmRes.data) setFarmData(farmRes.data);
      }

      toast.success('Settings updated successfully!');
    } catch (e) {
      toast.error(e?.message || 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      navigate('/login');
    }
  };

  const initials = useMemo(() => {
    const n = safeString(form.name || '').trim();
    if (!n) return 'U';
    const parts = n.split(/\s+/).filter(Boolean);
    const a = parts[0]?.[0] || 'U';
    const b = parts.length > 1 ? parts[parts.length - 1]?.[0] : '';
    return (a + b).toUpperCase();
  }, [form.name]);

  const tabs = useMemo(() => [
    { id: 'profile', label: 'Profile', icon: UserIcon },
    { id: 'farm', label: 'Farm Profile', icon: Sprout },
    { id: 'security', label: 'Security', icon: ShieldCheck },
    { id: 'activity', label: 'Activity', icon: Activity },
  ], []);

  return (
    <div className="settings-page-container">
      {/* ── Top User Profile HUD Card ── */}
      <div className="settings-top-card">
        <div className="settings-top-user">
          <div className="avatar-large">{initials}</div>
          <div className="settings-top-meta">
            <h2>{form.name || 'Farmer'}</h2>
            <p>{user?.email || 'farmer@farmxpert.ai'}</p>
            <span className="settings-badge">{user?.role || 'Verified Farmer'}</span>
          </div>
        </div>

        <div className="settings-top-actions">
          <button className="save-btn" onClick={handleSave} disabled={saving}>
            <Save size={18} />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button className="nav-item-logout" onClick={handleLogout} title="Sign Out">
            <LogOut size={18} />
            Sign Out
          </button>
        </div>
      </div>

      {/* ── Horizontal Navigation Tabs ── */}
      <div className="settings-tabs-bar">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`settings-tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            <t.icon size={18} />
            <span>{t.label}</span>
          </button>
        ))}
      </div>

      {/* ── Main Tab Content ── */}
      <div className="settings-main-content">
        <header className="content-header">
          <div>
            <h1>{tabs.find(t => t.id === activeTab)?.label}</h1>
            <p>Manage your account preferences, farm parameters, and security</p>
          </div>
        </header>

        <div className="content-shell">
          {activeTab === 'profile' && (
            <div className="settings-form-grid">
              <div className="form-card">
                <h3>Personal Information</h3>
                <div className="input-group">
                  <label>Full Name</label>
                  <input value={form.name} onChange={handleChange('name')} placeholder="Your Name" />
                </div>
                <div className="input-group">
                  <label>Email Address</label>
                  <input value={form.email} onChange={handleChange('email')} placeholder="email@example.com" />
                </div>
                <div className="input-group">
                  <label>Phone Number</label>
                  <input value={form.phone} onChange={handleChange('phone')} placeholder="+91..." />
                </div>
                <div className="input-group">
                  <label>Location</label>
                  <input value={form.location} onChange={handleChange('location')} placeholder="City, State" />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'farm' && (
            <div className="settings-form-grid">
              {loadingFarm ? (
                <div className="loading-state">Loading farm data...</div>
              ) : (
                <>
                  <div className="form-card">
                    <h3><Sprout size={18} /> Farm Details</h3>
                    <div className="input-group">
                      <label>Farm Name</label>
                      <input value={farmData?.farm_name || ''} onChange={handleFarmChange('farm_name')} placeholder="Green Acres" />
                    </div>
                    <div className="input-row">
                      <div className="input-group">
                        <label>Farm Size (Acres)</label>
                        <input value={farmData?.farm_size || ''} onChange={handleFarmChange('farm_size')} type="number" />
                      </div>
                      <div className="input-group">
                        <label>Soil Type</label>
                        <select value={farmData?.soil_type || ''} onChange={handleFarmChange('soil_type')}>
                          <option value="">Select soil type</option>
                          <option value="Loamy">Loamy</option>
                          <option value="Silty">Silty</option>
                          <option value="Clay">Clay</option>
                          <option value="Sandy">Sandy</option>
                          <option value="Black Soil">Black Soil</option>
                          <option value="Red Soil">Red Soil</option>
                          <option value="Alluvial">Alluvial</option>
                        </select>
                      </div>
                    </div>
                    {/* Crop and location were missing from this form even though
                        the dashboard tells the farmer to set them here, and the
                        season planner, Farm Map and weather all depend on them. */}
                    <div className="input-group">
                      <label>Current Crop</label>
                      <input
                        value={farmData?.crop_type || farmData?.specific_crop || ''}
                        onChange={handleFarmChange('crop_type')}
                        placeholder="e.g. Wheat, Cotton, Rice"
                      />
                    </div>
                    <div className="input-group">
                      <label>Farm Location</label>
                      <input
                        value={farmData?.location || ''}
                        onChange={handleFarmChange('location')}
                        placeholder="Village, District, State"
                      />
                    </div>
                    <div className="input-row">
                      <div className="input-group">
                        <label>Latitude</label>
                        <input
                          value={farmData?.latitude ?? ''}
                          onChange={handleFarmChange('latitude')}
                          type="number"
                          step="any"
                          placeholder="22.3039"
                        />
                      </div>
                      <div className="input-group">
                        <label>Longitude</label>
                        <input
                          value={farmData?.longitude ?? ''}
                          onChange={handleFarmChange('longitude')}
                          type="number"
                          step="any"
                          placeholder="70.8022"
                        />
                      </div>
                    </div>
                    <p className="input-hint" style={{ fontSize: '0.78rem', opacity: 0.7, marginTop: '4px' }}>
                      Coordinates are used for weather and field alerts. You can also set them
                      by drawing your boundary on the Farm Map.
                    </p>
                  </div>

                  <div className="form-card">
                    <h3><Droplets size={18} /> Resources</h3>
                    <div className="input-group">
                      <label>Water Source</label>
                      <input value={farmData?.water_source || ''} onChange={handleFarmChange('water_source')} />
                    </div>
                    <div className="input-group">
                      <label>Irrigation Method</label>
                      <input value={farmData?.irrigation_method || ''} onChange={handleFarmChange('irrigation_method')} />
                    </div>
                  </div>

                  <div className="form-card">
                    <h3><Truck size={18} /> Machinery & Labor</h3>
                    <div className="input-group">
                      <label>Labor Setup</label>
                      <input value={farmData?.labor_setup || ''} onChange={handleFarmChange('labor_setup')} />
                    </div>
                    <div className="input-group">
                      <label>Tech Comfort</label>
                      <select value={farmData?.tech_comfort || ''} onChange={handleFarmChange('tech_comfort')}>
                        <option value="New to Tech">New to Tech</option>
                        <option value="Interested">Interested</option>
                        <option value="Tech Savvy">Tech Savvy</option>
                      </select>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === 'security' && (
            <div className="settings-form-grid">
              <div className="form-card">
                <h3><KeyRound size={18} /> Password Reset</h3>
                <p className="card-hint">Manage your login security</p>
                <div className="input-group">
                  <label>Current Password</label>
                  <input type="password" placeholder="••••••••" />
                </div>
                <div className="input-group">
                  <label>New Password</label>
                  <input type="password" placeholder="••••••••" />
                </div>
              </div>
              <div className="form-card gray">
                <h3><ShieldCheck size={18} /> Identity Verification</h3>
                <p>Verify your account for enhanced security features.</p>
                <button className="secondary-btn">Start Verification</button>
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div className="activity-list-modern">
              <div className="activity-item-compact">
                <Activity size={16} />
                <div className="activity-info">
                  <h4>Profile Updated</h4>
                  <span>Today, 10:45 AM</span>
                </div>
              </div>
              <div className="activity-item-compact">
                <LogOut size={16} />
                <div className="activity-info">
                  <h4>Login Successful</h4>
                  <span>Yesterday, 04:20 PM</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
