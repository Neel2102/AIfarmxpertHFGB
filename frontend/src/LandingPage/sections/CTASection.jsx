import React from 'react';
import { Link } from 'react-router-dom';

export default function CTASection() {
  return (
    <section className="cta-section">
      <div className="section-container">
        <div className="cta-box reveal">
          <div
            className="section-eyebrow"
            style={{ justifyContent: 'center', marginBottom: '20px' }}
          >
            Get Started
          </div>

          <h2 className="cta-title">
            Ready to{' '}
            <span className="text-green">Transform</span>{' '}
            Your Farm?
          </h2>

          <p className="cta-desc">
            Join thousands of farmers already using FarmXpert's multi-agent AI
            platform to increase yields, reduce costs, and farm smarter.
          </p>

          <div className="cta-actions">
            <Link to="/register"><button className="btn-primary">Start Free Trial</button></Link>
            <Link to="/login"><button className="btn-secondary">Sign In</button></Link>
          </div>
        </div>
      </div>
    </section>
  );
}
