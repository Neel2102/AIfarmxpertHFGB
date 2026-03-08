// API Service for FarmXpert Backend
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const farmxpertAPI = {
  // Send message to centralized agent endpoint
  sendMessage: async (userInput, agentRole = 'farmer_coach', context = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_input: userInput,
          agent_role: agentRole,
          context: {
            farm_location: context.farm_location || 'ahmedabad, India',
            farm_size: context.farm_size || '5 acres',
            current_season: context.current_season || 'Rainy',
          },
          session_id: context.session_id || null,
          user_id: context.user_id || 1
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
};

export default farmxpertAPI;
