import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../../LandingPage/Navbar';
import AuthMeshArt from './AuthMeshArt';
import '../../styles/auth/auth.css';

/**
 * AuthLayout - Master split layout for all authentication pages.
 * Left: Form panel with brand logo & dynamic form view
 * Right: Geometric mesh art panel with contextual storytelling copy
 */
export default function AuthLayout({
  children,
  artTitle = 'Welcome\nBack',
  artSubtitle = 'Your farm intelligence platform awaits.',
}) {
  const [isRevealed, setIsRevealed] = useState(false);

  useEffect(() => {
    // Auto-reveal the card entrance animation on mount
    const timer = setTimeout(() => {
      setIsRevealed(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      <Navbar hideCta={true} />
      <main className="auth-viewport-auth">
        <div className={`page-auth ${isRevealed ? 'revealed-auth' : 'preparing-auth'}`}>
          {/* LEFT: FORM */}
          <section className="panel-form-auth">
            <div className="form-wrap-auth">
              {/* Brand Header */}
              <Link to="/" className="brand-auth" aria-label="FarmXpert">
                <svg className="brand-mark-auth" viewBox="0 0 32 32" aria-hidden="true">
                  <polygon
                    points="16,2 30,11 30,23 16,30 2,23 2,11"
                    fill="none"
                    stroke="url(#brandGradAuth)"
                    strokeWidth="2"
                  />
                  <polygon points="16,2 30,11 16,16" fill="url(#brandGradAuth)" opacity="0.9" />
                  <polygon points="16,16 30,11 30,23 16,30" fill="url(#brandGradAuth)" opacity="0.55" />
                  <polygon points="16,16 2,11 2,23 16,30" fill="url(#brandGradAuth)" opacity="0.3" />
                  <defs>
                    <linearGradient id="brandGradAuth" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="#047857" />
                      <stop offset="100%" stopColor="#10b981" />
                    </linearGradient>
                  </defs>
                </svg>
                <span className="brand-name-auth">FarmXpert</span>
              </Link>

              {/* Injected Form Component */}
              {children}
            </div>
          </section>

          {/* RIGHT: ARTWORK (Diagonal Split Overlay) */}
          <section className="panel-art-auth" aria-hidden="true">
            <AuthMeshArt />
            <div className="art-copy-auth">
              <h2 className="art-title-auth">{artTitle}</h2>
              <p className="art-sub-auth">{artSubtitle}</p>
            </div>
          </section>
        </div>
      </main>
    </>
  );
}
