import React, { useState, useEffect, useRef } from 'react';
import { 
  Map, 
  Play, 
  Pause, 
  RotateCcw, 
  X,
  ChevronDown,
  ChevronUp,
  Activity,
  CheckCircle,
  Clock,
  AlertCircle,
  Bot,
  TrendingUp,
  Sprout,
  Cloud,
  Droplets,
  Calendar,
  ArrowRight
} from 'lucide-react';
import '../styles/Dashboard/SmartChatJourneyTracker.css';

// Stage configuration
const STAGE_CONFIG = {
  input: { name: 'Farm Input', icon: Map, color: '#2196F3' },
  analysis: { name: 'Analysis', icon: Activity, color: '#9C27B0' },
  crop_recommendation: { name: 'Recommendations', icon: Sprout, color: '#FF9800' },
  crop_selection: { name: 'Selection', icon: CheckCircle, color: '#4CAF50' },
  farming_guidance: { name: 'Guidance', icon: Droplets, color: '#00BCD4' },
  market_insight: { name: 'Market', icon: TrendingUp, color: '#E91E63' },
  alerts_monitoring: { name: 'Alerts', icon: Cloud, color: '#795548' },
  complete: { name: 'Complete', icon: CheckCircle, color: '#4CAF50' }
};

// Agent display names
const AGENT_DISPLAY_NAMES = {
  soil_health: 'Soil Health',
  weather_watcher: 'Weather',
  crop_selector: 'Crop Selector',
  seed_selection: 'Seed Advisor',
  fertilizer_advisor: 'Fertilizer',
  irrigation_planner: 'Irrigation',
  pest_disease_diagnostic: 'Pest Control',
  market_intelligence: 'Market Intel',
  growth_stage_monitor: 'Growth Monitor'
};

