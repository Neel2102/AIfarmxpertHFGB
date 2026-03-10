import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const RouteGuard = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, loading, performCompleteLogout } = useAuth();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuthentication = () => {
      if (!loading) {
        if (!user) {
          sessionStorage.setItem('redirectPath', location.pathname);
          navigate('/login', { replace: true });
          return;
        }

        const token = localStorage.getItem('access_token') || getCookie('access_token');
        if (!token) {
          console.warn('No valid authentication token found');
          navigate('/login', { replace: true });
          return;
        }

        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          if (payload.exp * 1000 < Date.now()) {
            console.warn('Token expired');
            navigate('/login', { replace: true });
            return;
          }
        } catch (error) {
          console.warn('Invalid token format');
          navigate('/login', { replace: true });
          return;
        }
      }
      setIsChecking(false);
    };

    checkAuthentication();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, loading, location.pathname]);

  // Helper function to get cookie value
  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  };

  // Prevent browser back button from accessing protected routes after logout
  useEffect(() => {
    const handlePopState = () => {
      const token = localStorage.getItem('access_token');
      if (!token || !user) {
        // Use React Router navigate with replace so the page truly changes
        navigate('/login', { replace: true });
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Show loading spinner while checking authentication
  if (loading || isChecking) {
    return (
      <div className="auth-loading-container">
        <div className="auth-loading-spinner">
          <div className="spinner"></div>
          <p>Verifying authentication...</p>
        </div>
        <style jsx>{`
          .auth-loading-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.95);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
          }
          .auth-loading-spinner {
            text-align: center;
          }
          .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Render children only if authenticated
  return user ? children : null;
};

export default RouteGuard;
