import React, { useState, useEffect } from 'react';
import { User, Phone, MapPin, Calendar, Edit, Save, X, Shield, FileText, Key, Activity } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import '../styles/Dashboard/Profile/profile.css';

const Profile = () => {
  const { user, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [saving, setSaving] = useState(false);

  // Initialize with user data from context
  const [profileData, setProfileData] = useState({
    name: user?.full_name || user?.name || 'Krishna Patel',
    email: user?.email || 'krishna.p@farmxpert.ai',
    phone: user?.phone || '+91 98765 43210',
    location: user?.location || 'Ahmedabad, Gujarat',
    joinDate: 'Joined March 2024',
    farmingType: 'Organic Cotton & Wheat',
    experience: '12 Years',
    preferredLanguage: 'Gujarati / English'
  });

  const [editData, setEditData] = useState(profileData);

  useEffect(() => {
    if (user) {
      const newData = {
        ...profileData,
        name: user.full_name || user.name || profileData.name,
        email: user.email || profileData.email,
        phone: user.phone || profileData.phone,
      };
      setProfileData(newData);
      setEditData(newData);
    }
  }, [user]);

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'edit', label: 'Edit Profile', icon: Edit },
    { id: 'phone', label: 'Phone Verification', icon: Phone },
    { id: 'id', label: 'ID Verification', icon: FileText },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'activity', label: 'Activity Log', icon: Activity }
  ];

  // eslint-disable-next-line no-unused-vars
  const handleEdit = () => {
    setEditData(profileData);
    setIsEditing(true);
    setActiveTab('edit');
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await updateProfile({
        name: editData.name,
        email: editData.email,
        phone: editData.phone,
        location: editData.location,
      });

      if (res.success) {
        setProfileData(editData);
        setIsEditing(false);
        setActiveTab('profile');
        toast.success('Profile updated successfully!');
      } else {
        toast.error(res.error || 'Failed to update profile');
      }
    } catch (error) {
      toast.error('An unexpected error occurred');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditData(profileData);
    setIsEditing(false);
    setActiveTab('profile');
  };

  // Inject heading into header-left
  useEffect(() => {
    const headerLeft = document.querySelector('.header-left');
    if (headerLeft) {
      headerLeft.innerHTML = `
        <div className="page-header">
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Manage your profile information and account settings</p>
        </div>
      `;
    }

    return () => {
      // Cleanup on unmount
      const headerLeft = document.querySelector('.header-left');
      if (headerLeft) {
        headerLeft.innerHTML = '';
      }
    };
  }, []);

  const handleInputChange = (field, value) => {
    setEditData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  useEffect(() => {
    if (!isEditing) {
      setEditData(profileData);
    }
  }, [profileData, isEditing]);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="profile-content">
            <div className="profile-left">
              <div className="profile-avatar">
                <User size={64} strokeWidth={2} />
              </div>
              <div className="profile-basic-info">
                <h2 className="profile-name">{profileData.name}</h2>
                <p className="profile-email">{profileData.email}</p>
                <p className="profile-location">
                  <MapPin size={16} />
                  {profileData.location}
                </p>
              </div>
            </div>
            <div className="profile-right">
              <div className="profile-details">
                <div className="detail-row">
                  <span className="detail-label">Name:</span>
                  <span className="detail-value">{profileData.name}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Role:</span>
                  <span className="detail-value">{profileData.role}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Email:</span>
                  <span className="detail-value">{profileData.email}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Email verification:</span>
                  <span className="detail-value status-pending">{profileData.emailVerification}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Contact:</span>
                  <span className="detail-value">{profileData.phone}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Mobile verification:</span>
                  <span className="detail-value status-active">{profileData.mobileVerification}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Status:</span>
                  <span className="detail-value status-active">{profileData.status}</span>
                </div>
              </div>
            </div>
          </div>
        );

      case 'edit':
        return (
          <div className="edit-content">
            <div className="edit-form">
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={editData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={editData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input
                  type="tel"
                  value={editData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Location</label>
                <input
                  type="text"
                  value={editData.location}
                  onChange={(e) => handleInputChange('location', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Farm Size</label>
                <input
                  type="text"
                  value={editData.farmSize}
                  onChange={(e) => handleInputChange('farmSize', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Experience</label>
                <input
                  type="text"
                  value={editData.experience}
                  onChange={(e) => handleInputChange('experience', e.target.value)}
                  className="form-input"
                />
              </div>
              <div className="form-actions">
                <button onClick={handleSave} className="btn-save">
                  <Save size={18} />
                  Save Changes
                </button>
                <button onClick={handleCancel} className="btn-cancel">
                  <X size={18} />
                  Cancel
                </button>
              </div>
            </div>
          </div>
        );

      case 'phone':
        return (
          <div className="verification-content">
            <h3>Phone Verification</h3>
            <p>Verify your phone number to secure your account.</p>
            <div className="verification-status">
              <div className="status-item">
                <Phone size={20} />
                <span>{profileData.phone}</span>
                <span className="status-badge status-active">Verified</span>
              </div>
            </div>
          </div>
        );

      case 'id':
        return (
          <div className="verification-content">
            <h3>ID Verification</h3>
            <p>Upload your government-issued ID to verify your identity.</p>
            <div className="upload-area">
              <FileText size={48} />
              <p>Click to upload ID document</p>
            </div>
          </div>
        );

      case 'security':
        return (
          <div className="security-content">
            <h3>Security Settings</h3>
            <div className="security-options">
              <div className="security-item">
                <Key size={20} />
                <div>
                  <h4>Change Password</h4>
                  <p>Update your account password</p>
                </div>
                <button className="btn-secondary">Change</button>
              </div>
              <div className="security-item">
                <Shield size={20} />
                <div>
                  <h4>Two-Factor Authentication</h4>
                  <p>Add an extra layer of security</p>
                </div>
                <button className="btn-secondary">Enable</button>
              </div>
            </div>
          </div>
        );

      case 'activity':
        return (
          <div className="activity-content">
            <h3>Activity Log</h3>
            <div className="activity-list">
              <div className="activity-item">
                <Calendar size={16} />
                <span>Profile updated</span>
                <span className="activity-date">2 days ago</span>
              </div>
              <div className="activity-item">
                <Calendar size={16} />
                <span>Phone verified</span>
                <span className="activity-date">1 week ago</span>
              </div>
              <div className="activity-item">
                <Calendar size={16} />
                <span>Account created</span>
                <span className="activity-date">{profileData.joinDate}</span>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="container-profile">
      <div className="wrapper-profile">
        <div className="card-profile">
          <div className="tab-navigation">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                >
                  <Icon size={18} />
                  {tab.label}
                </button>
              );
            })}
          </div>

          <div className="tab-content">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;