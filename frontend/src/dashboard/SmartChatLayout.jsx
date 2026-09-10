import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ChatPanel from './ChatPanel';
// import OfflineIndicator from '../components/OfflineIndicator';
import { useAuth } from '../contexts/AuthContext';
import { useOrchestrator } from '../contexts/OrchestratorContext';
import { dataService } from '../services/apiService';
import '../styles/Dashboard/SmartChatLayout.css';
import '../styles/components/OfflineIndicator.css';

const SmartChatLayout = () => {
  const [farmData, setFarmData] = useState({
    farm_name: 'Krishna farm',
    location: 'Ahmedabad, Gujarat',
    size_acres: 15,
    weather: { temperature: 27, humidity: 85, condition: 'Partly Cloudy' }
  });
  const { user } = useAuth();
  const { session } = useOrchestrator();

  const getStorageKey = () => user?.id ? `farmxpert_session_id_${user.id}` : 'farmxpert_session_id';

  const [sessionId, setSessionId] = useState(() => {
    const key = user?.id ? `farmxpert_session_id_${user.id}` : 'farmxpert_session_id';
    const saved = localStorage.getItem(key);
    if (saved) return saved;
    const newSession = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem(key, newSession);
    return newSession;
  });

  // Sync session when user logs in or switches account
  useEffect(() => {
    const key = getStorageKey();
    const saved = localStorage.getItem(key);
    if (saved && saved !== sessionId) {
      setSessionId(saved);
    } else if (!saved) {
      const newSession = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem(key, newSession);
      setSessionId(newSession);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  // Keep sessionId synced when selected from sidebar
  useEffect(() => {
    if (session?.id && session.id !== sessionId) {
      setSessionId(session.id);
      localStorage.setItem(getStorageKey(), session.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.id, sessionId]);

  useEffect(() => {
    (async () => {
      try {
        const dashboardData = await dataService.getDashboardData(1);
        if (dashboardData.farm) {
          setFarmData({
            farm_name: dashboardData.farm.name || 'Krishna farm',
            location: dashboardData.farm.location || 'Ahmedabad, Gujarat',
            size_acres: dashboardData.farm.size_acres || 15,
            weather: dashboardData.weather || { temperature: 27, humidity: 85, condition: 'Partly Cloudy' }
          });
        }
        // Check if we're in offline mode
        // setIsOffline(dashboardData.system?.status === 'offline');
      } catch (e) {
        // setIsOffline(true);
      }
    })();
  }, []);

  return (
    <>
      {/* <OfflineIndicator isOnline={!isOffline} /> */}
      <div className="chat-agent-container">
        <div className="chat-wrapper">
          <Routes>
            <Route path="orchestrator" element={<ChatPanel agent="super-agent" farmData={farmData} sessionId={sessionId} />} />
            <Route path="crop-selector" element={<ChatPanel agent="crop_selector" farmData={farmData} sessionId={sessionId} />} />
            <Route path="seed-selection" element={<ChatPanel agent="seed_selection" farmData={farmData} sessionId={sessionId} />} />
            <Route path="soil-health" element={<ChatPanel agent="soil_health" farmData={farmData} sessionId={sessionId} />} />
            <Route path="fertilizer-advisor" element={<ChatPanel agent="fertilizer_advisor" farmData={farmData} sessionId={sessionId} />} />
            <Route path="irrigation-planner" element={<ChatPanel agent="irrigation_planner" farmData={farmData} sessionId={sessionId} />} />
            <Route path="pest-diagnostic" element={<ChatPanel agent="pest_disease_diagnostic" farmData={farmData} sessionId={sessionId} />} />
            <Route path="weather-watcher" element={<ChatPanel agent="weather_watcher" farmData={farmData} sessionId={sessionId} />} />
            <Route path="growth-monitor" element={<ChatPanel agent="growth_stage_monitor" farmData={farmData} sessionId={sessionId} />} />
            <Route path="task-scheduler" element={<ChatPanel agent="task_scheduler" farmData={farmData} sessionId={sessionId} />} />
            <Route path="machinery-manager" element={<ChatPanel agent="machinery_manager" farmData={farmData} sessionId={sessionId} />} />
            <Route path="drone-commander" element={<ChatPanel agent="drone_commander" farmData={farmData} sessionId={sessionId} />} />
            <Route path="layout-mapper" element={<ChatPanel agent="layout_mapper" farmData={farmData} sessionId={sessionId} />} />
            <Route path="yield-predictor" element={<ChatPanel agent="yield_predictor" farmData={farmData} sessionId={sessionId} />} />
            <Route path="profit-optimizer" element={<ChatPanel agent="profit_optimization" farmData={farmData} sessionId={sessionId} />} />
            <Route path="sustainability-tracker" element={<ChatPanel agent="sustainability_tracker" farmData={farmData} sessionId={sessionId} />} />
            <Route path="market-intelligence" element={<ChatPanel agent="market_intelligence" farmData={farmData} sessionId={sessionId} />} />
            <Route path="logistics-storage" element={<ChatPanel agent="logistics_storage" farmData={farmData} sessionId={sessionId} />} />
            <Route path="input-procurement" element={<ChatPanel agent="input_procurement" farmData={farmData} sessionId={sessionId} />} />
            <Route path="crop-insurance-risk" element={<ChatPanel agent="crop_insurance_risk" farmData={farmData} sessionId={sessionId} />} />
            <Route path="farmer-coach" element={<ChatPanel agent="farmer_coach" farmData={farmData} sessionId={sessionId} />} />
            <Route path="compliance-certification" element={<ChatPanel agent="compliance_certification" farmData={farmData} sessionId={sessionId} />} />
            <Route path="community-engagement" element={<ChatPanel agent="community_engagement" farmData={farmData} sessionId={sessionId} />} />
            <Route path="" element={<ChatPanel agent="super-agent" farmData={farmData} sessionId={sessionId} />} />
            <Route path="*" element={<Navigate to="/dashboard/orchestrator" replace />} />
          </Routes>
        </div>
      </div>
    </>
  );
};

export default SmartChatLayout;


