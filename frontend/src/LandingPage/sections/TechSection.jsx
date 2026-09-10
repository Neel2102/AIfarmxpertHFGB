import React from 'react';

const TECH_CHIPS = [
  'Next.js', 'FastAPI', 'TensorFlow', 'Python',
  'CNN Models', 'LSTM Networks', 'Transformer AI', 'Multi-Agent Systems',
  'Real-Time Analytics', 'Satellite APIs', 'IoT Edge Computing', 'PostgreSQL',
  'Redis Cache', 'Kubernetes', 'Docker', 'WebSocket Streams',
];

export default function TechSection() {
  return (
    <section className="tech-section" id="tech">
      <div className="section-container">
        <div className="section-eyebrow">Technology Stack</div>
        <h2 className="section-title">
          Built on{' '}
          <span className="text-green">Production-Grade</span>
          <br />
          Infrastructure
        </h2>
        <p className="section-sub">
          Every layer of FarmXpert is designed for scale, speed, and reliability —
          from edge inference to cloud orchestration.
        </p>
        <div className="tech-strip reveal">
          {TECH_CHIPS.map((chip) => (
            <div key={chip} className="tech-chip">
              <span className="tc-dot"></span>
              {chip}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
