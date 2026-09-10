import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check } from 'lucide-react';
import AuthLayout from './AuthLayout';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setEmail(e.target.value);
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    if (!email) {
      setError('Please enter your email address');
      setLoading(false);
      return;
    }

    if (!email.includes('@')) {
      setError('Please enter a valid email address');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(data.message);
        setEmail('');
      } else {
        setError(data.detail || 'Failed to send reset email');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      artTitle={'Account\nRecovery'}
      artSubtitle="Don't worry — we'll help you get back into your FarmXpert dashboard securely and quickly."
    >
      <header className="form-head-auth">
        <h1 className="form-title-auth">Forgot Password?</h1>
        <p className="form-sub-auth">
          Enter your email address and we'll send you a link to reset your password.
        </p>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="error-banner-auth" role="alert">
          <svg className="error-icon-auth" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div className="error-content-auth">
            <p className="error-title-auth">{error}</p>
          </div>
        </div>
      )}

      {/* Success Banner */}
      {success && (
        <div className="status-banner-auth">
          <div className="status-icon-auth"><Check size={16} /></div>
          <div>
            <p className="status-title-auth">Email Sent</p>
            <p className="status-desc-auth">{success}</p>
          </div>
        </div>
      )}

      <form className="login-form-auth" onSubmit={handleSubmit} noValidate>
        <div className="field-auth">
          <label className="field-label-auth" htmlFor="forgot-email">Email Address</label>
          <input
            id="forgot-email" name="email" type="email" autoComplete="email"
            placeholder="Enter your email address" className="field-input-auth"
            value={email} onChange={handleChange} required disabled={loading}
          />
        </div>

        <button
          type="submit"
          className="btn-primary-auth"
          disabled={loading || !email}
        >
          <span>{loading ? 'Sending...' : 'Send Reset Link'}</span>
        </button>
      </form>

      <div className="back-link-wrap-auth">
        <Link to="/login" className="nav-back-auth">
          ← Back to Sign In
        </Link>
      </div>
    </AuthLayout>
  );
};

export default ForgotPassword;
