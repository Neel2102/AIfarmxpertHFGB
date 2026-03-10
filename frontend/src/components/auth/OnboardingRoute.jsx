import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import FarmOnboarding from '../../auth/FarmOnboarding';

const OnboardingRoute = () => {
  const { user, needsOnboarding, loading } = useAuth();

  if (loading) {
    return <div className="loading-spinner">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!needsOnboarding) {
    if ((user?.role || '').toLowerCase() === 'admin') {
      return <Navigate to="/admin" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }
  return <FarmOnboarding />;
};

export default OnboardingRoute;