const SmartChatJourneyTracker = ({ sessionId, isActive, onComplete }) => {
  const [journeyState, setJourneyState] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [expandedStages, setExpandedStages] = useState(new Set());
  const [selectedAgent, setSelectedAgent] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // WebSocket connection
  useEffect(() => {
    if (!sessionId || !isActive) return;

    const connectWebSocket = () => {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/journey-graph/ws/${sessionId}`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('Journey WebSocket connected');
        setIsConnected(true);
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'state_update' || data.type === 'execution_complete') {
            setJourneyState(data.state);
            
            // Auto-expand current stage
            if (data.state?.current_stage) {
              setExpandedStages(prev => new Set([...prev, data.state.current_stage]));
            }
            
            // Notify parent when complete
            if (data.state?.is_complete && onComplete) {
              onComplete(data.state);
            }
          }
        } catch (e) {
          console.error('WebSocket message error:', e);
        }
      };
      
      wsRef.current.onclose = () => {
        setIsConnected(false);
        // Reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connectWebSocket();

    // Also fetch initial state
    fetchJourneyState();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [sessionId, isActive]);

  const fetchJourneyState = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/journey-graph/status/${sessionId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setJourneyState(data.state);
        }
      }
    } catch (e) {
      console.error('Failed to fetch journey state:', e);
    }
  };

  const toggleStage = (stage) => {
    setExpandedStages(prev => {
      const next = new Set(prev);
      if (next.has(stage)) {
        next.delete(stage);
      } else {
        next.add(stage);
      }
      return next;
    });
  };

  if (!journeyState) {
    return (
      <div className="journey-tracker-loading">
        <div className="journey-tracker-spinner" />
        <span>Initializing journey...</span>
      </div>
    );
  }

  const { 
    current_stage, 
    completed_stages, 
    total_stages, 
    progress,
    agent_executions = [],
    is_complete 
  } = journeyState;

  // Group executions by stage
  const executionsByStage = {};
  agent_executions.forEach(exec => {
    if (!executionsByStage[exec.stage]) {
      executionsByStage[exec.stage] = [];
    }
    executionsByStage[exec.stage].push(exec);
  });

  const stageOrder = ['input', 'analysis', 'crop_recommendation', 'crop_selection', 'farming_guidance', 'market_insight', 'alerts_monitoring'];

  return (
    <div className={`journey-tracker ${is_complete ? 'journey-complete' : ''}`}>
      {/* Header */}
      <div className="journey-tracker-header">
        <div className="journey-tracker-title">
          <Bot className="journey-tracker-icon" size={20} />
          <span>Smart Journey Tracker</span>
          <span className={`journey-connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '●' : '○'}
          </span>
        </div>
        <div className="journey-tracker-progress">
          <span>{Math.round(progress?.percentage || 0)}%</span>
          <span className="journey-stage-count">({completed_stages}/{total_stages} stages)</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="journey-tracker-progress-bar">
        <div 
          className="journey-tracker-progress-fill"
          style={{ width: `${progress?.percentage || 0}%` }}
        />
      </div>

      {/* Stage Pipeline */}
      <div className="journey-stage-pipeline">
        {stageOrder.map((stageKey, index) => {
          const config = STAGE_CONFIG[stageKey];
          const StageIcon = config?.icon || Bot;
          const isActive = current_stage === stageKey;
          const isCompleted = stageOrder.indexOf(current_stage) > index || is_complete;
          const stageExecutions = executionsByStage[stageKey] || [];
          const hasExecutions = stageExecutions.length > 0;
          const isExpanded = expandedStages.has(stageKey);

          return (
            <div 
              key={stageKey}
              className={`journey-stage ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
            >
              <div 
                className="journey-stage-header"
                onClick={() => hasExecutions && toggleStage(stageKey)}
              >
                <div 
                  className="journey-stage-indicator"
                  style={{ 
                    backgroundColor: isActive || isCompleted ? config?.color : undefined,
                    borderColor: config?.color
                  }}
                >
                  <StageIcon size={14} />
                </div>
                <span className="journey-stage-name">{config?.name || stageKey}</span>
                {hasExecutions && (
                  <span className="journey-stage-toggle">
                    {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </span>
                )}
              </div>

              {/* Executions */}
              {isExpanded && hasExecutions && (
                <div className="journey-stage-executions">
                  {stageExecutions.map((exec, idx) => (
                    <div 
                      key={idx}
                      className={`journey-execution ${exec.status}`}
                      onClick={() => setSelectedAgent(selectedAgent?.id === `${stageKey}-${idx}` ? null : { ...exec, id: `${stageKey}-${idx}` })}
                    >
                      <div className="journey-execution-header">
                        <span className="journey-execution-name">
                          {AGENT_DISPLAY_NAMES[exec.agent_name] || exec.agent_name}
                        </span>
                        <span className={`journey-execution-status ${exec.status}`}>
                          {exec.status === 'success' && <CheckCircle size={12} />}
                          {exec.status === 'running' && <Clock size={12} className="spinning" />}
                          {exec.status === 'failed' && <AlertCircle size={12} />}
                        </span>
                      </div>
                      {exec.execution_time_ms && (
                        <span className="journey-execution-time">{exec.execution_time_ms}ms</span>
                      )}

                      {/* Agent Details */}
                      {selectedAgent?.id === `${stageKey}-${idx}` && (
                        <div className="journey-execution-details">
                          {exec.result && (
                            <div className="journey-execution-result">
                              <strong>Result:</strong>
                              <pre>{JSON.stringify(exec.result, null, 2).substring(0, 200)}...</pre>
                            </div>
                          )}
                          {exec.error && (
                            <div className="journey-execution-error">
                              <strong>Error:</strong> {exec.error}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary */}
      {is_complete && (
        <div className="journey-tracker-summary">
          <CheckCircle size={16} className="journey-summary-icon" />
          <span>Journey Complete! All {total_stages} stages processed successfully.</span>
        </div>
      )}
    </div>
  );
};

export default SmartChatJourneyTracker;
