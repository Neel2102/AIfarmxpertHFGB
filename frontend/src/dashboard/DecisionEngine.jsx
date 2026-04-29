import React, { useState } from 'react';
import { 
  Droplets, FlaskConical, Sprout, 
  TrendingUp, AlertTriangle, ArrowRight, CheckCircle2,
  RefreshCw, BarChart3, Cpu
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import '../styles/Dashboard/TodayDashboard.css'; // Reusing styles for consistency

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

const DecisionEngine = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [soilInput, setSoilInput] = useState({
    air_temperature: 25.0,
    air_humidity: 60.0,
    soil_moisture: 45.0,
    soil_temperature: 22.0,
    soil_ph: 6.5,
    nitrogen: 40.0,
    phosphorus: 25.0,
    potassium: 100.0
  });

  const [recommendations, setRecommendations] = useState(null);
  const [alerts, setAlerts] = useState([]);

  // Step 1: Handle Input Changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSoilInput(prev => ({ ...prev, [name]: parseFloat(value) || 0 }));
  };

  // Fetch Live IoT Data
  const fetchLiveData = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/soil-tests/live`);
      const json = await res.json();
      if (json.has_data) {
        setSoilInput(prev => ({
          ...prev,
          air_temperature: json.data.air_temperature || prev.air_temperature,
          air_humidity: json.data.air_humidity || prev.air_humidity,
          soil_moisture: json.data.soil_moisture || prev.soil_moisture,
          soil_temperature: json.data.soil_temperature || prev.soil_temperature,
          soil_ph: json.data.soil_ph || prev.soil_ph,
          nitrogen: json.data.nitrogen || prev.nitrogen,
          phosphorus: json.data.phosphorus || prev.phosphorus,
          potassium: json.data.potassium || prev.potassium,
        }));
      }
    } catch (error) {
      console.error("Failed to fetch IoT data", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Get AI Recommendations
  const getRecommendations = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/agents/crop_selector`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: "Recommend top 3 crops based on my current soil data",
          context: {
            soil: soilInput,
            location: "Gujarat", // Default location
            season: "Kharif"
          }
        })
      });
      const data = await response.json();
      setRecommendations(data);
      setStep(2);
    } catch (error) {
      console.error("Failed to get recommendations", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Step 3: Monitoring Flow
  const startMonitoring = () => {
    // Generate some mock alerts based on soil data for demonstration
    const newAlerts = [];
    if (soilInput.soil_moisture < 40) {
      newAlerts.push({
        type: 'warning',
        title: 'Irrigation Needed',
        message: 'Soil moisture is below 40%. Schedule irrigation for tomorrow morning.',
        icon: Droplets
      });
    }
    if (soilInput.nitrogen < 30) {
      newAlerts.push({
        type: 'info',
        title: 'Fertilizer Advice',
        message: 'Nitrogen levels are low. Consider Nitrogen-rich top dressing.',
        icon: FlaskConical
      });
    }
    setAlerts(newAlerts);
    setStep(3);
  };

  return (
    <div className="today-page">
      <div className="today-header">
        <div>
          <div className="today-title">Decision Engine</div>
          <div className="today-subtitle">Guided Farming Flow: Step {step} of 3</div>
        </div>
        <div className="today-actions">
           {step > 1 && (
             <button className="today-btn secondary" onClick={() => setStep(step - 1)}>
               Back
             </button>
           )}
        </div>
      </div>

      <div className="decision-steps">
        <div className={`step-pill ${step >= 1 ? 'active' : ''}`}>1. Soil Health</div>
        <div className="step-divider"></div>
        <div className={`step-pill ${step >= 2 ? 'active' : ''}`}>2. Crop Selection</div>
        <div className="step-divider"></div>
        <div className={`step-pill ${step >= 3 ? 'active' : ''}`}>3. Alert Monitoring</div>
      </div>

      {step === 1 && (
        <div className="step-container">
          <div className="section-card">
            <div className="section-header">
              <h3><FlaskConical size={20} /> Soil Analysis</h3>
              <button 
                className="fetch-btn" 
                onClick={fetchLiveData}
                disabled={isLoading}
              >
                {isLoading ? <RefreshCw className="spinner" size={16} /> : <Cpu size={16} />}
                Fetch from IoT
              </button>
            </div>
            
            <div className="soil-grid">
              <div className="input-group">
                <label>pH Level</label>
                <input type="number" name="soil_ph" value={soilInput.soil_ph} onChange={handleInputChange} />
              </div>
              <div className="input-group">
                <label>Moisture (%)</label>
                <input type="number" name="soil_moisture" value={soilInput.soil_moisture} onChange={handleInputChange} />
              </div>
              <div className="input-group">
                <label>Nitrogen (mg/kg)</label>
                <input type="number" name="nitrogen" value={soilInput.nitrogen} onChange={handleInputChange} />
              </div>
              <div className="input-group">
                <label>Phosphorus (mg/kg)</label>
                <input type="number" name="phosphorus" value={soilInput.phosphorus} onChange={handleInputChange} />
              </div>
              <div className="input-group">
                <label>Potassium (mg/kg)</label>
                <input type="number" name="potassium" value={soilInput.potassium} onChange={handleInputChange} />
              </div>
              <div className="input-group">
                <label>Soil Temp (°C)</label>
                <input type="number" name="soil_temperature" value={soilInput.soil_temperature} onChange={handleInputChange} />
              </div>
            </div>

            <button className="next-btn primary" onClick={getRecommendations} disabled={isLoading}>
              {isLoading ? "Analyzing..." : "Analyze & Get Recommendations"} 
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {step === 2 && recommendations && (
        <div className="step-container">
          <div className="best-choice-card">
            <div className="ribbon">TOP CHOICE</div>
            <div className="choice-content">
              <Sprout size={48} className="choice-icon" />
              <div>
                <h2>{recommendations.best_choice}</h2>
                <p>{recommendations.response}</p>
              </div>
              <div className="choice-profit">
                <TrendingUp size={24} />
                <span>Max Profit</span>
              </div>
            </div>
          </div>

          <div className="recommendations-grid">
            {recommendations.top_three?.map((crop, idx) => (
              <div key={idx} className="crop-option-card">
                <div className="crop-option-header">
                  <h4>{crop.name}</h4>
                  <span className={`profit-pill ${crop.estimated_profit.toLowerCase().includes('high') ? 'high' : 'medium'}`}>
                    {crop.estimated_profit}
                  </span>
                </div>
                <p className="crop-reason">{crop.reason}</p>
                <div className="crop-risk">
                  <AlertTriangle size={14} />
                  <span>{crop.risk || "Low Risk"}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="profit-insight">
            <BarChart3 size={20} />
            <div>
              <strong>Profit Intelligence:</strong>
              <p>{recommendations.profit_comparison}</p>
            </div>
          </div>

          <button className="next-btn primary" onClick={startMonitoring}>
            Select Best Choice & Start Monitoring
            <ArrowRight size={18} />
          </button>
        </div>
      )}

      {step === 3 && (
        <div className="step-container">
          <div className="monitoring-status">
            <div className="status-indicator">
              <div className="pulse"></div>
              <span>Live Monitoring for {recommendations?.best_choice || "Selected Crop"}</span>
            </div>
          </div>

          <div className="alerts-list">
            {alerts.length > 0 ? (
              alerts.map((alert, idx) => {
                const Icon = alert.icon;
                return (
                  <div key={idx} className={`alert-item-large ${alert.type}`}>
                    <div className="alert-icon-box">
                      <Icon size={24} />
                    </div>
                    <div className="alert-content">
                      <h4>{alert.title}</h4>
                      <p>{alert.message}</p>
                    </div>
                    <CheckCircle2 size={24} className="check-mark" />
                  </div>
                );
              })
            ) : (
              <div className="no-alerts">
                <CheckCircle2 size={48} color="#4CAF50" />
                <h3>All Systems Optimal</h3>
                <p>No immediate actions required for your farm.</p>
              </div>
            )}
          </div>

          <button className="next-btn secondary" onClick={() => navigate('/dashboard/today')}>
             Go to Daily Dashboard
             <ArrowRight size={18} />
          </button>
        </div>
      )}

      <style dangerouslySetInnerHTML={{ __html: `
        .decision-steps {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 2rem;
          background: rgba(255, 255, 255, 0.05);
          padding: 0.75rem 1.5rem;
          border-radius: 50px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          width: fit-content;
        }
        .step-pill {
          font-weight: 600;
          color: rgba(255, 255, 255, 0.4);
          font-size: 0.9rem;
        }
        .step-pill.active {
          color: #4CAF50;
        }
        .step-divider {
          width: 20px;
          height: 1px;
          background: rgba(255, 255, 255, 0.1);
        }
        .section-card {
           background: rgba(255, 255, 255, 0.08);
           border-radius: 20px;
           padding: 2rem;
           border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }
        .section-header h3 {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin: 0;
        }
        .fetch-btn {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          background: #2196F3;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
        }
        .soil-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }
        .input-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .input-group label {
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.6);
        }
        .input-group input {
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: white;
          padding: 0.75rem;
          border-radius: 10px;
          font-size: 1rem;
        }
        .next-btn {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem 2rem;
          border-radius: 12px;
          font-weight: 600;
          cursor: pointer;
          border: none;
          transition: all 0.2s;
          width: 100%;
          justify-content: center;
        }
        .next-btn.primary {
          background: linear-gradient(135deg, #4CAF50, #2E7D32);
          color: white;
        }
        .next-btn.secondary {
           background: rgba(255, 255, 255, 0.1);
           color: white;
        }
        .best-choice-card {
          position: relative;
          background: linear-gradient(135deg, #1b5e20, #000);
          border-radius: 24px;
          padding: 2.5rem;
          margin-bottom: 2rem;
          border: 1px solid #4CAF50;
          overflow: hidden;
        }
        .ribbon {
          position: absolute;
          top: 0;
          right: 0;
          background: #FFD700;
          color: #000;
          padding: 0.5rem 2rem;
          font-weight: 800;
          transform: rotate(45deg) translate(25%, -50%);
          font-size: 0.75rem;
        }
        .choice-content {
          display: flex;
          align-items: center;
          gap: 2rem;
        }
        .choice-icon { color: #4CAF50; }
        .choice-profit {
          margin-left: auto;
          text-align: center;
          color: #4CAF50;
        }
        .recommendations-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }
        .crop-option-card {
          background: rgba(255, 255, 255, 0.05);
          padding: 1.5rem;
          border-radius: 20px;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .crop-option-header {
           display: flex;
           justify-content: space-between;
           margin-bottom: 1rem;
        }
        .profit-pill {
          font-size: 0.7rem;
          padding: 0.25rem 0.75rem;
          border-radius: 50px;
          font-weight: 600;
        }
        .profit-pill.high { background: rgba(76, 175, 80, 0.2); color: #4CAF50; }
        .profit-pill.medium { background: rgba(255, 193, 7, 0.2); color: #FFC107; }
        .profit-insight {
          display: flex;
          gap: 1rem;
          background: rgba(33, 150, 243, 0.1);
          padding: 1.5rem;
          border-radius: 15px;
          border: 1px solid rgba(33, 150, 243, 0.2);
          margin-bottom: 2rem;
        }
        .monitoring-status {
          background: rgba(0, 0, 0, 0.3);
          padding: 1rem;
          border-radius: 12px;
          margin-bottom: 2rem;
        }
        .status-indicator {
           display: flex;
           align-items: center;
           gap: 1rem;
        }
        .pulse {
          width: 12px;
          height: 12px;
          background: #4CAF50;
          border-radius: 50%;
          box-shadow: 0 0 0 rgba(76, 175, 80, 0.4);
          animation: pulse 2s infinite;
        }
        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
          70% { box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }
          100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
        }
        .alerts-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          margin-bottom: 2rem;
        }
        .alert-item-large {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          padding: 1.5rem;
          border-radius: 18px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .alert-item-large.warning { border-color: #f44336; }
        .alert-item-large.info { border-color: #2196F3; }
        .alert-icon-box { color: #fff; }
        .alert-content h4 { margin: 0 0 0.25rem 0; }
        .alert-content p { margin: 0; font-size: 0.9rem; opacity: 0.7; }
        .check-mark { margin-left: auto; color: rgba(255, 255, 255, 0.1); }
        .spinner { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}} />
    </div>
  );
};

export default DecisionEngine;
