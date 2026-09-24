import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQueryClient } from 'react-query';
import { API_BASE_URL } from '../services/apiBase';
import {
  SESSION_EXPIRED, clearSession, decodeJwt, refreshAccessToken,
} from '../services/authSession';

/**
 * Fired on `window` after the farm profile is successfully saved, carrying the
 * complete farm record returned by the backend. Any view that renders farm
 * data should listen for this and re-read, so a save in Settings is visible in
 * Farm Map (and vice versa) without a reload or a re-login.
 */
export const FARM_PROFILE_UPDATED = 'farmxpert:farm-profile-updated';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const queryClient = useQueryClient();

  // Check for existing session on app load
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const storedToken = localStorage.getItem('access_token');
        const storedUser = localStorage.getItem('user');
        
        if (storedToken && storedUser) {
          const parsedUser = JSON.parse(storedUser);
          
          // Decoded with the shared helper so the app has one definition of
          // what a session token looks like.
          const payload = decodeJwt(storedToken);

          if (!payload) {
            console.warn('Authentication token malformed. Resetting session.');
            throw new Error('Invalid token format');
          }

          if (payload.exp && payload.exp * 1000 < Date.now()) {
            // The access token lives 30 minutes, the refresh token 7 days.
            // Reloading the page after half an hour used to sign the farmer
            // out; try to renew the session before giving up on it.
            const renewed = await refreshAccessToken();
            if (!renewed) {
              throw new Error('Token expired');
            }
            setToken(renewed);
            setUser(parsedUser);
            if ((parsedUser?.role || '').toLowerCase() !== 'admin'
                && !parsedUser.onboarding_completed) {
              setNeedsOnboarding(true);
            }
            return;
          }

          setToken(storedToken);
          setUser(parsedUser);
          
          // Check if user needs onboarding
          if ((parsedUser?.role || '').toLowerCase() === 'admin') {
            setNeedsOnboarding(false);
          } else if (!parsedUser.onboarding_completed || parsedUser.onboarding_completed === false) {
            setNeedsOnboarding(true);
          }
        }
      } catch (error) {
        if (error.message !== 'Token expired') {
          console.warn('Auth check notice:', error.message);
        }
        clearSession();
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();

    // Listen for storage changes from other tabs
    const handleStorageChange = (e) => {
      if (e.key === 'access_token' && !e.newValue) {
        setUser(null);
        setToken(null);
      }
    };
    // Any API call whose session could not be renewed raises this, so the UI
    // drops to the sign-in state instead of leaving the farmer on a page that
    // silently fails every request.
    const handleSessionExpired = () => {
      setUser(null);
      setToken(null);
    };
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener(SESSION_EXPIRED, handleSessionExpired);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener(SESSION_EXPIRED, handleSessionExpired);
    };
  }, []);

  const login = async (username, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          password,
          ip_address: '127.0.0.1',
          user_agent: navigator.userAgent
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      
      // Store tokens and user data
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('session_token', data.session_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      setToken(data.access_token);
      setUser(data.user);
      
      // Check if user needs onboarding
      if ((data.user?.role || '').toLowerCase() === 'admin') {
        setNeedsOnboarding(false);
      } else if (!data.user.onboarding_completed || data.user.onboarding_completed === false) {
        setNeedsOnboarding(true);
      } else {
        setNeedsOnboarding(false);
      }
      
      return { success: true, user: data.user };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  };

  const register = async (userData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const error = await response.json();
        // FastAPI 422 returns detail as an array of validation error objects
        const detail = error.detail;
        let message;
        if (Array.isArray(detail)) {
          message = detail.map(e => e.msg || JSON.stringify(e)).join('; ');
        } else {
          message = detail || 'Registration failed';
        }
        throw new Error(message);
      }

      const data = await response.json();
      return { success: true, user: data };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error.message };
    }
  };

  const logout = async () => {
    try {
      // Call backend logout endpoint to invalidate session and clear cookies
      const token = localStorage.getItem('access_token') || getCookie('access_token');
      if (token) {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include cookies in the request
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Complete client-side cleanup regardless of API call success
      performCompleteLogout();
    }
  };

  // Helper function to get cookie value
  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  };

  // Complete logout cleanup function
  const performCompleteLogout = () => {
    // Clear all localStorage data
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('session_token');
    localStorage.removeItem('user');
    
    // Clear all farmxpert chat sessions
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('farmxpert_session_id')) {
        localStorage.removeItem(key);
      }
    });
    
    // Clear all cookies (client-side attempt)
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    document.cookie = 'session_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    // Clear React Query cache
    queryClient.clear();
    
    // Clear all session storage data
    sessionStorage.clear();
    
    // Reset authentication state
    setToken(null);
    setUser(null);
    setNeedsOnboarding(false);
    
    // Force reload to clear any remaining state
    window.location.replace('/login');
  };
  const updateProfile = async (profileData) => {
    try {
      const tokenVal = localStorage.getItem('access_token');
      // Normalise: always send full_name alongside name so backend accepts both
      const payload = {
        ...profileData,
        full_name: profileData.full_name || profileData.name,
        name: profileData.name || profileData.full_name,
        location: profileData.location,
      };
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${tokenVal}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        if (response.status === 404) {
          console.error('404 Error: The profile update endpoint was not found at', `${API_BASE_URL}/auth/profile`);
        }
        const error = await response.json();
        throw new Error(error.detail || 'Profile update failed');
      }

      const data = await response.json();
      // Merge with existing user so we don't lose fields the server doesn't return
      const merged = { ...user, ...data };
      localStorage.setItem('user', JSON.stringify(merged));
      setUser(merged);
      
      return { success: true, user: merged };
    } catch (error) {
      console.error('Profile update error:', error);
      return { success: false, error: error.message };
    }
  };

  const changePassword = async (oldPassword, newPassword) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Password change failed');
      }

      return { success: true };
    } catch (error) {
      console.error('Password change error:', error);
      return { success: false, error: error.message };
    }
  };

  const refreshToken = async () => {
    // Delegates to the shared single-flight refresh so concurrent callers
    // cannot each burn a refresh attempt.
    const renewed = await refreshAccessToken();
    if (renewed) {
      setToken(renewed);
      const stored = localStorage.getItem('user');
      if (stored) {
        try { setUser(JSON.parse(stored)); } catch { /* keep current user */ }
      }
      return { success: true, access_token: renewed };
    }
    setToken(null);
    setUser(null);
    return { success: false, error: 'Session expired. Please sign in again.' };
  };

  const getAuthHeaders = () => {
    // Try to get token from localStorage first, then from cookies
    const token = localStorage.getItem('access_token') || getCookie('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  };

  const completeOnboarding = async (onboardingData) => {
    try {
      const tokenVal = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/auth/onboarding/complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${tokenVal}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(onboardingData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Onboarding submission failed');
      }

      const data = await response.json();
      
      // Sync the fresh user object the backend sends back
      const serverUser = data.user || {};
      const updatedUser = { ...user, ...serverUser, onboarding_completed: true };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      setNeedsOnboarding(false);
      
      return { success: true, data };
    } catch (error) {
      console.error('Onboarding completion error:', error);
      return { success: false, error: error.message };
    }
  };

  const fetchFarmProfile = async () => {
    try {
      const tokenVal = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/auth/farm-profile`, {
        headers: {
          'Authorization': `Bearer ${tokenVal}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch farm profile');
      }

      return await response.json();
    } catch (error) {
      console.error('Fetch farm profile error:', error);
      return null;
    }
  };

  const updateFarmProfile = async (profileData) => {
    try {
      const tokenVal = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/auth/farm-profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${tokenVal}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profileData),
      });

      if (!response.ok) {
        let detail = 'We couldn\'t save your farm details. Please try again.';
        try {
          const error = await response.json();
          if (error?.detail) detail = error.detail;
        } catch {
          /* non-JSON error body — keep the friendly message */
        }
        throw new Error(detail);
      }

      // The response is the complete, committed farm record. Push it out so
      // every consumer (Settings, Farm Map, Daily Flow, weather, chat context)
      // re-reads PostgreSQL instead of keeping a divergent local copy.
      const data = await response.json();
      queryClient.invalidateQueries({ queryKey: ['farmProfile'] });
      queryClient.invalidateQueries({ queryKey: ['farm'] });
      window.dispatchEvent(new CustomEvent(FARM_PROFILE_UPDATED, { detail: data }));

      return { success: true, data };
    } catch (error) {
      console.error('Update farm profile error:', error);
      return { success: false, error: error.message };
    }
  };

  const value = {
    user,
    token,
    loading,
    needsOnboarding,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    refreshToken,
    getAuthHeaders,
    completeOnboarding,
    fetchFarmProfile,
    updateFarmProfile,
    performCompleteLogout, // Expose for emergency logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
