import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import AuthLayout from './AuthLayout';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const { register, login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (error) setError('');
  };

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return false;
    }
    if (!formData.email.includes('@')) {
      setError('Please enter a valid email address');
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
      const result = await register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        phone: formData.phone
      });

      if (result.success) {
        setSuccess('Registration successful! Setting up your farm...');
        try {
          const loginRes = await login(formData.username, formData.password);
          if (loginRes?.success) {
            navigate('/onboarding');
            return;
          }
        } catch (loginErr) {
          console.warn('Auto-login failed after registration:', loginErr);
        }
        setTimeout(() => {
          navigate('/login');
        }, 1500);
      } else {
        setError(result.error || 'Registration failed');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      artTitle={'Join\nFarmXpert'}
      artSubtitle="Create your account to unlock AI-powered precision farming with 21+ specialized agents working for your fields."
    >
      <header className="form-head-auth">
        <h1 className="form-title-auth">Create Account</h1>
        <p className="form-sub-auth">
          Already have an account?{' '}
          <Link to="/login" className="link-auth">
            Sign in
          </Link>
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
          <div className="status-icon-auth">✓</div>
          <div>
            <p className="status-title-auth">Success</p>
            <p className="status-desc-auth">{success}</p>
          </div>
        </div>
      )}

      <form className="login-form-auth" onSubmit={handleSubmit} noValidate>
        {/* 2x2 Grid: Name + Username */}
        <div className="fields-grid-2x2-auth">
          <div className="field-auth">
            <label className="field-label-auth" htmlFor="reg-fullname">Full Name</label>
            <input
              id="reg-fullname" name="full_name" type="text" autoComplete="name"
              placeholder="Enter your full name" className="field-input-auth"
              value={formData.full_name} onChange={handleChange} required disabled={loading}
            />
          </div>
          <div className="field-auth">
            <label className="field-label-auth" htmlFor="reg-username">Username</label>
            <input
              id="reg-username" name="username" type="text" autoComplete="username"
              placeholder="Choose a username" className="field-input-auth"
              value={formData.username} onChange={handleChange} required disabled={loading}
            />
          </div>
        </div>

        {/* 2x2 Grid: Email + Phone */}
        <div className="fields-grid-2x2-auth">
          <div className="field-auth">
            <label className="field-label-auth" htmlFor="reg-email">Email Address</label>
            <input
              id="reg-email" name="email" type="email" autoComplete="email"
              placeholder="Enter your email" className="field-input-auth"
              value={formData.email} onChange={handleChange} required disabled={loading}
            />
          </div>
          <div className="field-auth">
            <label className="field-label-auth" htmlFor="reg-phone">Phone (Optional)</label>
            <input
              id="reg-phone" name="phone" type="tel" autoComplete="tel"
              placeholder="Enter your phone number" className="field-input-auth"
              value={formData.phone} onChange={handleChange} disabled={loading}
            />
          </div>
        </div>

        {/* 2x2 Grid: Password + Confirm Password */}
        <div className="fields-grid-2x2-auth">
          <div className="field-auth">
            <label className="field-label-auth" htmlFor="reg-password">Password</label>
            <div className="field-control-auth">
              <input
                id="reg-password" name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="Create a password" className="field-input-auth"
                value={formData.password} onChange={handleChange} required disabled={loading}
              />
              <button
                type="button" className="peek-btn-auth"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword} tabIndex={-1}
              >
                {showPassword ? (
                  <svg className="peek-eye-auth" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                    <path d="M3 3l14 14M9.5 9.5a2.5 2.5 0 003.5 3.5m-1.5-6.5C14 6.5 17 9.5 17 9.5s-1.2 2.3-3.2 4.1M7.5 7.8C4.5 9.2 3 10 3 10s3 6 7 6c1.5 0 2.9-.5 4.1-1.3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : (
                  <svg className="peek-eye-auth" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                    <path d="M1 10s3.2-6 9-6 9 6 9 6-3.2 6-9 6-9-6-9-6Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
                    <circle cx="10" cy="10" r="2.4" stroke="currentColor" strokeWidth="1.4" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div className="field-auth">
            <label className="field-label-auth" htmlFor="reg-confirm">Confirm Password</label>
            <input
              id="reg-confirm" name="confirmPassword"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Confirm your password" className="field-input-auth"
              value={formData.confirmPassword} onChange={handleChange} required disabled={loading}
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="btn-primary-auth"
          disabled={loading || !formData.username || !formData.email || !formData.password || !formData.full_name}
        >
          <span>{loading ? 'Creating Account...' : 'Create Account'}</span>
        </button>
      </form>
    </AuthLayout>
  );
};

export default Register;