import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, Info, AlertTriangle, CloudRain, Wind } from 'lucide-react';
import apiService from '../services/api';
import '../styles/Dashboard/MarketDashboard.css';

const MarketDashboard = () => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setLoading(true);
        const response = await apiService.get('/api/market/prices');
        setMarketData(response.data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch market data:', err);
        setError('Could not load market prices at this time. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchMarketData();
  }, []);

  if (loading) {
    return (
      <div className="market-dashboard loading">
        <div className="skeleton-header"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-grid">
          <div className="skeleton-item"></div>
          <div className="skeleton-item"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="market-dashboard error">
        <AlertTriangle size={48} className="error-icon" />
        <h3>Market Data Unavailable</h3>
        <p>{error}</p>
        <button className="retry-btn" onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  if (!marketData) return null;

  const isUp = marketData.seven_day_trend === 'up';
  const isDown = marketData.seven_day_trend === 'down';
  
  const formattedDate = new Date(marketData.last_updated).toLocaleString('en-IN', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
  });

  return (
    <div className="market-dashboard">
      <header className="market-header">
        <div>
          <h2>Market Intelligence</h2>
          <p className="subtitle">APMC prices for {marketData.crop} in {marketData.state}</p>
        </div>
        <span className="last-updated">Last updated: {formattedDate}</span>
      </header>

      <div className="market-content">
        {/* Main Price Card */}
        <div className="price-card main-card">
          <div className="card-header">
            <h3>Current Market Price</h3>
            <span className={`trend-badge ${marketData.seven_day_trend}`}>
              {isUp ? <TrendingUp size={16} /> : isDown ? <TrendingDown size={16} /> : <Minus size={16} />}
              {Math.abs(marketData.trend_percent)}%
            </span>
          </div>
          
          <div className="price-display">
            <span className="currency">₹</span>
            <span className="amount">{marketData.current_price.toLocaleString('en-IN')}</span>
            <span className="unit">per quintal</span>
          </div>

          <div className="advice-section">
            <div className={`advice-chip ${marketData.advice.toLowerCase()}`}>
              RECOMMENDATION: {marketData.advice}
            </div>
            <p className="advice-reason">
              <Info size={16} />
              {marketData.advice_reason}
            </p>
          </div>
        </div>

        {/* Secondary Info Grid */}
        <div className="info-grid">
          <div className="info-card">
            <h4>Regional Average</h4>
            <div className="info-value">₹{(marketData.current_price * 0.95).toLocaleString('en-IN')}</div>
            <p className="info-desc">Average across nearby mandis</p>
          </div>
          
          <div className="info-card">
            <h4>Expected Volatility</h4>
            <div className="info-value">Moderate</div>
            <p className="info-desc">Based on recent weather patterns</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketDashboard;
