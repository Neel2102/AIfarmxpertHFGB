import React from 'react';

const AGENTS = [
  { domain: 'Soil Analysis', name: 'Soil Health Agent' },
  { domain: 'Water Management', name: 'Smart Irrigation Agent' },
  { domain: 'Crop Protection', name: 'Pest Detection Agent' },
  { domain: 'Crop Planning', name: 'Crop Advisor Agent' },
  { domain: 'Yield Forecasting', name: 'Yield Prediction Agent' },
  { domain: 'Market Intelligence', name: 'Market Insight Agent' },
  { domain: 'Growth Tracking', name: 'Growth Monitor Agent' },
  { domain: 'Farmer Interface', name: 'Voice Assistant Agent' },
];

export default function AgentsSection() {
  return (
    <section className="agents-section" id="agents">
      <div className="section-container">
        <div className="agents-intro">
          <div className="section-eyebrow">The Agent Network</div>
          <h2 className="section-title">
            Eight Specialized{' '}
            <span className="text-green">AI Agents</span>
            <br />
            Working in Concert
          </h2>
          <p className="section-sub">
            Each agent is a domain expert — trained on specific agricultural
            data, equipped with its own models, and connected to every other
            agent through our orchestration layer.
          </p>
        </div>

        <ul className="agents-roster" aria-label="Agent roster">
          {AGENTS.map((agent, i) => (
            <li key={i} className="agent-entry">
              <span className="agent-entry-domain">{agent.domain}</span>
              <span className="agent-entry-name">{agent.name}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
