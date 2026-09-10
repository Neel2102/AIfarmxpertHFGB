import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Check } from 'lucide-react';
import AuthLayout from './AuthLayout';

const ResetPassword = () => {
  const [formData, setFormData] = useState({
    newPassword: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [tokenValid, setTokenValid] = useState(null);
  const [passwordStrength, setPasswordStrength] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  useEffect(() => {
    const doVerify = async () => {
      if (!token) {
        setError('Invalid reset link. Please request a new password reset.');
        setTokenValid(false);
        return;
      }
      try {
        const response = await fetch('/api/auth/verify-reset-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        });

        if (response.ok) {
          setTokenValid(true);
        } else {
          setTokenValid(false);
          setError('Invalid or expired reset link. Please request a new password reset.');
        }
      } catch (err) {
        setTokenValid(false);
        setError('Failed to verify reset link. Please try again.');
      }
    };
    doVerify();
  }, [token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (error) setError('');

    if (name === 'newPassword') {
      checkPasswordStrength(value);
    }
  };

  const checkPasswordStrength = (password) => {
    if (password.length < 6) {
      setPasswordStrength('weak');
    } else if (password.length < 8) {
      setPasswordStrength('medium');
    } else {
      setPasswordStrength('strong');
    }
  };

  const validateForm = () => {
    if (formData.newPassword !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    if (formData.newPassword.length < 6) {
      setError('Password must be at least 6 characters long');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    if (!validateForm()) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          new_password: formData.newPassword
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Password reset successfully! Redirecting to login...');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        setError(data.detail || 'Failed to reset password');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (tokenValid === null) {
    return (
      <AuthLayout
        artTitle={'Password\nReset'}
        artSubtitle="Setting a new standard for intelligent farm management."
      >
        <header className="form-head-auth">
          <h1 className="form-title-auth">Verifying link...</h1>
          <p className="form-sub-auth">Please wait while we verify your password reset link.</p>
        </header>
        <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem 0' }}>
          <span className="spinner-auth" style={{ width: '28px', height: '28px' }} />
        </div>
      </AuthLayout>
    );
  }

  if (tokenValid === false) {
    return (
      <AuthLayout
        artTitle={'Password\nReset'}
        artSubtitle="Setting a new standard for intelligent farm management."
      >
        <header className="form-head-auth">
          <h1 className="form-title-auth">Invalid Reset Link</h1>
          <p className="form-sub-auth">This password reset link is invalid or has expired.</p>
        </header>

        <div className="error-banner-auth" role="alert">
          <svg className="error-icon-auth" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div className="error-content-auth">
            <p className="error-title-auth">{error || 'Link expired'}</p>
          </div>
        </div>

        <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
          <Link to="/forgot-password" className="btn-primary-auth" style={{ display: 'inline-block', textDecoration: 'none' }}>
            Request New Reset Link
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      artTitle={'Set New\nPassword'}
      artSubtitle="Choose a strong password to protect your agricultural operations data."
    >
      <header className="form-head-auth">
        <h1 className="form-title-auth">Reset Password</h1>
        <p className="form-sub-auth">Enter your new secure password below.</p>
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
            <p className="status-title-auth">Success</p>
            <p className="status-desc-auth">{success}</p>
          </div>
        </div>
      )}

      <form className="login-form-auth" onSubmit={handleSubmit} noValidate>
        {/* New Password */}
        <div className="field-auth">
          <label className="field-label-auth" htmlFor="reset-newPassword">New Password</label>
          <div className="password-wrapper-auth">
            <input
              id="reset-newPassword"
              name="newPassword"
              type={showPassword ? 'text' : 'password'}
              placeholder="Enter your new password"
              className="field-input-auth"
              value={formData.newPassword}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <button
              type="button"
              className="password-toggle-auth"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              tabIndex={-1}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                {showPassword ? (
                  <>
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </>
                ) : (
                  <>
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </>
                )}
              </svg>
            </button>
          </div>
          {formData.newPassword && (
            <div
              style={{
                marginTop: '6px',
                fontSize: '12px',
                color: passwordStrength === 'strong' ? '#10b981' : passwordStrength === 'medium' ? '#f59e0b' : '#ef4444'
              }}
            >
              Password strength: {passwordStrength}
            </div>
          )}
        </div>

        {/* Confirm New Password */}
        <div className="field-auth">
          <label className="field-label-auth" htmlFor="reset-confirmPassword">Confirm New Password</label>
          <div className="password-wrapper-auth">
            <input
              id="reset-confirmPassword"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="Confirm your new password"
              className="field-input-auth"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <button
              type="button"
              className="password-toggle-auth"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
              tabIndex={-1}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                {showConfirmPassword ? (
                  <>
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </>
                ) : (
                  <>
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </>
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          className="btn-primary-auth"
          disabled={loading || !formData.newPassword || !formData.confirmPassword}
        >
          {loading ? (
            <>
              <span className="spinner-auth" />
              Resetting Password...
            </>
          ) : (
            'Reset Password'
          )}
        </button>
      </form>

      <div className="footer-auth">
        Remember your password?{' '}
        <Link to="/login" className="link-inline-auth">Sign in here</Link>
      </div>
    </AuthLayout>
  );
};

export default ResetPassword;
