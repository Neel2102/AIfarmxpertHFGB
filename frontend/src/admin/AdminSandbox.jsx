import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { 
  Users,
  Thermometer, 
  Droplets, 
  Gauge, 
  Zap, 
  Activity, 
  Beaker,
  Leaf,
  Sprout,
  Flower,
  Power,
  Cpu,
  Database,
  Send,
  ShieldAlert,
  ShieldCheck,
  Search,
  RefreshCw,
  Server,
  FileText,
  X,
  Download,
  HeartPulse,
  Sliders
} from 'lucide-react';
import styles from './AdminSandbox.module.css';

const API_BASE_URL = '/api';

const AdminSandbox = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [adminMe, setAdminMe] = useState(null);

  const storedUser = useMemo(() => {
    try {
      const raw = localStorage.getItem('user');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }, []);

  const isAdmin = ((storedUser?.role || '').toLowerCase() === 'admin');

  const [globalSearch, setGlobalSearch] = useState('');
  const [globalSearchOpen, setGlobalSearchOpen] = useState(false);
  const [globalSearchLoading, setGlobalSearchLoading] = useState(false);
  const [globalSearchItems, setGlobalSearchItems] = useState([]);

  const [selectedUserId, setSelectedUserId] = useState(null);
  const [userDrawerOpen, setUserDrawerOpen] = useState(false);
  const [userDrawerTab, setUserDrawerTab] = useState('profile');
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedUserFarms, setSelectedUserFarms] = useState({ items: [], total: 0, page: 1, page_size: 25 });
  const [selectedUserAudit, setSelectedUserAudit] = useState({ items: [], total: 0, page: 1, page_size: 50 });
  const [selectedUserAuditPage, setSelectedUserAuditPage] = useState(1);
  const [selectedUserDevices, setSelectedUserDevices] = useState({ items: [], total: 0, page: 1, page_size: 25 });
  const [selectedUserUsage, setSelectedUserUsage] = useState(null);
  const [selectedUserUsageBucket, setSelectedUserUsageBucket] = useState('day');

  const [usersPage, setUsersPage] = useState(1);
  const [usersQuery, setUsersQuery] = useState('');
  const [usersRole, setUsersRole] = useState('');
  const [usersOnlyActive, setUsersOnlyActive] = useState('');
  const [usersData, setUsersData] = useState({ items: [], total: 0, page: 1, page_size: 25 });

  const [auditPage, setAuditPage] = useState(1);
  const [auditData, setAuditData] = useState({ items: [], total: 0, page: 1, page_size: 50 });

  const [farmsPage, setFarmsPage] = useState(1);
  const [farmsQuery, setFarmsQuery] = useState('');
  const [farmsData, setFarmsData] = useState({ items: [], total: 0, page: 1, page_size: 25 });

  const [devicesData, setDevicesData] = useState({ items: [], total: 0, page: 1, page_size: 25 });

  const [aiPage, setAiPage] = useState(1);
  const [aiData, setAiData] = useState({ items: [], total: 0, page: 1, page_size: 25 });

  const [healthData, setHealthData] = useState(null);
  const [orchestratorStatus, setOrchestratorStatus] = useState(null);

  const [overridesPage, setOverridesPage] = useState(1);
  const [overridesFarmId, setOverridesFarmId] = useState('');
  const [overridesMetric, setOverridesMetric] = useState('');
  const [overridesActiveOnly, setOverridesActiveOnly] = useState(true);
  const [overridesData, setOverridesData] = useState({ items: [], total: 0, page: 1, page_size: 25 });
  const [overrideCreate, setOverrideCreate] = useState({ farm_id: '', device_id: '', metric: '', value: '', effective_to: '', reason: '' });

  const [isLiveMode, setIsLiveMode] = useState(false);
  const [isInjecting, setIsInjecting] = useState(false);
  const [totalTokens, setTotalTokens] = useState(0);
  const [agentLogs, setAgentLogs] = useState([]);

  // Sensor states
  const [sensorData, setSensorData] = useState({
    airTemperature: 25,
    airHumidity: 60,
    soilMoisture: 45,
    soilTemperature: 22,
    soilEC: 1.2,
    soilPH: 6.8,
    nitrogen: 40,
    phosphorus: 30,
    potassium: 35
  });

  // Sensor configuration
  const sensors = [
    { 
      key: 'airTemperature', 
      label: 'Air Temperature', 
      unit: '°C', 
      min: -10, 
      max: 50, 
      icon: Thermometer,
      color: '#ef4444'
    },
    { 
      key: 'airHumidity', 
      label: 'Air Humidity', 
      unit: '%', 
      min: 0, 
      max: 100, 
      icon: Droplets,
      color: '#3b82f6'
    },
    { 
      key: 'soilMoisture', 
      label: 'Soil Moisture', 
      unit: '%', 
      min: 0, 
      max: 100, 
      icon: Droplets,
      color: '#06b6d4'
    },
    { 
      key: 'soilTemperature', 
      label: 'Soil Temperature', 
      unit: '°C', 
      min: -5, 
      max: 45, 
      icon: Thermometer,
      color: '#f97316'
    },
    { 
      key: 'soilEC', 
      label: 'Soil EC', 
      unit: 'dS/m', 
      min: 0, 
      max: 5, 
      step: 0.1,
      icon: Zap,
      color: '#8b5cf6'
    },
    { 
      key: 'soilPH', 
      label: 'Soil pH', 
      unit: '', 
      min: 0, 
      max: 14, 
      step: 0.1,
      icon: Beaker,
      color: '#10b981'
    },
    { 
      key: 'nitrogen', 
      label: 'Nitrogen (N)', 
      unit: 'mg/kg', 
      min: 0, 
      max: 200, 
      icon: Leaf,
      color: '#22c55e'
    },
    { 
      key: 'phosphorus', 
      label: 'Phosphorus (P)', 
      unit: 'mg/kg', 
      min: 0, 
      max: 150, 
      icon: Sprout,
      color: '#f59e0b'
    },
    { 
      key: 'potassium', 
      label: 'Potassium (K)', 
      unit: 'mg/kg', 
      min: 0, 
      max: 200, 
      icon: Flower,
      color: '#ec4899'
    }
  ];

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('session_token') || localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    };
  }, []);

  const createOverride = async () => {
    const payload = {
      farm_id: Number(overrideCreate.farm_id),
      device_id: overrideCreate.device_id ? Number(overrideCreate.device_id) : null,
      metric: overrideCreate.metric,
      value: Number(overrideCreate.value),
      effective_to: overrideCreate.effective_to || null,
      reason: overrideCreate.reason || null,
    };
    const res = await fetch(`${API_BASE_URL}/admin/sensor-overrides`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail || body?.message || `Create failed: ${res.status}`);
    }
    toast.success('Override created');
    setOverrideCreate({ farm_id: '', device_id: '', metric: '', value: '', effective_to: '', reason: '' });
    await loadOverrides();
  };

  const expireOverride = async (id) => {
    const res = await fetch(`${API_BASE_URL}/admin/sensor-overrides/${id}/expire`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail || body?.message || `Expire failed: ${res.status}`);
    }
    toast.success('Override expired');
    await loadOverrides();
  };

  const fetchJson = useCallback(async (path) => {
    const res = await fetch(`${API_BASE_URL}${path}`, { headers: getAuthHeaders() });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const msg = body?.detail || body?.message || `Request failed: ${res.status}`;
      throw new Error(msg);
    }
    return res.json();
  }, [getAuthHeaders]);

  const loadHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      const data = await res.json().catch(() => null);
      setHealthData(data);
    } catch (e) {
      setHealthData(null);
    }
    try {
      const status = await fetchJson('/orchestrator/status');
      setOrchestratorStatus(status);
    } catch (e) {
      setOrchestratorStatus({ error: e?.message || 'Failed' });
    }
  }, [fetchJson]);

  const loadOverrides = useCallback(async () => {
    const params = new URLSearchParams();
    params.set('page', String(overridesPage));
    params.set('page_size', '25');
    params.set('active_only', overridesActiveOnly ? 'true' : 'false');
    if (overridesFarmId) params.set('farm_id', overridesFarmId);
    if (overridesMetric) params.set('metric', overridesMetric);
    const res = await fetchJson(`/admin/sensor-overrides?${params.toString()}`);
    setOverridesData(res);
  }, [fetchJson, overridesActiveOnly, overridesFarmId, overridesMetric, overridesPage]);

  const toCsv = (rows) => {
    if (!rows || rows.length === 0) return '';
    const headers = Array.from(
      rows.reduce((set, r) => {
        Object.keys(r || {}).forEach((k) => set.add(k));
        return set;
      }, new Set())
    );
    const esc = (v) => {
      if (v === null || v === undefined) return '';
      const s = String(v);
      if (s.includes('"') || s.includes(',') || s.includes('\n')) {
        return `"${s.replace(/"/g, '""')}"`;
      }
      return s;
    };
    return [headers.join(','), ...rows.map((r) => headers.map((h) => esc(r?.[h])).join(','))].join('\n');
  };

  const downloadCsv = (filename, csvText) => {
    const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const exportPaged = async ({ name, fetchPage, pageSize = 200, maxRows = 5000 }) => {
    let page = 1;
    let all = [];
    while (all.length < maxRows) {
      const res = await fetchPage({ page, page_size: pageSize });
      const items = res?.items || [];
      all = all.concat(items);
      if (items.length < pageSize) break;
      page += 1;
      if (page > 100) break;
    }
    const trimmed = all.slice(0, maxRows);
    const csv = toCsv(trimmed);
    downloadCsv(`${name}.csv`, csv);
    toast.success(`Exported ${trimmed.length} rows`);
  };

  const runGlobalSearch = useCallback(async (value) => {
    const q = value.trim();
    if (!q) {
      setGlobalSearchItems([]);
      return;
    }
    setGlobalSearchLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('q', q);
      params.set('limit', '8');
      const res = await fetchJson(`/admin/search?${params.toString()}`);
      setGlobalSearchItems(res?.items || []);
    } catch (e) {
      setGlobalSearchItems([]);
    } finally {
      setGlobalSearchLoading(false);
    }
  }, [fetchJson]);

  const onSelectSearchItem = (item) => {
    setGlobalSearchOpen(false);
    if (!item) return;
    if (item.kind === 'user') {
      setActiveTab('users');
      openUserDrawer(item.id);
      return;
    }
    if (item.kind === 'farm') {
      setActiveTab('farms');
      setFarmsQuery('');
      return;
    }
    if (item.kind === 'device') {
      setActiveTab('iot');
      return;
    }
    if (item.kind === 'interaction') {
      setActiveTab('ai');
    }
  };

  const refreshOverview = useCallback(async () => {
    if (!isAdmin) {
      setAdminMe(null);
      return;
    }
    try {
      setIsRefreshing(true);
      const me = await fetchJson('/admin/me');
      setAdminMe(me);
    } catch (e) {
      setAdminMe(null);
      toast.error(e?.message || 'Failed to load admin info');
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchJson, isAdmin]);

  const loadUsers = useCallback(async () => {
    const params = new URLSearchParams();
    params.set('page', String(usersPage));
    params.set('page_size', '25');
    if (usersQuery.trim()) params.set('q', usersQuery.trim());
    if (usersRole) params.set('role', usersRole);
    if (usersOnlyActive !== '') params.set('is_active', usersOnlyActive);

    const data = await fetchJson(`/admin/users?${params.toString()}`);
    setUsersData(data);
  }, [fetchJson, usersOnlyActive, usersPage, usersQuery, usersRole]);

  const suspendUser = async (userId) => {
    const reason = window.prompt('Suspend reason');
    if (!reason) return;

    const res = await fetch(`${API_BASE_URL}/admin/users/${userId}/suspend`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ reason })
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail || body?.message || `Suspend failed: ${res.status}`);
    }
    toast.success('User suspended');
    await loadUsers();
  };

  const unsuspendUser = async (userId) => {
    const res = await fetch(`${API_BASE_URL}/admin/users/${userId}/unsuspend`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail || body?.message || `Unsuspend failed: ${res.status}`);
    }
    toast.success('User re-activated');
    await loadUsers();
  };

  const loadAudit = useCallback(async () => {
    const params = new URLSearchParams();
    params.set('page', String(auditPage));
    params.set('page_size', '50');
    if (selectedUserId) {
      params.set('target_type', 'user');
      params.set('target_id', String(selectedUserId));
    }
    const data = await fetchJson(`/admin/audit/events?${params.toString()}`);
    setAuditData(data);
  }, [auditPage, fetchJson, selectedUserId]);

  const openUserDrawer = async (userId) => {
    try {
      setSelectedUserId(userId);
      setUserDrawerOpen(true);
      setUserDrawerTab('profile');
      setSelectedUser(null);
      setSelectedUserAuditPage(1);
      setSelectedUserUsageBucket('day');
      setSelectedUserUsage(null);

      const user = await fetchJson(`/admin/users/${userId}`);
      setSelectedUser(user);

      const farmsParams = new URLSearchParams();
      farmsParams.set('page', '1');
      farmsParams.set('page_size', '25');
      farmsParams.set('user_id', String(userId));
      const farms = await fetchJson(`/admin/farms?${farmsParams.toString()}`);
      setSelectedUserFarms(farms);

      const auditParams = new URLSearchParams();
      auditParams.set('page', '1');
      auditParams.set('page_size', '50');
      auditParams.set('target_type', 'user');
      auditParams.set('target_id', String(userId));
      const audit = await fetchJson(`/admin/audit/events?${auditParams.toString()}`);
      setSelectedUserAudit(audit);

      const deviceParams = new URLSearchParams();
      deviceParams.set('page', '1');
      deviceParams.set('page_size', '50');
      const devices = await fetchJson(`/admin/users/${userId}/iot/devices?${deviceParams.toString()}`);
      setSelectedUserDevices(devices);

      const usageParams = new URLSearchParams();
      usageParams.set('bucket', 'day');
      const usage = await fetchJson(`/admin/users/${userId}/usage/tokens?${usageParams.toString()}`);
      setSelectedUserUsage(usage);
    } catch (e) {
      toast.error(e?.message || 'Failed to load user details');
    }
  };

  const closeUserDrawer = () => {
    setUserDrawerOpen(false);
  };

  const loadSelectedUserAudit = useCallback(async () => {
    if (!selectedUserId) return;
    const auditParams = new URLSearchParams();
    auditParams.set('page', String(selectedUserAuditPage));
    auditParams.set('page_size', '50');
    auditParams.set('target_type', 'user');
    auditParams.set('target_id', String(selectedUserId));
    const audit = await fetchJson(`/api/admin/audit/events?${auditParams.toString()}`);
    setSelectedUserAudit(audit);
  }, [fetchJson, selectedUserAuditPage, selectedUserId]);

  const loadFarms = useCallback(async () => {
    const params = new URLSearchParams();
    params.set('page', String(farmsPage));
    params.set('page_size', '25');
    if (farmsQuery.trim()) params.set('q', farmsQuery.trim());
    const data = await fetchJson(`/admin/farms?${params.toString()}`);
    setFarmsData(data);
  }, [farmsPage, farmsQuery, fetchJson]);

  const loadDevices = useCallback(async () => {
    const params = new URLSearchParams();
    params.set('page', '1');
    params.set('page_size', '50');
    const data = await fetchJson(`/admin/iot/devices?${params.toString()}`);
    setDevicesData(data);
  }, [fetchJson]);

  const loadAiInteractions = useCallback(async () => {
    const params = new URLSearchParams();
    params.set('page', String(aiPage));
    params.set('page_size', '25');
    const data = await fetchJson(`/admin/ai/interactions?${params.toString()}`);
    setAiData(data);
  }, [aiPage, fetchJson]);

  // Poll agent activity from backend API
  const pollAgentActivity = useCallback(async () => {
    if (!isAdmin) return;
    try {
      const response = await fetch(`${API_BASE_URL}/admin/metrics`, { headers: getAuthHeaders() });
      if (response.ok) {
        const data = await response.json();
        
        // Transform API data to log format
        const newLogs = data.map(item => ({
          id: Date.now() + Math.random(), // Ensure unique IDs
          timestamp: new Date(item.timestamp).toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          }),
          message: `🤖 ${item.agent_name} consumed ${item.tokens_used} tokens...`,
          tokens: item.tokens_used
        }));

        // Update logs and total tokens
        setAgentLogs(prev => [...newLogs, ...prev].slice(0, 50));
        setTotalTokens(prev => prev + newLogs.reduce((sum, log) => sum + log.tokens, 0));
      }
    } catch (error) {
      console.error('Failed to poll agent activity:', error);
    }
  }, [getAuthHeaders, isAdmin]);

  // Poll for agent activity every 3 seconds
  useEffect(() => {
    const interval = setInterval(pollAgentActivity, 3000);
    pollAgentActivity();
    return () => clearInterval(interval);
  }, [pollAgentActivity]);

  useEffect(() => {
    refreshOverview();
  }, [refreshOverview]);

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers().catch((e) => toast.error(e?.message || 'Failed to load users'));
    }
  }, [activeTab, loadUsers, usersPage]);

  useEffect(() => {
    if (activeTab === 'audit') {
      loadAudit().catch((e) => toast.error(e?.message || 'Failed to load audit logs'));
    }
  }, [activeTab, auditPage, loadAudit, selectedUserId]);

  useEffect(() => {
    if (userDrawerOpen && userDrawerTab === 'audit') {
      loadSelectedUserAudit().catch((e) => toast.error(e?.message || 'Failed to load user audit logs'));
    }
  }, [loadSelectedUserAudit, selectedUserAuditPage, userDrawerOpen, userDrawerTab]);

  useEffect(() => {
    if (!userDrawerOpen) return;
    if (!selectedUserId) return;
    if (userDrawerTab !== 'usage') return;

    const usageParams = new URLSearchParams();
    usageParams.set('bucket', selectedUserUsageBucket);
    fetchJson(`/admin/users/${selectedUserId}/usage/tokens?${usageParams.toString()}`)
      .then(setSelectedUserUsage)
      .catch((e) => toast.error(e?.message || 'Failed to load token usage'));
  }, [fetchJson, selectedUserId, selectedUserUsageBucket, userDrawerOpen, userDrawerTab]);

  useEffect(() => {
    if (activeTab === 'farms') {
      loadFarms().catch((e) => toast.error(e?.message || 'Failed to load farms'));
    }
  }, [activeTab, farmsPage, loadFarms]);

  useEffect(() => {
    if (activeTab === 'iot') {
      loadDevices().catch((e) => toast.error(e?.message || 'Failed to load IoT devices'));
    }
  }, [activeTab, loadDevices]);

  useEffect(() => {
    if (activeTab === 'ai') {
      loadAiInteractions().catch((e) => toast.error(e?.message || 'Failed to load AI interactions'));
    }
  }, [activeTab, aiPage, loadAiInteractions]);

  useEffect(() => {
    if (activeTab === 'health') {
      loadHealth();
    }
  }, [activeTab, loadHealth]);

  useEffect(() => {
    if (activeTab === 'overrides') {
      loadOverrides().catch((e) => toast.error(e?.message || 'Failed to load overrides'));
    }
  }, [activeTab, loadOverrides, overridesPage]);

  const handleSensorChange = (key, value) => {
    setSensorData(prev => ({
      ...prev,
      [key]: parseFloat(value)
    }));
  };

  if (!isAdmin) {
    return (
      <div className={styles.adminSandbox}>
        <div className={styles.panel}>
          <div className={styles.emptyState}>Admin access required. Please login with an admin account.</div>
        </div>
      </div>
    );
  }

  const handleInjectData = async () => {
    setIsInjecting(true);
    
    const payload = {
      user_id: 1,
      sensor_data: sensorData,
      source: isLiveMode ? 'live_hardware' : 'simulator',
      timestamp: new Date().toISOString()
    };

    try {
      const response = await fetch(`${API_BASE_URL}/iot/inject`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Sensor data injected successfully:', data);
        toast.success('Sensor data injected successfully!');
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Failed to inject sensor data:', errorData);
        toast.error(errorData.message || 'Failed to inject sensor data');
      }
    } catch (error) {
      console.error('Error injecting sensor data:', error);
      toast.error('Network error: Failed to inject sensor data');
    } finally {
      setIsInjecting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={styles.adminSandbox}
    >
      <div className={styles.header}>
        <div className={styles.headerTopRow}>
          <div>
            <h1 className={styles.title}>God Mode Admin</h1>
            <p className={styles.subtitle}>Control plane for users, farms, IoT and AI activity</p>
          </div>

          <div className={styles.headerRight}>
            <div className={styles.globalSearchWrap}>
              <div className={styles.searchBox}>
                <Search size={16} />
                <input
                  value={globalSearch}
                  onChange={(e) => {
                    const v = e.target.value;
                    setGlobalSearch(v);
                    setGlobalSearchOpen(true);
                    runGlobalSearch(v);
                  }}
                  onFocus={() => setGlobalSearchOpen(true)}
                  onBlur={() => setTimeout(() => setGlobalSearchOpen(false), 150)}
                  placeholder="Search users/farms/devices/interactions"
                />
              </div>

              {globalSearchOpen && (globalSearchLoading || globalSearchItems.length > 0) && (
                <div className={styles.searchDropdown}>
                  {globalSearchLoading ? (
                    <div className={styles.searchItemMuted}>Searching...</div>
                  ) : (
                    globalSearchItems.map((it) => (
                      <button key={`${it.kind}-${it.id}`} className={styles.searchItem} onMouseDown={() => onSelectSearchItem(it)}>
                        <div className={styles.searchItemMain}>{it.label}</div>
                        <div className={styles.searchItemMeta}>{it.kind}</div>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>

            <button
              className={styles.refreshButton}
              onClick={refreshOverview}
              disabled={isRefreshing}
            >
              <RefreshCw size={16} />
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        <div className={styles.tabs}>
          <button className={`${styles.tab} ${activeTab === 'overview' ? styles.tabActive : ''}`} onClick={() => setActiveTab('overview')}>
            <Server size={16} />
            Overview
          </button>
          <button className={`${styles.tab} ${activeTab === 'users' ? styles.tabActive : ''}`} onClick={() => setActiveTab('users')}>
            <Users size={16} />
            Users
          </button>
          <button className={`${styles.tab} ${activeTab === 'farms' ? styles.tabActive : ''}`} onClick={() => setActiveTab('farms')}>
            <Gauge size={16} />
            Farms
          </button>
          <button className={`${styles.tab} ${activeTab === 'iot' ? styles.tabActive : ''}`} onClick={() => setActiveTab('iot')}>
            <Cpu size={16} />
            IoT Fleet
          </button>
          <button className={`${styles.tab} ${activeTab === 'ai' ? styles.tabActive : ''}`} onClick={() => setActiveTab('ai')}>
            <Activity size={16} />
            AI Interactions
          </button>
          <button className={`${styles.tab} ${activeTab === 'audit' ? styles.tabActive : ''}`} onClick={() => setActiveTab('audit')}>
            <FileText size={16} />
            Audit Log
          </button>
          <button className={`${styles.tab} ${activeTab === 'health' ? styles.tabActive : ''}`} onClick={() => setActiveTab('health')}>
            <HeartPulse size={16} />
            System Health
          </button>
          <button className={`${styles.tab} ${activeTab === 'overrides' ? styles.tabActive : ''}`} onClick={() => setActiveTab('overrides')}>
            <Sliders size={16} />
            Sensor Overrides
          </button>
          <button className={`${styles.tab} ${activeTab === 'sandbox' ? styles.tabActive : ''}`} onClick={() => setActiveTab('sandbox')}>
            <Zap size={16} />
            Sandbox
          </button>
        </div>
      </div>

      {activeTab === 'overview' && (
        <div className={styles.overviewGrid}>
          <div className={styles.panel}>
            <div className={styles.panelHeaderCompact}>
              <div className={styles.panelTitle}>
                <Server size={20} />
                Admin Session
              </div>
            </div>
            {adminMe ? (
              <div className={styles.kvGrid}>
                <div className={styles.kvRow}><span>User</span><span>{adminMe.username}</span></div>
                <div className={styles.kvRow}><span>Email</span><span>{adminMe.email}</span></div>
                <div className={styles.kvRow}><span>Role</span><span>{adminMe.role}</span></div>
                <div className={styles.kvRow}><span>Verified</span><span>{String(adminMe.is_verified)}</span></div>
                <div className={styles.kvRow}><span>Active</span><span>{String(adminMe.is_active)}</span></div>
              </div>
            ) : (
              <div className={styles.emptyState}>
                Unable to load `/api/admin/me`. Ensure you are logged in as an admin.
              </div>
            )}
          </div>

          <div className={styles.panel}>
            <div className={styles.panelHeaderCompact}>
              <div className={styles.panelTitle}>
                <Activity size={20} />
                Recent Token Usage
              </div>
              <div className={styles.tokenCounter}>
                <Database size={16} />
                Total Tokens Used: <span className={styles.tokenValue}>{totalTokens.toLocaleString()}</span>
              </div>
            </div>

            <div className={styles.terminal}>
              <div className={styles.terminalHeader}>
                <div className={styles.terminalButtons}>
                  <div className={`${styles.terminalButton} ${styles.red}`} />
                  <div className={`${styles.terminalButton} ${styles.yellow}`} />
                  <div className={`${styles.terminalButton} ${styles.green}`} />
                </div>
                <div className={styles.terminalTitle}>Live Agent Feed</div>
              </div>

              <div className={styles.terminalContent}>
                {agentLogs.length === 0 ? (
                  <div className={styles.terminalPlaceholder}>
                    <Power size={24} />
                    Waiting for agent activity...
                  </div>
                ) : (
                  <div className={styles.logContainer}>
                    {agentLogs.map((log) => (
                      <motion.div
                        key={log.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={styles.logEntry}
                      >
                        <span className={styles.logTimestamp}>[{log.timestamp}]</span>
                        <span className={styles.logMessage}>{log.message}</span>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'health' && (
        <div className={styles.overviewGrid}>
          <div className={styles.panel}>
            <div className={styles.panelHeaderCompact}>
              <div className={styles.panelTitle}>
                <HeartPulse size={20} />
                API Health
              </div>
              <button className={styles.refreshButtonSmall} onClick={loadHealth}>
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>
            <pre className={styles.jsonBox}>{JSON.stringify(healthData, null, 2)}</pre>
          </div>

          <div className={styles.panel}>
            <div className={styles.panelHeaderCompact}>
              <div className={styles.panelTitle}>
                <Server size={20} />
                Orchestrator Status
              </div>
              <button className={styles.refreshButtonSmall} onClick={loadHealth}>
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>
            <pre className={styles.jsonBox}>{JSON.stringify(orchestratorStatus, null, 2)}</pre>
          </div>
        </div>
      )}

      {activeTab === 'overrides' && (
        <div className={styles.panel}>
          <div className={styles.panelHeaderCompact}>
            <div className={styles.panelTitle}>
              <Sliders size={20} />
              Sensor Overrides
            </div>
            <div className={styles.headerActions}>
              <button className={styles.refreshButtonSmall} onClick={() => loadOverrides().catch((e) => toast.error(e?.message || 'Failed to load overrides'))}>
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>
          </div>

          <div className={styles.filtersRow}>
            <input className={styles.textInput} placeholder="farm_id" value={overridesFarmId} onChange={(e) => setOverridesFarmId(e.target.value)} />
            <input className={styles.textInput} placeholder="metric" value={overridesMetric} onChange={(e) => setOverridesMetric(e.target.value)} />
            <label className={styles.checkboxLabel}>
              <input type="checkbox" checked={overridesActiveOnly} onChange={(e) => setOverridesActiveOnly(e.target.checked)} />
              Active only
            </label>
            <button className={styles.primaryButton} onClick={() => { setOverridesPage(1); loadOverrides().catch((e) => toast.error(e?.message || 'Failed to load overrides')); }}>
              Apply
            </button>
          </div>

          <div className={styles.formGrid}>
            <input className={styles.textInput} placeholder="farm_id" value={overrideCreate.farm_id} onChange={(e) => setOverrideCreate((p) => ({ ...p, farm_id: e.target.value }))} />
            <input className={styles.textInput} placeholder="device_id (optional)" value={overrideCreate.device_id} onChange={(e) => setOverrideCreate((p) => ({ ...p, device_id: e.target.value }))} />
            <input className={styles.textInput} placeholder="metric (e.g. soil_moisture)" value={overrideCreate.metric} onChange={(e) => setOverrideCreate((p) => ({ ...p, metric: e.target.value }))} />
            <input className={styles.textInput} placeholder="value" value={overrideCreate.value} onChange={(e) => setOverrideCreate((p) => ({ ...p, value: e.target.value }))} />
            <input className={styles.textInput} placeholder="effective_to (ISO, optional)" value={overrideCreate.effective_to} onChange={(e) => setOverrideCreate((p) => ({ ...p, effective_to: e.target.value }))} />
            <input className={styles.textInput} placeholder="reason (optional)" value={overrideCreate.reason} onChange={(e) => setOverrideCreate((p) => ({ ...p, reason: e.target.value }))} />
            <button className={styles.primaryButton} onClick={() => createOverride().catch((e) => toast.error(e?.message || 'Create failed'))}>
              Create override
            </button>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Farm</th>
                  <th>Device</th>
                  <th>Metric</th>
                  <th>Value</th>
                  <th>From</th>
                  <th>To</th>
                  <th>Deleted</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {overridesData.items?.length ? (
                  overridesData.items.map((o) => (
                    <tr key={o.id}>
                      <td>{o.id}</td>
                      <td>{o.farm_id}</td>
                      <td>{o.device_id ?? '-'}</td>
                      <td>{o.metric}</td>
                      <td>{o.value}</td>
                      <td>{o.effective_from ? new Date(o.effective_from).toLocaleString() : '-'}</td>
                      <td>{o.effective_to ? new Date(o.effective_to).toLocaleString() : '-'}</td>
                      <td>{o.deleted_at ? new Date(o.deleted_at).toLocaleString() : '-'}</td>
                      <td className={styles.actionsCell}>
                        {!o.deleted_at ? (
                          <button className={styles.dangerButton} onClick={() => expireOverride(o.id).catch((e) => toast.error(e?.message || 'Expire failed'))}>
                            Expire
                          </button>
                        ) : (
                          <span>-</span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr><td colSpan={9} className={styles.emptyCell}>No overrides found</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <div className={styles.paginationRow}>
            <button className={styles.secondaryButton} disabled={overridesPage <= 1} onClick={() => setOverridesPage((p) => Math.max(1, p - 1))}>Prev</button>
            <div className={styles.paginationMeta}>Page {overridesData.page} / {Math.max(1, Math.ceil((overridesData.total || 0) / (overridesData.page_size || 25)))}</div>
            <button className={styles.secondaryButton} disabled={(overridesData.page || 1) * (overridesData.page_size || 25) >= (overridesData.total || 0)} onClick={() => setOverridesPage((p) => p + 1)}>Next</button>
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className={styles.panel}>
          <div className={styles.panelHeaderCompact}>
            <div className={styles.panelTitle}>
              <Users size={20} />
              Users
            </div>
            <div className={styles.headerActions}>
              <button className={styles.refreshButtonSmall} onClick={() => loadUsers().catch((e) => toast.error(e?.message || 'Failed to load users'))}>
                <RefreshCw size={16} />
                Refresh
              </button>
              <button
                className={styles.refreshButtonSmall}
                onClick={() => exportPaged({
                  name: 'users_export',
                  fetchPage: ({ page, page_size }) => {
                    const params = new URLSearchParams();
                    params.set('page', String(page));
                    params.set('page_size', String(page_size));
                    if (usersQuery.trim()) params.set('q', usersQuery.trim());
                    if (usersRole) params.set('role', usersRole);
                    if (usersOnlyActive !== '') params.set('is_active', usersOnlyActive);
                    return fetchJson(`/api/admin/users?${params.toString()}`);
                  },
                }).catch((e) => toast.error(e?.message || 'Export failed'))}
              >
                <Download size={16} />
                Export CSV
              </button>
            </div>
          </div>

          <div className={styles.filtersRow}>
            <div className={styles.searchBox}>
              <Search size={16} />
              <input
                value={usersQuery}
                onChange={(e) => setUsersQuery(e.target.value)}
                placeholder="Search username/email/name"
              />
            </div>
            <select value={usersRole} onChange={(e) => setUsersRole(e.target.value)} className={styles.select}>
              <option value="">All roles</option>
              <option value="admin">admin</option>
              <option value="farmer">farmer</option>
            </select>
            <select value={usersOnlyActive} onChange={(e) => setUsersOnlyActive(e.target.value)} className={styles.select}>
              <option value="">All statuses</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
            <button
              className={styles.primaryButton}
              onClick={() => {
                setUsersPage(1);
                loadUsers().catch((e) => toast.error(e?.message || 'Failed to load users'));
              }}
            >
              Apply
            </button>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Onboarding</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {usersData.items.length === 0 ? (
                  <tr><td colSpan={7} className={styles.emptyCell}>No users found</td></tr>
                ) : (
                  usersData.items.map((u) => (
                    <tr
                      key={u.id}
                      className={styles.rowClickable}
                      onClick={() => openUserDrawer(u.id)}
                    >
                      <td>{u.id}</td>
                      <td>{u.username}</td>
                      <td>{u.email}</td>
                      <td>{u.role}</td>
                      <td>{u.is_active ? 'active' : 'inactive'}</td>
                      <td>{u.onboarding_completed ? 'yes' : 'no'}</td>
                      <td className={styles.actionsCell}>
                        {u.is_active ? (
                          <button
                            className={styles.dangerButton}
                            onClick={(e) => {
                              e.stopPropagation();
                              suspendUser(u.id).catch((err) => toast.error(err?.message || 'Suspend failed'));
                            }}
                          >
                            <ShieldAlert size={16} />
                            Suspend
                          </button>
                        ) : (
                          <button
                            className={styles.successButton}
                            onClick={(e) => {
                              e.stopPropagation();
                              unsuspendUser(u.id).catch((err) => toast.error(err?.message || 'Unsuspend failed'));
                            }}
                          >
                            <ShieldCheck size={16} />
                            Unsuspend
                          </button>
                        )}
                        <button
                          className={styles.refreshButtonSmall}
                          title="View this user's IoT &amp; token sandbox"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/admin/sandbox/${u.id}`);
                          }}
                          style={{ marginLeft: 6 }}
                        >
                          <Zap size={14} />
                          View Sandbox
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className={styles.paginationRow}>
            <button className={styles.secondaryButton} disabled={usersPage <= 1} onClick={() => setUsersPage((p) => Math.max(1, p - 1))}>Prev</button>
            <div className={styles.paginationMeta}>Page {usersData.page} / {Math.max(1, Math.ceil((usersData.total || 0) / (usersData.page_size || 25)))}</div>
            <button className={styles.secondaryButton} disabled={(usersData.page || 1) * (usersData.page_size || 25) >= (usersData.total || 0)} onClick={() => setUsersPage((p) => p + 1)}>Next</button>
          </div>
        </div>
      )}

      {activeTab === 'farms' && (
        <div className={styles.panel}>
          <div className={styles.panelHeaderCompact}>
            <div className={styles.panelTitle}>
              <Gauge size={20} />
              Farms
            </div>
            <div className={styles.headerActions}>
              <button className={styles.refreshButtonSmall} onClick={() => loadFarms().catch((e) => toast.error(e?.message || 'Failed to load farms'))}>
                <RefreshCw size={16} />
                Refresh
              </button>
              <button
                className={styles.refreshButtonSmall}
                onClick={() => exportPaged({
                  name: 'farms_export',
                  fetchPage: ({ page, page_size }) => {
                    const params = new URLSearchParams();
                    params.set('page', String(page));
                    params.set('page_size', String(page_size));
                    if (farmsQuery.trim()) params.set('q', farmsQuery.trim());
                    return fetchJson(`/api/admin/farms?${params.toString()}`);
                  },
                }).catch((e) => toast.error(e?.message || 'Export failed'))}
              >
                <Download size={16} />
                Export CSV
              </button>
            </div>
          </div>

          <div className={styles.filtersRow}>
            <div className={styles.searchBox}>
              <Search size={16} />
              <input
                value={farmsQuery}
                onChange={(e) => setFarmsQuery(e.target.value)}
                placeholder="Search farm name/location"
              />
            </div>
            <button
              className={styles.primaryButton}
              onClick={() => {
                setFarmsPage(1);
                loadFarms().catch((e) => toast.error(e?.message || 'Failed to load farms'));
              }}
            >
              Apply
            </button>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>User</th>
                  <th>Location</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {farmsData.items.length === 0 ? (
                  <tr><td colSpan={5} className={styles.emptyCell}>No farms found</td></tr>
                ) : (
                  farmsData.items.map((f) => (
                    <tr key={f.id}>
                      <td>{f.id}</td>
                      <td>{f.name || f.farm_name || '-'}</td>
                      <td>{f.user_id ?? '-'}</td>
                      <td>{[f.location, f.state, f.district].filter(Boolean).join(', ') || '-'}</td>
                      <td>{f.created_at ? new Date(f.created_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className={styles.paginationRow}>
            <button className={styles.secondaryButton} disabled={farmsPage <= 1} onClick={() => setFarmsPage((p) => Math.max(1, p - 1))}>Prev</button>
            <div className={styles.paginationMeta}>Page {farmsData.page} / {Math.max(1, Math.ceil((farmsData.total || 0) / (farmsData.page_size || 25)))}</div>
            <button className={styles.secondaryButton} disabled={(farmsData.page || 1) * (farmsData.page_size || 25) >= (farmsData.total || 0)} onClick={() => setFarmsPage((p) => p + 1)}>Next</button>
          </div>
        </div>
      )}

      {activeTab === 'iot' && (
        <div className={styles.panel}>
          <div className={styles.panelHeaderCompact}>
            <div className={styles.panelTitle}>
              <Cpu size={20} />
              IoT Fleet
            </div>
            <button className={styles.refreshButtonSmall} onClick={() => loadDevices().catch((e) => toast.error(e?.message || 'Failed to load devices'))}>
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Farm</th>
                  <th>Status</th>
                  <th>Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {devicesData.items?.length ? (
                  devicesData.items.map((d) => (
                    <tr key={d.id}>
                      <td>{d.id}</td>
                      <td>{d.name || d.device_name || '-'}</td>
                      <td>{d.farm_id ?? '-'}</td>
                      <td>{d.status || '-'}</td>
                      <td>{d.last_seen_at ? new Date(d.last_seen_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))
                ) : (
                  <tr><td colSpan={5} className={styles.emptyCell}>No devices found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'ai' && (
        <div className={styles.panel}>
          <div className={styles.panelHeaderCompact}>
            <div className={styles.panelTitle}>
              <Activity size={20} />
              AI Interactions
            </div>
            <div className={styles.headerActions}>
              <button className={styles.refreshButtonSmall} onClick={() => loadAiInteractions().catch((e) => toast.error(e?.message || 'Failed to load AI interactions'))}>
                <RefreshCw size={16} />
                Refresh
              </button>
              <button
                className={styles.refreshButtonSmall}
                onClick={() => exportPaged({
                  name: 'ai_interactions_export',
                  fetchPage: ({ page, page_size }) => {
                    const params = new URLSearchParams();
                    params.set('page', String(page));
                    params.set('page_size', String(page_size));
                    return fetchJson(`/api/admin/ai/interactions?${params.toString()}`);
                  },
                }).catch((e) => toast.error(e?.message || 'Export failed'))}
              >
                <Download size={16} />
                Export CSV
              </button>
            </div>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Farm</th>
                  <th>Agent</th>
                  <th>Tokens</th>
                  <th>Success</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {aiData.items.length === 0 ? (
                  <tr><td colSpan={6} className={styles.emptyCell}>No interactions found</td></tr>
                ) : (
                  aiData.items.map((i) => (
                    <tr key={i.id}>
                      <td>{i.id}</td>
                      <td>{i.farm_id ?? '-'}</td>
                      <td>{i.agent_name}</td>
                      <td>{i.tokens_used}</td>
                      <td>{i.success ? 'yes' : 'no'}</td>
                      <td>{i.created_at ? new Date(i.created_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className={styles.paginationRow}>
            <button className={styles.secondaryButton} disabled={aiPage <= 1} onClick={() => setAiPage((p) => Math.max(1, p - 1))}>Prev</button>
            <div className={styles.paginationMeta}>Page {aiData.page} / {Math.max(1, Math.ceil((aiData.total || 0) / (aiData.page_size || 25)))}</div>
            <button className={styles.secondaryButton} disabled={(aiData.page || 1) * (aiData.page_size || 25) >= (aiData.total || 0)} onClick={() => setAiPage((p) => p + 1)}>Next</button>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className={styles.panel}>
          <div className={styles.panelHeaderCompact}>
            <div className={styles.panelTitle}>
              <FileText size={20} />
              Audit Events
            </div>
            <div className={styles.headerActions}>
              <button className={styles.refreshButtonSmall} onClick={() => loadAudit().catch((e) => toast.error(e?.message || 'Failed to load audit logs'))}>
                <RefreshCw size={16} />
                Refresh
              </button>
              <button
                className={styles.refreshButtonSmall}
                onClick={() => exportPaged({
                  name: 'audit_events_export',
                  fetchPage: ({ page, page_size }) => {
                    const params = new URLSearchParams();
                    params.set('page', String(page));
                    params.set('page_size', String(page_size));
                    if (selectedUserId) {
                      params.set('target_type', 'user');
                      params.set('target_id', String(selectedUserId));
                    }
                    return fetchJson(`/api/admin/audit/events?${params.toString()}`);
                  },
                  pageSize: 200,
                }).catch((e) => toast.error(e?.message || 'Export failed'))}
              >
                <Download size={16} />
                Export CSV
              </button>
            </div>
          </div>

          <div className={styles.filtersRow}>
            <div className={styles.auditFilterPill}>
              <span>Filter:</span>
              <span className={styles.auditFilterValue}>
                {selectedUserId ? `User #${selectedUserId}` : 'All'}
              </span>
              {selectedUserId && (
                <button
                  className={styles.auditClearButton}
                  onClick={() => setSelectedUserId(null)}
                  title="Clear filter"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Target</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {auditData.items.length === 0 ? (
                  <tr><td colSpan={5} className={styles.emptyCell}>No audit events found</td></tr>
                ) : (
                  auditData.items.map((e) => (
                    <tr key={e.id}>
                      <td>{e.id}</td>
                      <td>{e.actor_user_id}</td>
                      <td>{e.action_type}</td>
                      <td>{e.target_type}:{e.target_id}</td>
                      <td>{e.created_at ? new Date(e.created_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className={styles.paginationRow}>
            <button className={styles.secondaryButton} disabled={auditPage <= 1} onClick={() => setAuditPage((p) => Math.max(1, p - 1))}>Prev</button>
            <div className={styles.paginationMeta}>Page {auditData.page} / {Math.max(1, Math.ceil((auditData.total || 0) / (auditData.page_size || 50)))}</div>
            <button className={styles.secondaryButton} disabled={(auditData.page || 1) * (auditData.page_size || 50) >= (auditData.total || 0)} onClick={() => setAuditPage((p) => p + 1)}>Next</button>
          </div>
        </div>
      )}

      {activeTab === 'sandbox' && (
        <div className={styles.panelsContainer}>
        {/* Left Panel - IoT Hardware Simulator */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className={styles.panel}
        >
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>
              <Cpu size={20} />
              IoT Hardware Simulator
            </div>
            <div className={styles.toggleContainer}>
              <span className={`${styles.toggleLabel} ${!isLiveMode ? styles.active : ''}`}>
                Simulated Data
              </span>
              <button
                className={`${styles.toggle} ${isLiveMode ? styles.live : ''}`}
                onClick={() => setIsLiveMode(!isLiveMode)}
              >
                <div className={styles.toggleSlider} />
              </button>
              <span className={`${styles.toggleLabel} ${isLiveMode ? styles.active : ''}`}>
                Live Hardware Data
              </span>
            </div>
          </div>

          <div className={styles.sensorsGrid}>
            {sensors.map((sensor) => {
              const Icon = sensor.icon;
              return (
                <motion.div
                  key={sensor.key}
                  whileHover={{ scale: 1.02 }}
                  className={styles.sensorCard}
                >
                  <div className={styles.sensorHeader}>
                    <Icon 
                      size={16} 
                      style={{ color: sensor.color }}
                    />
                    <span className={styles.sensorLabel}>{sensor.label}</span>
                  </div>
                  <div className={styles.sensorValue}>
                    {sensorData[sensor.key]}
                    <span className={styles.sensorUnit}>{sensor.unit}</span>
                  </div>
                  <input
                    type="range"
                    min={sensor.min}
                    max={sensor.max}
                    step={sensor.step || 1}
                    value={sensorData[sensor.key]}
                    onChange={(e) => handleSensorChange(sensor.key, e.target.value)}
                    className={styles.sensorSlider}
                    style={{
                      background: `linear-gradient(to right, ${sensor.color} 0%, ${sensor.color} ${((sensorData[sensor.key] - sensor.min) / (sensor.max - sensor.min)) * 100}%, rgba(255,255,255,0.1) ${((sensorData[sensor.key] - sensor.min) / (sensor.max - sensor.min)) * 100}%, rgba(255,255,255,0.1) 100%)`
                    }}
                  />
                </motion.div>
              );
            })}
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleInjectData}
            disabled={isInjecting}
            className={`${styles.injectButton} ${isInjecting ? styles.injecting : ''}`}
          >
            {isInjecting ? (
              <>
                <div className={styles.spinner} />
                Injecting...
              </>
            ) : (
              <>
                <Send size={16} />
                Inject Sensor Data
              </>
            )}
          </motion.button>
        </motion.div>

        {/* Right Panel - Agent Activity Monitor */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className={styles.panel}
        >
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>
              <Activity size={20} />
              Agent Activity Monitor
            </div>
            <div className={styles.tokenCounter}>
              <Database size={16} />
              Total Tokens Used: <span className={styles.tokenValue}>{totalTokens.toLocaleString()}</span>
            </div>
          </div>

          <div className={styles.terminal}>
            <div className={styles.terminalHeader}>
              <div className={styles.terminalButtons}>
                <div className={`${styles.terminalButton} ${styles.red}`} />
                <div className={`${styles.terminalButton} ${styles.yellow}`} />
                <div className={`${styles.terminalButton} ${styles.green}`} />
              </div>
              <div className={styles.terminalTitle}>Live Agent Feed</div>
            </div>
            
            <div className={styles.terminalContent}>
              {agentLogs.length === 0 ? (
                <div className={styles.terminalPlaceholder}>
                  <Power size={24} />
                  Waiting for agent activity...
                </div>
              ) : (
                <div className={styles.logContainer}>
                  {agentLogs.map((log) => (
                    <motion.div
                      key={log.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={styles.logEntry}
                    >
                      <span className={styles.logTimestamp}>[{log.timestamp}]</span>
                      <span className={styles.logMessage}>{log.message}</span>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
      )}

      {userDrawerOpen && (
        <div className={styles.drawerOverlay} onClick={closeUserDrawer}>
          <div className={styles.drawer} onClick={(e) => e.stopPropagation()}>
            <div className={styles.drawerHeader}>
              <div>
                <div className={styles.drawerTitle}>User Details</div>
                <div className={styles.drawerSubtitle}>
                  {selectedUser ? `${selectedUser.username} (#${selectedUser.id})` : `User #${selectedUserId}`}
                </div>
              </div>
              <button className={styles.iconButton} onClick={closeUserDrawer}>
                <X size={18} />
              </button>
            </div>

            <div className={styles.drawerTabs}>
              <button className={`${styles.drawerTab} ${userDrawerTab === 'profile' ? styles.drawerTabActive : ''}`} onClick={() => setUserDrawerTab('profile')}>
                Profile
              </button>
              <button className={`${styles.drawerTab} ${userDrawerTab === 'farms' ? styles.drawerTabActive : ''}`} onClick={() => setUserDrawerTab('farms')}>
                Farms
              </button>
              <button className={`${styles.drawerTab} ${userDrawerTab === 'iot' ? styles.drawerTabActive : ''}`} onClick={() => setUserDrawerTab('iot')}>
                IoT
              </button>
              <button className={`${styles.drawerTab} ${userDrawerTab === 'usage' ? styles.drawerTabActive : ''}`} onClick={() => setUserDrawerTab('usage')}>
                Usage
              </button>
              <button className={`${styles.drawerTab} ${userDrawerTab === 'audit' ? styles.drawerTabActive : ''}`} onClick={() => setUserDrawerTab('audit')}>
                Audit
              </button>
            </div>

            <div className={styles.drawerBody}>
              {userDrawerTab === 'profile' && (
                <>
                  {selectedUser ? (
                    <>
                      <div className={styles.kpiRow}>
                        <div className={styles.kpiCard}>
                          <div className={styles.kpiLabel}>Farms</div>
                          <div className={styles.kpiValue}>{selectedUserFarms?.total ?? (selectedUserFarms?.items?.length || 0)}</div>
                        </div>
                        <div className={styles.kpiCard}>
                          <div className={styles.kpiLabel}>IoT Devices</div>
                          <div className={styles.kpiValue}>{selectedUserDevices?.total ?? (selectedUserDevices?.items?.length || 0)}</div>
                        </div>
                        <div className={styles.kpiCard}>
                          <div className={styles.kpiLabel}>IoT Connected</div>
                          <div className={styles.kpiValue}>
                            {(selectedUserDevices?.items || []).some((d) => d.status === 'active') ? 'yes' : 'no'}
                          </div>
                        </div>
                      </div>

                      <div className={styles.kvGrid}>
                        <div className={styles.kvRow}><span>Username</span><span>{selectedUser.username}</span></div>
                        <div className={styles.kvRow}><span>Email</span><span>{selectedUser.email}</span></div>
                        <div className={styles.kvRow}><span>Full Name</span><span>{selectedUser.full_name}</span></div>
                        <div className={styles.kvRow}><span>Phone</span><span>{selectedUser.phone || '-'}</span></div>
                        <div className={styles.kvRow}><span>Role</span><span>{selectedUser.role}</span></div>
                        <div className={styles.kvRow}><span>Status</span><span>{selectedUser.is_active ? 'active' : 'inactive'}</span></div>
                        <div className={styles.kvRow}><span>Verified</span><span>{selectedUser.is_verified ? 'yes' : 'no'}</span></div>
                        <div className={styles.kvRow}><span>Onboarding</span><span>{selectedUser.onboarding_completed ? 'complete' : 'pending'}</span></div>
                        <div className={styles.kvRow}><span>Last Device Seen</span><span>{(() => {
                          const last = (selectedUserDevices?.items || [])
                            .filter((d) => d.last_seen_at)
                            .sort((a, b) => new Date(b.last_seen_at).getTime() - new Date(a.last_seen_at).getTime())[0];
                          return last?.last_seen_at ? new Date(last.last_seen_at).toLocaleString() : '-';
                        })()}</span></div>
                        <div className={styles.kvRow}><span>Suspended At</span><span>{selectedUser.suspended_at ? new Date(selectedUser.suspended_at).toLocaleString() : '-'}</span></div>
                        <div className={styles.kvRow}><span>Suspend Reason</span><span>{selectedUser.suspend_reason || '-'}</span></div>
                      </div>
                    </>
                  ) : (
                    <div className={styles.emptyState}>Loading user profile...</div>
                  )}

                  {selectedUser && (
                    <div className={styles.drawerActions}>
                      {selectedUser.is_active ? (
                        <button className={styles.dangerButton} onClick={() => suspendUser(selectedUser.id).then(() => openUserDrawer(selectedUser.id)).catch((e) => toast.error(e?.message || 'Suspend failed'))}>
                          <ShieldAlert size={16} />
                          Suspend
                        </button>
                      ) : (
                        <button className={styles.successButton} onClick={() => unsuspendUser(selectedUser.id).then(() => openUserDrawer(selectedUser.id)).catch((e) => toast.error(e?.message || 'Unsuspend failed'))}>
                          <ShieldCheck size={16} />
                          Unsuspend
                        </button>
                      )}
                    </div>
                  )}
                </>
              )}

              {userDrawerTab === 'farms' && (
                <>
                  <div className={styles.tableWrap}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Name</th>
                          <th>State</th>
                          <th>District</th>
                          <th>Created</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedUserFarms.items?.length ? (
                          selectedUserFarms.items.map((f) => (
                            <tr key={f.id}>
                              <td>{f.id}</td>
                              <td>{f.name || f.farm_name || '-'}</td>
                              <td>{f.state || '-'}</td>
                              <td>{f.district || '-'}</td>
                              <td>{f.created_at ? new Date(f.created_at).toLocaleString() : '-'}</td>
                            </tr>
                          ))
                        ) : (
                          <tr><td colSpan={5} className={styles.emptyCell}>No farms found</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {userDrawerTab === 'iot' && (
                <>
                  <div className={styles.kpiRow}>
                    <div className={styles.kpiCard}>
                      <div className={styles.kpiLabel}>Devices</div>
                      <div className={styles.kpiValue}>{selectedUserDevices?.total ?? (selectedUserDevices?.items?.length || 0)}</div>
                    </div>
                    <div className={styles.kpiCard}>
                      <div className={styles.kpiLabel}>Connected</div>
                      <div className={styles.kpiValue}>
                        {(selectedUserDevices?.items || []).filter((d) => d.status === 'active').length}
                      </div>
                    </div>
                    <div className={styles.kpiCard}>
                      <div className={styles.kpiLabel}>Offline</div>
                      <div className={styles.kpiValue}>
                        {(selectedUserDevices?.items || []).filter((d) => d.status === 'offline').length}
                      </div>
                    </div>
                  </div>

                  <div className={styles.tableWrap}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Farm</th>
                          <th>Device</th>
                          <th>Status</th>
                          <th>Last Seen</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedUserDevices.items?.length ? (
                          selectedUserDevices.items.map((d) => (
                            <tr key={d.id}>
                              <td>{d.id}</td>
                              <td>{d.farm_id ?? '-'}</td>
                              <td>{d.device_name || '-'}</td>
                              <td>{d.status || '-'}</td>
                              <td>{d.last_seen_at ? new Date(d.last_seen_at).toLocaleString() : '-'}</td>
                            </tr>
                          ))
                        ) : (
                          <tr><td colSpan={5} className={styles.emptyCell}>No devices found</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {userDrawerTab === 'usage' && (
                <>
                  <div className={styles.filtersRow}>
                    <div className={styles.auditFilterPill}>
                      <span>Bucket</span>
                      <select
                        className={styles.select}
                        value={selectedUserUsageBucket}
                        onChange={(e) => setSelectedUserUsageBucket(e.target.value)}
                      >
                        <option value="hour">hour</option>
                        <option value="day">day</option>
                        <option value="week">week</option>
                        <option value="month">month</option>
                      </select>
                    </div>
                    {selectedUserUsage && (
                      <div className={styles.auditFilterPill}>
                        <span>Total tokens</span>
                        <span className={styles.auditFilterValue}>{selectedUserUsage.total_tokens?.toLocaleString?.() ?? selectedUserUsage.total_tokens}</span>
                      </div>
                    )}
                    {selectedUserUsage && (
                      <div className={styles.auditFilterPill}>
                        <span>Interactions</span>
                        <span className={styles.auditFilterValue}>{selectedUserUsage.total_interactions?.toLocaleString?.() ?? selectedUserUsage.total_interactions}</span>
                      </div>
                    )}
                  </div>

                  <div className={styles.tableWrap}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>Bucket</th>
                          <th>Tokens</th>
                          <th>Interactions</th>
                          <th>Success</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedUserUsage?.series?.length ? (
                          selectedUserUsage.series.map((r) => (
                            <tr key={r.bucket}>
                              <td>{r.bucket ? new Date(r.bucket).toLocaleString() : '-'}</td>
                              <td>{r.tokens}</td>
                              <td>{r.interactions}</td>
                              <td>{r.success_count}</td>
                            </tr>
                          ))
                        ) : (
                          <tr><td colSpan={4} className={styles.emptyCell}>No usage data found</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {userDrawerTab === 'audit' && (
                <>
                  <div className={styles.tableWrap}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Actor</th>
                          <th>Action</th>
                          <th>Target</th>
                          <th>Created</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedUserAudit.items?.length ? (
                          selectedUserAudit.items.map((e) => (
                            <tr key={e.id}>
                              <td>{e.id}</td>
                              <td>{e.actor_user_id}</td>
                              <td>{e.action_type}</td>
                              <td>{e.target_type}:{e.target_id}</td>
                              <td>{e.created_at ? new Date(e.created_at).toLocaleString() : '-'}</td>
                            </tr>
                          ))
                        ) : (
                          <tr><td colSpan={5} className={styles.emptyCell}>No audit events found</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  <div className={styles.paginationRow}>
                    <button className={styles.secondaryButton} disabled={selectedUserAuditPage <= 1} onClick={() => setSelectedUserAuditPage((p) => Math.max(1, p - 1))}>Prev</button>
                    <div className={styles.paginationMeta}>Page {selectedUserAudit.page} / {Math.max(1, Math.ceil((selectedUserAudit.total || 0) / (selectedUserAudit.page_size || 50)))}</div>
                    <button className={styles.secondaryButton} disabled={(selectedUserAudit.page || 1) * (selectedUserAudit.page_size || 50) >= (selectedUserAudit.total || 0)} onClick={() => setSelectedUserAuditPage((p) => p + 1)}>Next</button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default AdminSandbox;
