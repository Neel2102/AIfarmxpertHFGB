import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Components
import LandingPage from './LandingPage/LandingPage';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import ForgotPassword from './components/auth/ForgotPassword';
import ResetPassword from './components/auth/ResetPassword';
import OnboardingRoute from './components/auth/OnboardingRoute';
import MainDashboard from './dashboard/MainDashboard';
import AdminSandbox from './admin/AdminSandbox';
import AdminUserSandbox from './admin/AdminUserSandbox';
import RouteGuard from './components/auth/RouteGuard';

import LoadingSpinner from './components/LoadingSpinner';
import OfflineIndicator from './components/OfflineIndicator';

// Context
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AgentProvider } from './contexts/AgentContext';
import { ChatProvider } from './contexts/ChatContext';
import { OrchestratorProvider } from './contexts/OrchestratorContext';

// Styles

// Auth Container Component
const AuthContainer = ({ children }) => (
  <div className="auth-container">
    {children}
  </div>
);

// Auth Card Component  
const AuthCard = ({ children }) => (
  <div className="auth-card">
    {children}
  </div>
);

// Enhanced Private Route Component with strict validation
const PrivateRoute = ({ children }) => {
  const { user, loading, needsOnboarding } = useAuth();

  if (loading) {
    return (
      <AuthContainer>
        <LoadingSpinner />
      </AuthContainer>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Force onboarding if needed, EXCEPT when already on onboarding route
  // Note: AppContent handles global redirection, but this is a safety guard
  if (needsOnboarding && window.location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  return <RouteGuard>{children}</RouteGuard>;
};

// Helper function to get cookie value
const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
};

// Main App Component
const AppContent = () => {
  const { user, loading, needsOnboarding } = useAuth();

  if (loading) {
    return (
      <AuthContainer>
        <LoadingSpinner />
      </AuthContainer>
    );
  }

  // Unauthenticated: allow landing, login, register, etc. 
  // (Handled by the Routes in App component)
  if (!user) {
    return null; 
  }

  // Authenticated BUT needs onboarding: strictly force onboarding
  if (needsOnboarding) {
    if (window.location.pathname !== '/onboarding') {
      return <Navigate to="/onboarding" replace />;
    }
    return null; // Let the Routes handle /onboarding
  }

  // Authenticated AND onboarded: standard dashboard/admin routes
  return null;
};

// Root App Component
function App() {
  return (
    <AuthProvider>
      <OfflineIndicator />
      <OrchestratorProvider>
        <AgentProvider>
          <ChatProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/onboarding" element={<OnboardingRoute />} />
              
              {/* Protected admin routes */}
              <Route path="/admin" element={
                <PrivateRoute>
                  <AdminSandbox />
                </PrivateRoute>
              } />

              {/* Admin: User Sandbox view — /admin/sandbox/:userId */}
              <Route path="/admin/sandbox/:userId" element={
                <PrivateRoute>
                  <AdminUserSandbox />
                </PrivateRoute>
              } />
              
              <Route path="/dashboard/*" element={
                <PrivateRoute>
                  <MainDashboard />
                </PrivateRoute>
              } />
              
              {/* Catch-all route with authentication validation */}
              <Route path="/*" element={<AppContent />} />
            </Routes>
          </ChatProvider>
        </AgentProvider>
      </OrchestratorProvider>
    </AuthProvider>
  );
}

export default App;