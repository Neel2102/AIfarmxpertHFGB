import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  LogOut, Save, User as UserIcon, Edit3, 
  ShieldCheck, FileText, KeyRound, Activity, 
  Sprout, Droplets, Truck, Target, Cpu 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
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
      const data = await fetchFarmProfile();
      if (data) setFarmData(data);
      setLoadingFarm(false);
    };
    loadFarm();
  }, [fetchFarmProfile]);

  const handleChange = (key) => (e) => {
    setForm((p) => ({ ...p, [key]: e.target.value }));
  };

  const handleFarmChange = (key) => (e) => {
    setFarmData(p => ({ ...p, [key]: e.target.value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        full_name: form.name,
        name: form.name,
        email: form.email,
        phone: form.phone,
      };

      const res = await updateProfile(payload);
      if (!res?.success) throw new Error(res?.error || 'Failed to update profile');

      if (farmData) {
        const farmRes = await updateFarmProfile(farmData);
        if (!farmRes?.success) throw new Error(farmRes?.error || 'Failed to update farm profile');
      }

      toast.success('Settings updated successfully!');
    } catch (e) {
      toast.error(e?.message || 'Update failed');
    } finally {
      setSaving(true); 
      setTimeout(() => setSaving(false), 1000);
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
      <div className="settings-sidebar">
        <div className="sidebar-header">
          <div className="avatar-large">{initials}</div>
          <h3>{form.name}</h3>
          <p>{user?.email}</p>
        </div>
        <nav className="sidebar-nav">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`nav-item ${activeTab === t.id ? 'active' : ''}`}
              onClick={() => setActiveTab(t.id)}
            >
              <t.icon size={18} />
              {t.label}
            </button>
          ))}
        </nav>
        <button className="nav-item-logout" onClick={handleLogout}>
          <LogOut size={18} />
          Sign Out
        </button>
      </div>

      <div className="settings-main-content">
        <header className="content-header">
          <div>
            <h1>{tabs.find(t => t.id === activeTab)?.label}</h1>
            <p>Manage your account preferences and information</p>
          </div>
          <button className="save-btn" onClick={handleSave} disabled={saving}>
            <Save size={18} />
            {saving ? 'Saved' : 'Save Changes'}
          </button>
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
                  <input value={form.email} onChange={handleChange('email')} disabled />
                </div>
                <div className="input-group">
                  <label>Phone Number</label>
                  <input value={form.phone} onChange={handleChange('phone')} placeholder="+91..." />
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
                          <option value="Loamy">Loamy</option>
                          <option value="Silty">Silty</option>
                          <option value="Clay">Clay</option>
                          <option value="Sandy">Sandy</option>
                        </select>
                      </div>
                    </div>
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
