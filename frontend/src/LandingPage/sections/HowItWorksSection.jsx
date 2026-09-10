import React from 'react';
import { Radio, Microscope, Network, CheckCircle2 } from 'lucide-react';

const STEPS = [
  { key: 'ingestion', num: '01', icon: <Radio size={18} />, title: 'Data Ingestion', description: 'Sensors, satellites, weather APIs, and market feeds stream data into the agent network in real-time.', delay: '' },
  { key: 'analysis', num: '02', icon: <Microscope size={18} />, title: 'Agent Analysis', description: 'Each specialized agent processes its domain data through trained CNN, LSTM, and Transformer models.', delay: '0.1s' },
  { key: 'fusion', num: '03', icon: <Network size={18} />, title: 'Cross-Agent Fusion', description: 'Agents share findings through the orchestration layer, building a holistic picture of your farm.', delay: '0.2s' },
  { key: 'action', num: '04', icon: <CheckCircle2 size={18} />, title: 'Actionable Output', description: 'Precise recommendations delivered in your language, via voice, dashboard, or automated actuators.', delay: '0.3s' },
];

export default function HowItWorksSection() {
  return (
    <section className="how-section" id="how">
      <div className="section-container">
        <div style={{ textAlign: 'center', marginBottom: 0 }}>
          <div className="section-eyebrow" style={{ justifyContent: 'center' }}>
            Process Flow
          </div>
          <h2 className="section-title" style={{ textAlign: 'center' }}>
            From{' '}
            <span className="text-green">Sensor</span>{' '}
            to Action
          </h2>
          <p className="section-sub" style={{ margin: '0 auto', textAlign: 'center' }}>
            Four stages transform raw field data into precise, actionable farming intelligence.
          </p>
        </div>

        <div className="how-grid">
          {STEPS.map((step) => (
            <div
              key={step.key}
              className="how-step reveal"
              style={step.delay ? { transitionDelay: step.delay } : undefined}
            >
              <div className="how-num-circle">
                <span className="how-num">{step.num}</span>
                <span className="how-step-icon">{step.icon}</span>
              </div>
              <div className="how-step-title">{step.title}</div>
              <div className="how-step-desc">{step.description}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
