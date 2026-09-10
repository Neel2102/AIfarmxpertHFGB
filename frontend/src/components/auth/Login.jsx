import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import AuthLayout from './AuthLayout';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login, user, needsOnboarding } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  React.useEffect(() => {
    if (user) {
      if ((user?.role || '').toLowerCase() === 'admin') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/dashboard/farm-information', { replace: true });
      }
    }
  }, [user, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await login(formData.username, formData.password);

      if (result.success) {
        setTimeout(() => {
          if (needsOnboarding) {
            navigate('/onboarding');
          } else {
            if ((result?.user?.role || '').toLowerCase() === 'admin') {
              navigate('/admin');
            } else {
              navigate('/dashboard/farm-information');
            }
          }
        }, 1500);
      } else {
        setError(result.error || 'Login failed');
      }
    } catch (err) {
      setError('An unexpected error occurred during login');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      artTitle={'Welcome\nBack'}
      artSubtitle="Your farm intelligence platform awaits. Sign in to access real-time insights, AI-powered recommendations, and your complete farm dashboard."
    >
      <header className="form-head-auth">
        <h1 className="form-title-auth">Sign In</h1>
        <p className="form-sub-auth">
          New to FarmXpert?{' '}
          <Link to="/register" className="link-auth">
            Create an account
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

      <form className="login-form-auth" onSubmit={handleSubmit} noValidate>
        {/* Username / Email field */}
        <div className="field-auth">
          <label className="field-label-auth" htmlFor="login-email">
            Username or Email
          </label>
          <input
            id="login-email"
            name="username"
            type="text"
            autoComplete="username"
            placeholder="Enter your username or email"
            className="field-input-auth"
            value={formData.username}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>

        {/* Password field with peek toggle */}
        <div className="field-auth">
          <label className="field-label-auth" htmlFor="login-password">
            Password
          </label>
          <div className="field-control-auth">
            <input
              id="login-password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              placeholder="Enter your password"
              className="field-input-auth"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <button
              type="button"
              className="peek-btn-auth"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              aria-pressed={showPassword}
              tabIndex={-1}
            >
              {showPassword ? (
                <svg className="peek-eye-auth" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M3 3l14 14M9.5 9.5a2.5 2.5 0 003.5 3.5m-1.5-6.5C14 6.5 17 9.5 17 9.5s-1.2 2.3-3.2 4.1M7.5 7.8C4.5 9.2 3 10 3 10s3 6 7 6c1.5 0 2.9-.5 4.1-1.3"
                    stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                  />
                </svg>
              ) : (
                <svg className="peek-eye-auth" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M1 10s3.2-6 9-6 9 6 9 6-3.2 6-9 6-9-6-9-6Z"
                    stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"
                  />
                  <circle cx="10" cy="10" r="2.4" stroke="currentColor" strokeWidth="1.4" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Row: Forgot password */}
        <div className="field-row-auth">
          <span></span>
          <Link to="/forgot-password" className="link-muted-auth">
            Forgot password?
          </Link>
        </div>

        {/* Primary Submit Button */}
        <button
          type="submit"
          className="btn-primary-auth"
          disabled={loading || !formData.username || !formData.password}
        >
          <span>{loading ? 'Signing in...' : 'Sign In'}</span>
        </button>
      </form>
    </AuthLayout>
  );
};

export default Login;