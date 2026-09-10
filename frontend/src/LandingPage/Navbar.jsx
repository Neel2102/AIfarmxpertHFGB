import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { Sun, Moon, LogOut, LayoutDashboard } from 'lucide-react';
import '../styles/navbar.css';

/**
 * Navbar component — Frozen Lake design with Theme Toggle (Light/Dark).
 * Logo, navigation anchor links, theme toggle button, and auth action buttons.
 */
export default function Navbar({ hideCta = false }) {
  const location = useLocation();
  const pathname = location.pathname;
  const { toggleTheme, isDark } = useTheme();
  const { user, logout } = useAuth();

  const isAuthPage = pathname.includes('/login') || pathname.includes('/register') || pathname.includes('/forgot-password') || pathname.includes('/reset-password');
  const isDashboardPage = pathname.includes('/dashboard');

  const shouldHideCta = hideCta || isAuthPage || isDashboardPage;

  return (
    <nav className={isAuthPage || isDashboardPage ? 'nav-auth-page' : ''}>
      <Link to="/" className="nav-logo">
        Farm<span>X</span>pert
      </Link>

      <div className="nav-links">
        <a href={isAuthPage || isDashboardPage ? "/#agents" : "#agents"}>Agents</a>
        <a href={isAuthPage || isDashboardPage ? "/#features" : "#features"}>Features</a>
        <a href={isAuthPage || isDashboardPage ? "/#how" : "#how"}>How It Works</a>
        <a href={isAuthPage || isDashboardPage ? "/#tech" : "#tech"}>Technology</a>
      </div>

      <div className="nav-actions">
        <button
          type="button"
          onClick={toggleTheme}
          className="theme-toggle-btn"
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          {isDark ? <Sun size={15} /> : <Moon size={15} />}
          <span>{isDark ? "Light" : "Dark"}</span>
        </button>

        {!shouldHideCta && (
          user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Link to="/dashboard" className="nav-cta" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <LayoutDashboard size={15} />
                Dashboard
              </Link>
              <button
                type="button"
                onClick={logout}
                className="theme-toggle-btn"
                title="Log Out"
                style={{ padding: '8px 12px', border: '1px solid var(--border-medium)' }}
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Link to="/login" style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)', textDecoration: 'none', padding: '6px 10px' }}>
                Sign In
              </Link>
              <Link to="/register" className="nav-cta">
                Get Started
              </Link>
            </div>
          )
        )}
      </div>
    </nav>
  );
}
