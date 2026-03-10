// API Service for fetching real data from FarmXpert backend
import axios from 'axios';

const API_BASE_URL = '/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth tokens if needed
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Farm Data API
export const farmAPI = {
  // Get farm details
  getFarm: async (farmId) => {
    try {
      const response = await apiClient.get(`/farms/${farmId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching farm data:', error);
      throw error;
    }
  },

  // Get farm summary
  getFarmSummary: async (farmId) => {
    try {
      const response = await apiClient.get(`/farms/${farmId}/summary`);
      return response.data;
    } catch (error) {
      console.error('Error fetching farm summary:', error);
      throw error;
    }
  },

  // Get farm tasks
  getFarmTasks: async (farmId, status = null) => {
    try {
      const params = status ? { status } : {};
      const response = await apiClient.get(`/farms/${farmId}/tasks`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching farm tasks:', error);
      throw error;
    }
  },

  // Get farm crops
  getFarmCrops: async (farmId, status = null) => {
    try {
      const params = status ? { status } : {};
      const response = await apiClient.get(`/farms/${farmId}/crops`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching farm crops:', error);
      throw error;
    }
  },

  // Get soil tests
  getSoilTests: async (farmId) => {
    try {
      const response = await apiClient.get(`/farms/${farmId}/soil-tests`);
      return response.data;
    } catch (error) {
      console.error('Error fetching soil tests:', error);
      throw error;
    }
  },
};

// Agent Data API
export const agentAPI = {
  // Get all agents
  getAllAgents: async () => {
    try {
      const response = await apiClient.get('/agents');
      const agentsDict = response.data || {};
      return {
        agents: Object.entries(agentsDict).map(([name, description]) => ({
          name,
          description,
        })),
      };
    } catch (error) {
      console.error('Error fetching agents:', error);
      throw error;
    }
  },

  // Get agent categories
  getAgentCategories: async () => {
    return { categories: [] };
  },

  // Get agent details
  getAgentDetails: async (agentName) => {
    try {
      const response = await apiClient.get('/agents');
      const agentsDict = response.data || {};
      return { name: agentName, description: agentsDict[agentName] };
    } catch (error) {
      console.error('Error fetching agent details:', error);
      throw error;
    }
  },

  // Get available agents from super agent
  getAvailableAgents: async () => {
    try {
      const response = await apiClient.get('/super-agent/agents');
      return response.data;
    } catch (error) {
      console.error('Error fetching available agents:', error);
      throw error;
    }
  },
};

// System Status API
export const systemAPI = {
  // Get system status
  getSystemStatus: async () => {
    try {
      const response = await apiClient.get('/system/status');
      return response.data;
    } catch (error) {
      console.error('Error fetching system status:', error);
      // Fallback for demo if system is down
      return {
        status: 'offline',
        agents: { active: 0, total: 16 },
        system: { uptime: '0h 0m', health: 'unknown' },
        message: 'Backend unavailable'
      };
    }
  },

  // Get health check
  getHealthCheck: async () => {
    try {
      const response = await apiClient.get('/system/health');
      return response.data;
    } catch (error) {
      return { status: 'offline', health: 'unknown' };
    }
  },

  // Get real-time status
  getRealtimeStatus: async () => {
    try {
      const response = await apiClient.get('/system/realtime');
      return response.data;
    } catch (error) {
      return { status: 'offline' };
    }
  },
};

// Weather API (placeholder - would integrate with real weather service)
export const weatherAPI = {
  // Get weather data for location
  // eslint-disable-next-line no-unused-vars
  getWeatherData: async (location) => {
    // This would integrate with a real weather API
    // For now, return mock data that matches the expected format
    return {
      temperature: 27,
      condition: 'Partly Cloudy',
      humidity: 85,
      wind_speed: 15,
      precipitation: 0,
      forecast: [
        { date: 'Today', temp: 27, condition: 'Partly Cloudy', precipitation: 0 },
        { date: 'Tomorrow', temp: 25, condition: 'Rain', precipitation: 15 },
        { date: 'Day After', temp: 23, condition: 'Heavy Rain', precipitation: 25 }
      ]
    };
  },
};

// Combined data service
export const dataService = {
  // Get dashboard data
  getDashboardData: async (farmId = 1) => {
    try {
      // Fetch real farm data
      const farmResponse = await fetch(`${API_BASE_URL}/soil-tests/farm-info`);
      const farmData = await farmResponse.json();
      
      if (!farmData.has_farm) {
        return {
          farm: null,
          summary: {
            total_crops: 0,
            active_tasks: 0,
            completed_tasks: 0,
            soil_health_score: 0,
            weather_alert: false,
            last_updated: new Date().toISOString()
          },
          system: {
            status: 'no_farm',
            message: 'No farm setup found'
          }
        };
      }

      // Fetch latest soil data for additional info
      const soilResponse = await fetch(`${API_BASE_URL}/soil-tests/latest`);
      const soilData = await soilResponse.json();
      
      return {
        farm: farmData.farm,
        summary: {
          total_crops: farmData.farm?.crops?.length || 0,
          active_tasks: 0, // Can be enhanced with real task data
          completed_tasks: 0, // Can be enhanced with real task data
          soil_health_score: soilData.has_data ? 75 : 0, // Basic calculation
          weather_alert: false,
          last_updated: new Date().toISOString()
        },
        system: {
          status: 'active',
          data_source: 'database'
        }
      };
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      return {
        farm: null,
        summary: {
          total_crops: 0,
          active_tasks: 0,
          completed_tasks: 0,
          soil_health_score: 0,
          weather_alert: false,
          last_updated: new Date().toISOString()
        },
        system: {
          status: 'error',
          message: 'Failed to load data'
        }
      };
    }
  },

  // Get agent status data
  getAgentStatusData: async () => {
    // For now, always return mock data to avoid API calls
    // This can be changed when backend is available
    return {
      agents: [],
      categories: [],
      system: {
        status: 'offline',
        message: 'Backend server is not running. Using offline mode.'
      },
      realtime: {
        status: 'offline',
        message: 'Backend server is not running. Using offline mode.'
      }
    };
  },
};

const apiServices = {
  farmAPI,
  agentAPI,
  systemAPI,
  weatherAPI,
  dataService
};

export default apiServices;
