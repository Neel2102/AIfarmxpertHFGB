import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Save, User as UserIcon, Edit3, ShieldCheck, FileText, KeyRound, Activity } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Dashboard/SettingsPage.css';
import '../styles/Dashboard/MainDashboard-1.css';

const safeString = (v) => (typeof v === 'string' ? v : v == null ? '' : String(v));

const SettingsPage = () => {
  const navigate = useNavigate();
  const { user, updateProfile, logout } = useAuth();
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
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(initial);
  }, [initial]);

  const handleChange = (key) => (e) => {
    setForm((p) => ({ ...p, [key]: e.target.value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        ...(user || {}),
        name: form.name,
        email: form.email,
        phone: form.phone,
        location: form.location,
      };

      const res = await updateProfile(payload);
      if (!res?.success) {
        throw new Error(res?.error || 'Failed to update profile');
      }

      toast.success('Profile updated');
    } catch (e) {
      toast.error(e?.message || 'Profile update failed');
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

  const details = useMemo(() => {
    return [
      { label: 'Name', value: form.name || '—' },
      { label: 'Role', value: form.role || 'User' },
      { label: 'Email', value: form.email || '—' },
      { label: 'Contact', value: form.phone || '—' },
      { label: 'Location', value: form.location || '—' },
      { label: 'Status', value: 'Active', tone: 'good' },
    ];
  }, [form.email, form.location, form.name, form.phone, form.role]);

  const tabs = useMemo(() => {
    return [
      { id: 'profile', label: 'Profile', icon: UserIcon },
      { id: 'edit', label: 'Edit Profile', icon: Edit3 },
      { id: 'phone', label: 'Phone Verification', icon: ShieldCheck },
      { id: 'id', label: 'ID Verification', icon: FileText },
      { id: 'password', label: 'Reset Password', icon: KeyRound },
      { id: 'activity', label: 'Activity Log', icon: Activity },
    ];
  }, []);

  return (
    <div className="main-dashboard-layout">
      <div className="main-dashboard-content-1">
        <div className="settings-page">
          <div className="settings-hero">
            <div className="settings-hero-inner">
              <div>
                <div className="settings-kicker">My Profile</div>
                <div className="settings-title">Settings</div>
                <div className="settings-subtitle">Manage your profile information and account settings</div>
              </div>
              <button className="settings-logout" onClick={handleLogout} type="button">
                <LogOut size={16} />
                Logout
              </button>
            </div>
          </div>

          <div className="settings-shell">
            <div className="settings-tabs">
              {tabs.map((t) => {
                const Icon = t.icon;
                return (
                  <button
                    key={t.id}
                    type="button"
                    className={`settings-tab ${activeTab === t.id ? 'active' : ''}`}
                    onClick={() => setActiveTab(t.id)}
                  >
                    <Icon size={16} />
                    {t.label}
                  </button>
                );
              })}
            </div>

            <div className="settings-card settings-profile-card">
              <div className="settings-card-inner">
                <div className="settings-left">
                  <div className="settings-avatar-wrap">
                    <div className="settings-avatar">{initials}</div>
                  </div>
                  <div className="settings-user-name">{form.name || 'User'}</div>
                  <div className="settings-user-email">{form.email || '—'}</div>
                  <div className="settings-user-location">{form.location || '—'}</div>
                </div>

                <div className="settings-right">
                  {activeTab === 'edit' ? (
                    <div className="settings-form">
                      <div className="field">
                        <label className="field-label">Full name</label>
                        <input className="field-input" value={form.name} onChange={handleChange('name')} placeholder="Your name" />
                      </div>

                      <div className="field">
                        <label className="field-label">Email</label>
                        <input className="field-input" value={form.email} onChange={handleChange('email')} placeholder="name@example.com" />
                      </div>

                      <div className="field">
                        <label className="field-label">Phone</label>
                        <input className="field-input" value={form.phone} onChange={handleChange('phone')} placeholder="+91..." />
                      </div>

                      <div className="field">
                        <label className="field-label">Location</label>
                        <input className="field-input" value={form.location} onChange={handleChange('location')} placeholder="City, Country" />
                      </div>

                      <div className="form-actions">
                        <button className="settings-btn" type="button" onClick={() => setActiveTab('profile')}>Cancel</button>
                        <button className="settings-btn primary" type="button" onClick={handleSave} disabled={saving}>
                          <Save size={16} />
                          {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="settings-details">
                      {details.map((row) => (
                        <div key={row.label} className="settings-detail-row">
                          <div className="settings-detail-label">{row.label}</div>
                          <div className="settings-detail-sep">:</div>
                          <div className={`settings-detail-value ${row.tone ? `tone-${row.tone}` : ''}`}>{row.value}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Phone Verification Tab - Outside profile card */}
            {activeTab === 'phone' && (
              <div className="phone-verification">
                <h2>Phone Verification</h2>
                <div className="phone-form">
                  <div className="phone-input-group">
                    <input type="tel" placeholder="Enter your phone number" />
                    <button className="verify-btn">Send Code</button>
                  </div>
                  
                  <div className="otp-section">
                    <p>Enter 6-digit code sent to your phone</p>
                    <div className="otp-inputs">
                      <input type="text" maxLength="1" />
                      <input type="text" maxLength="1" />
                      <input type="text" maxLength="1" />
                      <input type="text" maxLength="1" />
                      <input type="text" maxLength="1" />
                      <input type="text" maxLength="1" />
                    </div>
                    <button className="verify-btn">Verify Phone</button>
                  </div>
                </div>
              </div>
            )}
            
            {/* ID Verification Tab - Outside profile card */}
            {activeTab === 'id' && (
              <div className="id-verification">
                <h2>ID Verification</h2>
                
                <div className="hardware-id-section">
                  <h3>Hardware ID Verification</h3>
                  <p>Your unique hardware identifier for secure access:</p>
                  <div className="hardware-id-display">
                    HW-ID: A1B2-C3D4-E5F6-G7H8-I9J0
                  </div>
                  <button className="verify-btn">Verify Hardware ID</button>
                </div>
                
                <div className="id-upload-area">
                  <h3>Upload ID Document</h3>
                  <p>Click to upload or drag and drop</p>
                  <p>PDF, JPG, PNG (max. 5MB)</p>
                  <button className="upload-btn">Choose File</button>
                </div>
              </div>
            )}
            
            {/* Reset Password Tab - Outside profile card */}
            {activeTab === 'password' && (
              <div className="reset-password">
                <h2>Reset Password</h2>
                <div className="password-form">
                  <input type="password" className="password-input" placeholder="Current Password" />
                  <input type="password" className="password-input" placeholder="New Password" />
                  <div className="password-strength weak"></div>
                  <input type="password" className="password-input" placeholder="Confirm New Password" />
                  <button className="verify-btn">Update Password</button>
                </div>
              </div>
            )}
            
            {/* Activity Log Tab - Outside profile card */}
            {activeTab === 'activity' && (
              <div className="activity-log">
                <h2>Activity Log</h2>
                
                <div className="activity-filters">
                  <button className="filter-btn active">All</button>
                  <button className="filter-btn">Login</button>
                  <button className="filter-btn">Profile Updates</button>
                  <button className="filter-btn">Security</button>
                </div>
                
                <div className="activity-list">
                  <div className="activity-item">
                    <div className="activity-icon">L</div>
                    <div className="activity-details">
                      <h4>Login Successful</h4>
                      <p>Logged in from Chrome on Windows</p>
                    </div>
                    <div className="activity-time">2 hours ago</div>
                  </div>
                  
                  <div className="activity-item">
                    <div className="activity-icon">P</div>
                    <div className="activity-details">
                      <h4>Profile Updated</h4>
                      <p>Changed phone number and location</p>
                    </div>
                    <div className="activity-time">1 day ago</div>
                  </div>
                  
                  <div className="activity-item">
                    <div className="activity-icon">S</div>
                    <div className="activity-details">
                      <h4>Security Check</h4>
                      <p>Hardware ID verification completed</p>
                    </div>
                    <div className="activity-time">3 days ago</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
