import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { Sun, Moon } from 'lucide-react';
import '../styles/navbar.css';

/**
 * Navbar component — Frozen Lake design with Theme Toggle (Light/Dark).
 * Logo, navigation anchor links, theme toggle button, and conditional CTA button.
 */
export default function Navbar({ hideCta = false }) {
  const location = useLocation();
  const pathname = location.pathname;
  const { toggleTheme, isDark } = useTheme();

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
          <Link to="/login" className="nav-cta">
            Get Started
          </Link>
        )}
      </div>
    </nav>
  );
}
