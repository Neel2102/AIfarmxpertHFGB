import React from 'react';
import { Brain, Zap, Satellite, BarChart3 } from 'lucide-react';

const FEATURES = [
  { key: 'multiAgent', icon: <Brain size={20} />, title: 'Multi-Agent Architecture', description: 'Eight specialized agents collaborate in real-time, each with domain expertise in soil, water, pests, crops, yield, markets, growth, and farmer communication.', delay: '' },
  { key: 'edgeAnalytics', icon: <Zap size={20} />, title: 'Edge Analytics', description: 'Process sensor data at the edge for sub-200ms response times. Critical decisions happen on-farm, not in the cloud.', delay: '0.1s' },
  { key: 'satelliteFusion', icon: <Satellite size={20} />, title: 'Satellite Fusion', description: 'Combine ground-truth sensor readings with satellite imagery for comprehensive field-level intelligence at any scale.', delay: '0.2s' },
  { key: 'adaptiveLoop', icon: <BarChart3 size={20} />, title: 'Adaptive Learning Loop', description: 'Every harvest improves the models. Yield outcomes feed back into predictions, creating a continuously improving system.', delay: '0.3s' },
];

export default function FeaturesSection() {
  return (
    <section className="features-section" id="features">
      <div className="section-container">
        <div className="feature-visual">
          <img
            className="feature-main-img"
            src="https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=700&q=80"
            alt="Core Platform"
          />
          <img
            className="feature-secondary-img"
            src="https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=400&q=80"
            alt="Core Platform"
          />
          <div className="feature-badge-card">
            <div className="fbc-icon"><Brain size={28} /></div>
            <span className="fbc-val">94.7%</span>
            <span className="fbc-label">AI Accuracy Score</span>
          </div>
        </div>

        <div>
          <div className="section-eyebrow">Core Platform</div>
          <h2 className="section-title">
            Why{' '}
            <span className="text-green">FarmXpert</span>{' '}
            Is Different
          </h2>
          <p className="section-sub">
            Not another dashboard. A living, breathing agricultural nervous
            system that thinks, learns, and acts.
          </p>

          <div className="feature-list">
            {FEATURES.map((item) => (
              <div
                key={item.key}
                className="feature-item reveal"
                style={item.delay ? { transitionDelay: item.delay } : undefined}
              >
                <div className="fi-icon">{item.icon}</div>
                <div>
                  <div className="fi-title">{item.title}</div>
                  <div className="fi-desc">{item.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
