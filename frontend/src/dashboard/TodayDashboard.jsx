import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle, CloudRain, Mic, MessageSquare, TrendingUp,
  Sparkles, Calendar, CheckCircle2, Circle, Clock, Droplets, Bug, Sprout,
  Hammer, Check, RefreshCw, Layers, AlertCircle, Zap
} from 'lucide-react';
import { dataService } from '../services/apiService';
import apiService from '../services/api';
import DailyFlowTimeline from './DailyFlowTimeline';
import '../styles/Dashboard/TodayDashboard.css';

import { API_BASE_URL } from '../services/apiBase';

const getCategoryIcon = (category) => {
  switch (category?.toLowerCase()) {
    case 'irrigation': return <Droplets size={16} />;
    case 'pest': return <Bug size={16} />;
    case 'fertilizer': return <Sprout size={16} />;
    case 'maintenance': return <Hammer size={16} />;
    case 'harvest': return <Sparkles size={16} />;
    default: return <Clock size={16} />;
  }
};

const TodayDashboard = () => {
  const navigate = useNavigate();
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [farmData, setFarmData] = useState(null);
  const [soilData, setSoilData] = useState({
    moisture: null,
    temperature: null,
    ph: null,
    lastUpdated: null,
    status: 'loading',
    error: null,
  });

  // -- Daily Flow state machine ------------------------------------------
  // flowStatus is the single source of truth for what this page renders:
  //   'loading'     first load in progress
  //   'needs_farm'  no farm / crop configured yet
  //   'no_flow'     farm exists but no tasks generated yet
  //   'generating'  a season plan is being generated
  //   'ready'       tasks loaded
  //   'error'       a request failed
  // It replaces a bare `flowLoading` boolean that was initialised to true and
  // only ever cleared inside fetchDailyFlow -- which never ran when the farms
  // request failed, leaving the page on its skeleton indefinitely.
  const [farmsList, setFarmsList] = useState([]);
  const [selectedFarmId, setSelectedFarmId] = useState(null);
  const [selectedCropId, setSelectedCropId] = useState(null);
  const [flowData, setFlowData] = useState(null);
  const [flowStatus, setFlowStatus] = useState('loading');
  const [missingFields, setMissingFields] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [flowError, setFlowError] = useState(null);
  const [activeTab, setActiveTab] = useState('today'); // 'today' | 'upcoming' | 'timeline' | 'completed' | 'overdue'

  // Network online / offline
  useEffect(() => {
    const onOnline = () => setIsOnline(true);
    const onOffline = () => setIsOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  // Fetch the Daily Flow for an already resolved farm/crop.
  const fetchDailyFlow = useCallback(async (farmId, cropId) => {
    setFlowError(null);
    try {
      const params = new URLSearchParams();
      if (farmId) params.append('farm_id', farmId);
      if (cropId) params.append('crop_id', cropId);

      const res = await apiService.get(`/api/tasks/daily-flow?${params.toString()}`);
      const data = res?.data || res;

      if (data?.status === 'needs_farm_setup') {
        setMissingFields(data.missing_fields || []);
        setFlowStatus('needs_farm');
        return;
      }
      setFlowData(data);
      setFlowStatus((data?.total_tasks_count || 0) > 0 ? 'ready' : 'no_flow');
    } catch (e) {
      console.error('Error fetching Daily Flow:', e);
      setFlowError("We couldn't load your task plan. Please try again.");
      setFlowStatus('error');
    }
  }, []);

  // Resolve the farm and crop, then load the flow. Every exit path settles
  // flowStatus, so the skeleton can never be the page's final state.
  const fetchFarmsAndCrops = useCallback(async () => {
    setFlowStatus('loading');
    setFlowError(null);
    try {
      const res = await apiService.get('/api/tasks/farms-and-crops');
      const data = res?.data || res;

      if (!data?.farms || data.farms.length === 0) {
        setFarmsList([]);
        setMissingFields(data?.missing_fields || []);
        setFlowStatus('needs_farm');
        return;
      }

      setFarmsList(data.farms);
      const farmId = data.active_farm_id || data.farms[0].id;
      const cropId = data.active_crop_id
        || (data.farms[0].crops && data.farms[0].crops.length > 0 ? data.farms[0].crops[0].id : null);
      setSelectedFarmId(farmId);
      setSelectedCropId(cropId);

      if (!cropId) {
        setMissingFields(['crop_type']);
        setFlowStatus('needs_farm');
        return;
      }
      await fetchDailyFlow(farmId, cropId);
    } catch (e) {
      console.error('Could not load farms and crops:', e);
      setFlowError("We couldn't load your farm information. Please try again.");
      setFlowStatus('error');
    }
  }, [fetchDailyFlow]);

  useEffect(() => {
    fetchFarmsAndCrops();
  }, [fetchFarmsAndCrops]);

  // Re-fetch when the farmer switches farm or crop. The first mount is already
  // covered by fetchFarmsAndCrops, so it is skipped here.
  const initialised = React.useRef(false);
  useEffect(() => {
    if (!selectedFarmId || !selectedCropId) return;
    if (!initialised.current) { initialised.current = true; return; }
    setFlowStatus('loading');
    fetchDailyFlow(selectedFarmId, selectedCropId);
  }, [selectedFarmId, selectedCropId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Generate / Regenerate Daily Flow
  const handleGenerateDailyFlow = async () => {
    try {
      setGenerating(true);
      setFlowError(null);
      const res = await apiService.post('/api/tasks/daily-flow/generate', {
        farm_id: selectedFarmId,
        crop_id: selectedCropId
      });
      const data = res?.data || res;

      if (data?.status === 'needs_farm_setup') {
        setMissingFields(data.missing_fields || []);
        setFlowStatus('needs_farm');
        return;
      }
      setFlowData(data);
      setFlowStatus((data?.total_tasks_count || 0) > 0 ? 'ready' : 'no_flow');
    } catch (e) {
      console.error('Error generating Daily Flow:', e);
      // Never surface a raw backend exception to the farmer.
      setFlowError('Unable to generate your season plan. Please try again.');
      setFlowStatus('error');
    } finally {
      setGenerating(false);
    }
  };

  // Toggle Task Completion
  const handleToggleTask = async (taskId, currentStatus) => {
    // Optimistic local update across all task arrays
    const updateList = (arr) =>
      (arr || []).map(t => t.id === taskId ? { ...t, is_completed: !currentStatus, status: !currentStatus ? 'completed' : 'pending' } : t);

    setFlowData(prev => {
      if (!prev) return prev;
      const updatedToday = updateList(prev.today);
      const updatedTomorrow = updateList(prev.tomorrow);
      const updatedUpcoming = updateList(prev.upcoming_7_days);
      const updatedOverdue = updateList(prev.overdue);
      const updatedCompleted = !currentStatus
        ? [...prev.completed, { id: taskId, is_completed: true, status: 'completed' }]
        : prev.completed.filter(t => t.id !== taskId);

      const updatedStages = (prev.season_plan || []).map(stg => ({
        ...stg,
        tasks: updateList(stg.tasks)
      }));

      return {
        ...prev,
        today: updatedToday,
        tomorrow: updatedTomorrow,
        upcoming_7_days: updatedUpcoming,
        overdue: updatedOverdue,
        completed: updatedCompleted,
        season_plan: updatedStages
      };
    });

    try {
      await apiService.patch(`/api/tasks/${taskId}/complete`, {
        is_completed: !currentStatus
      });
    } catch (err) {
      console.error('Failed to sync task status with backend:', err);
      // Re-fetch on error to ensure sync
      fetchDailyFlow(selectedFarmId, selectedCropId);
    }
  };

  // Legacy Dashboard Data (Weather & Farm context)
  useEffect(() => {
    (async () => {
      try {
        const dashboardData = await dataService.getDashboardData(1);
        setFarmData(dashboardData);
      } catch (e) {
        setFarmData(null);
      }
    })();
  }, []);

  const refreshSoil = async () => {
    setSoilData((p) => ({ ...p, status: 'loading', error: null }));
    try {
      const res = await fetch(`${API_BASE_URL}/soil-tests/live`);
      const json = await res.json();
      if (!res.ok || json?.error) {
        throw new Error(json?.message || `Failed to fetch live soil data (status ${res.status})`);
      }
      if (!json?.has_data) {
        throw new Error(json?.message || 'No soil telemetry data available');
      }
      const data = json.data;
      setSoilData({
        moisture: typeof data.soil_moisture === 'number' ? data.soil_moisture : null,
        temperature: typeof data.soil_temperature === 'number' ? data.soil_temperature : null,
        ph: typeof data.soil_ph === 'number' ? data.soil_ph : null,
        lastUpdated: json?.timestamp || new Date().toISOString(),
        status: 'live',
        error: null,
        source: json?.source || 'database',
      });
    } catch (e) {
      setSoilData((p) => ({
        ...p,
        status: 'offline',
        error: String(e?.message || e),
        lastUpdated: new Date().toISOString(),
      }));
    }
  };

  useEffect(() => {
    refreshSoil();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const nowLabel = useMemo(() => new Date().toLocaleString(), []);
  const weather = farmData?.weather;

  const todayActions = useMemo(() => {
    const actions = [];
    if (weather?.condition && /rain/i.test(weather.condition)) {
      actions.push({
        tone: 'warning',
        icon: CloudRain,
        title: 'Weather risk: Rain expected',
        action: 'Avoid spraying. Check drainage in low-lying plots.',
        why: ['Higher wash-off risk for sprays', 'Waterlogging risk increases pest/disease'],
        confidence: 'Medium',
        dataUsed: ['Weather forecast'],
      });
    } else {
      actions.push({
        tone: 'good',
        icon: CloudRain,
        title: 'Weather: No major alerts',
        action: 'Follow normal irrigation schedule. Recheck forecast in evening.',
        why: ['No rain/heat alerts detected'],
        confidence: 'Medium',
        dataUsed: ['Weather snapshot'],
      });
    }

    if (typeof soilData.moisture === 'number') {
      if (soilData.moisture < 40) {
        actions.push({
          tone: 'warning',
          icon: AlertTriangle,
          title: 'Low soil moisture',
          action: 'Irrigate within 24 hours if crop is at sensitive stage.',
          why: ['Moisture below 40% can stress plants'],
          confidence: 'High',
          dataUsed: ['Soil moisture sensor'],
        });
      } else if (soilData.moisture > 80) {
        actions.push({
          tone: 'warning',
          icon: AlertTriangle,
          title: 'High soil moisture',
          action: 'Pause irrigation; monitor for fungal disease signs.',
          why: ['High moisture increases fungal risk'],
          confidence: 'High',
          dataUsed: ['Soil moisture sensor'],
        });
      }
    }

    actions.push({
      tone: 'info',
      icon: TrendingUp,
      title: 'Market check',
      action: 'Open Market Intelligence to compare nearby mandi prices.',
      why: ['Prices change daily; compare before selling'],
      confidence: 'Low',
      dataUsed: ['(Connect price feed)'],
      cta: { label: 'View prices', onClick: () => navigate('/dashboard/orchestrator/market-intelligence') },
    });

    return actions;
  }, [navigate, soilData.moisture, weather?.condition]);

  const lastUpdatedLabel = soilData?.lastUpdated ? new Date(soilData.lastUpdated).toLocaleString() : '--';

  // Active farm and crops list
  const currentFarm = farmsList.find(f => f.id === Number(selectedFarmId)) || farmsList[0];
  const currentCrop = (currentFarm?.crops || []).find(c => c.id === Number(selectedCropId)) || (currentFarm?.crops || [])[0];

  const seasonInfo = flowData?.season_info;
  const currentStage = seasonInfo?.current_stage;

  // Selected tab counts
  const todayCount = flowData?.today?.length || 0;
  const tomorrowCount = flowData?.tomorrow?.length || 0;
  const upcoming7Count = flowData?.upcoming_7_days?.length || 0;
  const upcomingTotal = tomorrowCount + upcoming7Count;
  const stagesCount = flowData?.season_plan?.length || 0;
  const overdueCount = flowData?.overdue?.length || 0;
  const completedCount = flowData?.completed?.length || 0;

  return (
    <div className="today-page">
      {/* Header */}
      <div className="today-header">
        <div>
          <div className="today-title">
            <Layers size={26} style={{ color: 'var(--dash-emerald)' }} />
            Daily Flow
          </div>
          <div className="today-subtitle">
            {flowData?.farm_name || currentFarm?.name || 'Your Farm'} • {flowData?.farm_location || currentFarm?.location || 'Regional'}
            <span className={`today-pill ${isOnline ? 'pill-online' : 'pill-offline'}`}>{isOnline ? 'Online' : 'Offline'}</span>
            <span className="today-pill pill-muted">Updated: {lastUpdatedLabel}</span>
          </div>
        </div>

        <div className="today-actions">
          <button className="today-btn secondary" onClick={() => navigate('/dashboard/voice')}>
            <Mic size={16} />
            Voice
          </button>
          <button className="today-btn secondary" onClick={() => navigate('/dashboard/orchestrator')}>
            <MessageSquare size={16} />
            Ask AI
          </button>
          <button 
            className="today-btn primary" 
            onClick={handleGenerateDailyFlow}
            disabled={generating}
            style={{ minWidth: '170px' }}
          >
            <Sparkles size={16} />
            {generating ? 'Cultivating Flow...' : 'Generate Season Flow'}
          </button>
        </div>
      </div>

      {/* Farm and Crop Selection Controls */}
      <div className="flow-controls-bar">
        <div className="farm-crop-selectors">
          <div className="selector-group">
            <span className="selector-label">Farm:</span>
            <select
              className="styled-select"
              value={selectedFarmId || ''}
              onChange={(e) => {
                const fId = Number(e.target.value);
                setSelectedFarmId(fId);
                const f = farmsList.find(farm => farm.id === fId);
                if (f && f.crops && f.crops.length > 0) {
                  setSelectedCropId(f.crops[0].id);
                }
              }}
            >
              {farmsList.map(f => (
                <option key={f.id} value={f.id}>{f.name} ({f.location})</option>
              ))}
            </select>
          </div>

          {currentFarm?.crops && currentFarm.crops.length > 0 && (
            <div className="selector-group">
              <span className="selector-label">Crop:</span>
              <select
                className="styled-select"
                value={selectedCropId || ''}
                onChange={(e) => setSelectedCropId(Number(e.target.value))}
              >
                {currentFarm.crops.map(c => (
                  <option key={c.id} value={c.id}>{c.crop_type} ({c.variety || 'Standard'})</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="quick-stats-pill">
          <span style={{ color: 'var(--dash-text-muted)', fontSize: '0.8rem' }}>
            Total Season Tasks: <strong>{flowData?.total_tasks_count || 0}</strong>
          </span>
        </div>
      </div>

      {/* Error Alert Banner */}
      {flowError && flowStatus === 'ready' && (
        <div className="checklist-error" style={{ marginBottom: '18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertCircle size={18} />
            <span>{flowError}</span>
          </div>
          <button 
            className="today-btn secondary"
            style={{ padding: '4px 12px', fontSize: '0.8rem', height: 'auto', flexShrink: 0 }}
            onClick={fetchFarmsAndCrops}
          >
            <RefreshCw size={13} /> Retry
          </button>
        </div>
      )}

      {/* STATE 4 — Generating Banner */}
      {generating && (
        <div className="task-cultivating-card" style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px 20px',
          background: 'rgba(16, 185, 129, 0.05)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          borderRadius: '16px',
          marginBottom: '20px',
          gap: '8px'
        }}>
          <dotlottie-player
            src="/animations/soil cultivating.lottie"
            autoplay
            loop
            style={{ width: '85px', height: '85px' }}
          />
          <div style={{ fontFamily: 'Orbitron, monospace', fontSize: '0.86rem', fontWeight: 700, color: 'var(--dash-emerald)', letterSpacing: '0.06em' }}>
            Generating your seasonal plan...
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--dash-text-muted)' }}>
            Calculating crop duration, stage milestones, weather alerts, and soil sensor telemetry
          </div>
        </div>
      )}

      {/* STATE 1 — Initial Loading Skeleton (only while actually loading) */}
      {flowStatus === 'loading' && (
        <div className="daily-flow-loading-skeleton">
          <div className="skeleton-line title" />
          <div className="skeleton-line" style={{ width: '55%' }} />
          <div className="skeleton-grid">
            <div className="skeleton-box" />
            <div className="skeleton-box" />
            <div className="skeleton-box" />
            <div className="skeleton-box" />
          </div>
        </div>
      )}

      {/* STATE 2 — No Farm / Crop Configured */}
      {flowStatus === 'needs_farm' && (
        <div className="daily-flow-card state-no-farm">
          <Sprout size={42} style={{ color: 'var(--dash-emerald)', marginBottom: '12px' }} />
          <h3>Add your farm to generate a seasonal plan.</h3>
          <p>
            {missingFields.length > 0
              ? `Set your ${missingFields.map(f => f.replace(/_/g, ' ')).join(' and ')} in Settings to get a seasonal crop timeline and daily operations.`
              : 'Set up your farm profile, crop type, and soil details to get tailored seasonal crop timelines and daily operations.'}
          </p>
          <button className="today-btn primary" onClick={() => navigate('/dashboard/setting')}>
            Configure Farm Profile
          </button>
        </div>
      )}

      {/* STATE 6 — Load / Generation Failed */}
      {flowStatus === 'error' && (
        <div className="daily-flow-card state-error">
          <AlertCircle size={38} style={{ color: '#ef4444', marginBottom: '10px' }} />
          <h3>Something went wrong.</h3>
          <p>{flowError}</p>
          <button className="today-btn primary" onClick={fetchFarmsAndCrops} disabled={generating}>
            <RefreshCw size={15} /> Try Again
          </button>
        </div>
      )}

      {/* STATE 3 — Farm Exists, No Season Flow Generated Yet */}
      {flowStatus === 'no_flow' && !generating && (
        <div className="daily-flow-card state-uninitiated">
          <Sparkles size={40} style={{ color: 'var(--dash-emerald)', marginBottom: '12px' }} />
          <h3>Your seasonal plan hasn't been generated yet.</h3>
          <p>Generate a complete crop lifecycle roadmap with growth stages, weather-informed irrigation, and daily farm tasks.</p>
          <button className="today-btn primary" onClick={handleGenerateDailyFlow} disabled={generating}>
            <Sparkles size={16} /> Generate Season Flow
          </button>
        </div>
      )}

      {/* STATE 4 — Generating Season Flow */}
      {generating && (
        <div className="daily-flow-card state-generating">
          <RefreshCw size={36} className="spin" style={{ color: 'var(--dash-emerald)', marginBottom: '12px' }} />
          <h3>AI is crafting your customized seasonal crop plan...</h3>
          <p>Analyzing soil profile, historical weather patterns, and crop lifecycle milestones. This takes ~5-10 seconds.</p>
        </div>
      )}

      {/* STATE 5 — Season Flow Loaded */}
      {flowStatus === 'ready' && !generating && flowData && (
        <>
          {/* Crop Season Overview Progress Card */}
          {seasonInfo && (
            <div className="season-overview-card">
              <div className="season-header-row">
                <div className="season-crop-title">
                  <Sprout size={22} style={{ color: 'var(--dash-emerald)' }} />
                  {flowData?.crop_name || currentCrop?.crop_type || 'Crop'}
                  {flowData?.crop_variety && (
                    <span style={{ fontSize: '0.86rem', color: 'var(--dash-text-muted)', fontWeight: 500 }}>
                      ({flowData.crop_variety})
                    </span>
                  )}
                  {currentStage && (
                    <span className="stage-pill">
                      {currentStage.name || 'Active Vegetative'}
                    </span>
                  )}
                </div>

                <div className="season-cycle-stat">
                  Day {seasonInfo.days_since_planting} of {seasonInfo.duration_days} ({seasonInfo.progress_pct}%)
                </div>
              </div>

              <div className="season-dates-bar">
                <span className="season-date-item">
                  <Sprout size={15} />
                  <span className="season-date-label">Sown</span>
                  <span className="season-date-value">{new Date(seasonInfo.planting_date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</span>
                </span>
                <span className="season-date-item">
                  <Calendar size={15} />
                  <span className="season-date-label">Expected harvest</span>
                  <span className="season-date-value">{new Date(seasonInfo.expected_harvest_date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</span>
                </span>
                <span className="season-date-item">
                  <Clock size={15} />
                  <span className="season-date-label">Duration</span>
                  <span className="season-date-value">{seasonInfo.duration_days} days</span>
                </span>
              </div>

              <div className="season-progress-container">
                <div className="season-progress-header">
                  <span>Season Progression</span>
                  <span>{seasonInfo.progress_pct}% Completed</span>
                </div>
                <div className="season-progress-bar">
                  <div 
                    className="season-progress-fill" 
                    style={{ width: `${seasonInfo.progress_pct}%` }} 
                  />
                </div>
              </div>
            </div>
          )}

          {/* Flow View Tabs */}
          <div className="flow-tabs-nav">
            <button
              className={`flow-tab-btn ${activeTab === 'today' ? 'active' : ''}`}
              onClick={() => setActiveTab('today')}
            >
              <Zap size={15} /> Today's Tasks
              <span className="flow-tab-badge">{todayCount}</span>
            </button>

            <button
              className={`flow-tab-btn ${activeTab === 'upcoming' ? 'active' : ''}`}
              onClick={() => setActiveTab('upcoming')}
            >
              <Calendar size={15} /> Next 7 Days
              <span className="flow-tab-badge">{upcomingTotal}</span>
            </button>

            <button
              className={`flow-tab-btn ${activeTab === 'timeline' ? 'active' : ''}`}
              onClick={() => setActiveTab('timeline')}
            >
              <Sprout size={15} /> Season Timeline
              <span className="flow-tab-badge">{stagesCount} Stages</span>
            </button>

            {overdueCount > 0 && (
              <button
                className={`flow-tab-btn danger ${activeTab === 'overdue' ? 'active' : ''}`}
                onClick={() => setActiveTab('overdue')}
              >
                <AlertTriangle size={15} /> Overdue
                <span className="flow-tab-badge">{overdueCount}</span>
              </button>
            )}

            <button
              className={`flow-tab-btn ${activeTab === 'completed' ? 'active' : ''}`}
              onClick={() => setActiveTab('completed')}
            >
              <CheckCircle2 size={15} /> Completed
              <span className="flow-tab-badge">{completedCount}</span>
            </button>
          </div>

          {/* Tab 1: Today's Tasks */}
          {activeTab === 'today' && (
            <div className="daily-checklist" style={{ margin: '0 0 28px 0' }}>
              <div className="checklist-header">
                <div>
                  <h3>Today's Action Plan</h3>
                  <p className="subtitle">High-priority operational tasks for {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</p>
                </div>
                {todayCount > 0 && (
                  <div className="progress-indicator">
                    {flowData.today.filter(t => t.is_completed).length} / {todayCount} Completed
                  </div>
                )}
              </div>

              {todayCount === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon-wrap">
                    <Check size={30} />
                  </div>
                  <h4>All caught up for today!</h4>
                  <p>No pending operations scheduled for today. Check upcoming tasks in the Tomorrow & Next 7 Days tab or review the Season Timeline.</p>
                </div>
              ) : (
                <div className="task-list">
                  {flowData.today.map((task) => (
                <div 
                  key={task.id} 
                  className={`task-item ${task.is_completed ? 'completed' : ''} priority-${task.priority.toLowerCase()}`}
                  onClick={() => handleToggleTask(task.id, task.is_completed)}
                >
                  <div className="task-checkbox">
                    {task.is_completed ? (
                      <CheckCircle2 className="checked" size={24} />
                    ) : (
                      <Circle className="unchecked" size={24} />
                    )}
                  </div>
                  
                  <div className="task-content">
                    <div className="task-title-row">
                      <h4 className="task-title">{task.title}</h4>
                      <span className={`task-badge ${task.priority.toLowerCase()}`}>
                        {task.priority.toUpperCase()}
                      </span>
                    </div>
                    <p className="task-desc">{task.description}</p>
                    <div className="task-meta">
                      <span className="task-category">
                        {getCategoryIcon(task.category)}
                        {task.category?.toUpperCase() || 'OPERATION'}
                      </span>
                      <span className="task-time">
                        <Calendar size={13} /> Today
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Tomorrow & Next 7 Days */}
      {activeTab === 'upcoming' && (
        <div className="upcoming-tasks-section" style={{ marginBottom: '28px' }}>
          {/* Tomorrow Section */}
          <div className="daily-checklist" style={{ margin: '0 0 20px 0' }}>
            <div className="checklist-header">
              <div>
                <h3>Tomorrow's Tasks</h3>
                <p className="subtitle">Scheduled operations for tomorrow</p>
              </div>
              <span className="flow-tab-badge">{tomorrowCount} tasks</span>
            </div>

            {tomorrowCount === 0 ? (
              <div style={{ padding: '20px', color: 'var(--dash-text-muted)', fontSize: '0.86rem' }}>
                No specific tasks scheduled for tomorrow.
              </div>
            ) : (
              <div className="task-list">
                {flowData.tomorrow.map(task => (
                  <div 
                    key={task.id} 
                    className={`task-item ${task.is_completed ? 'completed' : ''} priority-${task.priority.toLowerCase()}`}
                    onClick={() => handleToggleTask(task.id, task.is_completed)}
                  >
                    <div className="task-checkbox">
                      {task.is_completed ? <CheckCircle2 className="checked" size={24} /> : <Circle className="unchecked" size={24} />}
                    </div>
                    <div className="task-content">
                      <div className="task-title-row">
                        <h4 className="task-title">{task.title}</h4>
                        <span className={`task-badge ${task.priority.toLowerCase()}`}>{task.priority.toUpperCase()}</span>
                      </div>
                      <p className="task-desc">{task.description}</p>
                      <div className="task-meta">
                        <span className="task-category">{getCategoryIcon(task.category)} {task.category?.toUpperCase()}</span>
                        <span className="task-time"><Calendar size={13} /> {task.scheduled_date_str}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Next 7 Days Section */}
          <div className="daily-checklist" style={{ margin: 0 }}>
            <div className="checklist-header">
              <div>
                <h3>Next 7 Days Operational Horizon</h3>
                <p className="subtitle">Upcoming work scheduled over the coming week</p>
              </div>
              <span className="flow-tab-badge">{upcoming7Count} tasks</span>
            </div>

            {upcoming7Count === 0 ? (
              <div style={{ padding: '20px', color: 'var(--dash-text-muted)', fontSize: '0.86rem' }}>
                No tasks scheduled for the next 7 days.
              </div>
            ) : (
              <div className="task-list">
                {flowData.upcoming_7_days.map(task => (
                  <div 
                    key={task.id} 
                    className={`task-item ${task.is_completed ? 'completed' : ''} priority-${task.priority.toLowerCase()}`}
                    onClick={() => handleToggleTask(task.id, task.is_completed)}
                  >
                    <div className="task-checkbox">
                      {task.is_completed ? <CheckCircle2 className="checked" size={24} /> : <Circle className="unchecked" size={24} />}
                    </div>
                    <div className="task-content">
                      <div className="task-title-row">
                        <h4 className="task-title">{task.title}</h4>
                        <span className={`task-badge ${task.priority.toLowerCase()}`}>{task.priority.toUpperCase()}</span>
                      </div>
                      <p className="task-desc">{task.description}</p>
                      <div className="task-meta">
                        <span className="task-category">{getCategoryIcon(task.category)} {task.category?.toUpperCase()}</span>
                        <span className="task-time"><Calendar size={13} /> {task.scheduled_date_str}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Season Flow Timeline */}
      {activeTab === 'timeline' && (
        <DailyFlowTimeline
          stages={flowData?.season_plan || []}
          onToggleTask={handleToggleTask}
        />
      )}

      {/* Tab 4: Overdue Tasks */}
      {activeTab === 'overdue' && (
        <div className="daily-checklist" style={{ margin: '0 0 28px 0', borderColor: 'rgba(239, 68, 68, 0.4)' }}>
          <div className="checklist-header">
            <div>
              <h3 style={{ color: '#ef4444' }}>Overdue Tasks</h3>
              <p className="subtitle">Tasks past their scheduled deadline requiring immediate attention</p>
            </div>
          </div>

          <div className="task-list">
            {flowData?.overdue?.map(task => (
              <div 
                key={task.id} 
                className="task-item priority-high"
                onClick={() => handleToggleTask(task.id, task.is_completed)}
              >
                <div className="task-checkbox">
                  <Circle className="unchecked" size={24} />
                </div>
                <div className="task-content">
                  <div className="task-title-row">
                    <h4 className="task-title">{task.title}</h4>
                    <span className="task-badge high">OVERDUE</span>
                  </div>
                  <p className="task-desc">{task.description}</p>
                  <div className="task-meta">
                    <span className="task-category">{getCategoryIcon(task.category)} {task.category?.toUpperCase()}</span>
                    <span className="task-time" style={{ color: '#ef4444' }}>
                      <Calendar size={13} /> Was scheduled: {task.scheduled_date_str}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 5: Completed Tasks */}
      {activeTab === 'completed' && (
        <div className="daily-checklist" style={{ margin: '0 0 28px 0' }}>
          <div className="checklist-header">
            <div>
              <h3>Completed Operations</h3>
              <p className="subtitle">Audit log of fulfilled tasks across the crop cycle</p>
            </div>
            <span className="flow-tab-badge">{completedCount} Completed</span>
          </div>

          {completedCount === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--dash-text-muted)' }}>
              No tasks completed yet. Check off tasks in Today or the Timeline as you complete them!
            </div>
          ) : (
            <div className="task-list">
              {flowData?.completed?.map(task => (
                <div 
                  key={task.id} 
                  className="task-item completed"
                  onClick={() => handleToggleTask(task.id, task.is_completed)}
                >
                  <div className="task-checkbox">
                    <CheckCircle2 className="checked" size={24} />
                  </div>
                  <div className="task-content">
                    <div className="task-title-row">
                      <h4 className="task-title">{task.title}</h4>
                      <span className="task-badge" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>COMPLETED</span>
                    </div>
                    <p className="task-desc">{task.description}</p>
                    <div className="task-meta">
                      <span className="task-category">{getCategoryIcon(task.category)} {task.category?.toUpperCase()}</span>
                      <span className="task-time"><Calendar size={13} /> {task.scheduled_date_str}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      </>
      )}

      {/* Preserved Telemetry Action Grid */}
      <h3 style={{ margin: '32px 0 16px', fontSize: '1.1rem', fontWeight: 700, color: 'var(--dash-text-heading)' }}>
        Live Farm Telemetry & Field Alerts
      </h3>

      <div className="today-grid">
        {todayActions.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className={`action-card ${card.tone}`}>
              <div className="action-card-top">
                <div className="action-card-icon">
                  <Icon size={18} />
                </div>
                <div className="action-card-head">
                  <div className="action-card-title">{card.title}</div>
                  <div className="action-card-action">{card.action}</div>
                </div>
              </div>

              <div className="action-card-meta">
                <div className="meta-row">
                  <span className="meta-label">Why</span>
                  <div className="meta-value">
                    {card.why?.map((w, i) => (
                      <div key={i} className="meta-bullet">{w}</div>
                    ))}
                  </div>
                </div>
                <div className="meta-row">
                  <span className="meta-label">Confidence</span>
                  <span className="meta-chip">{card.confidence || '—'}</span>
                </div>
                <div className="meta-row">
                  <span className="meta-label">Data used</span>
                  <span className="meta-muted">{(card.dataUsed || []).join(', ')}</span>
                </div>
              </div>

              <div className="action-card-footer">
                <button className="today-btn link" onClick={() => navigate('/dashboard/farm-information')}>
                  View details
                </button>
                {card.cta && (
                  <button className="today-btn secondary" onClick={card.cta.onClick}>
                    {card.cta.label}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="today-footnote">Generated at: {nowLabel}</div>
    </div>
  );
};

export default TodayDashboard;
