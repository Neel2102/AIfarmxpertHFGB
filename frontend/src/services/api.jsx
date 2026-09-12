/**
 * API Service for FarmXpert Orchestrator
 * Handles all backend communication for the orchestrator components
 */

import { API_BASE_URL } from './apiBase';

class ApiService {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return token ? { Authorization: `Bearer ${token}` } : {};
    }

    normalizeEndpoint(endpoint) {
        if (!endpoint) return '';
        let clean = endpoint.trim();
        // If baseURL ends with '/api' and endpoint starts with '/api/', remove duplicate '/api'
        if (this.baseURL.endsWith('/api') && clean.startsWith('/api/')) {
            clean = clean.substring(4);
        }
        return clean.startsWith('/') ? clean : `/${clean}`;
    }

    /**
     * Generic API request method
     */
    async request(endpoint, options = {}) {
        const cleanEndpoint = this.normalizeEndpoint(endpoint);
        const url = `${this.baseURL}${cleanEndpoint}`;
        const headers = {
            ...this.defaultHeaders,
            ...this.getAuthHeaders(),
            ...options.headers,
        };

        if (typeof FormData !== 'undefined' && options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        const config = {
            headers,
            ...options,
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                let errorDetails = '';
                try {
                    const errJson = await response.json();
                    errorDetails = errJson.detail || errJson.message || JSON.stringify(errJson);
                } catch {
                    errorDetails = response.statusText;
                }
                throw new Error(errorDetails || `API Error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`API Request failed [${options.method || 'GET'} ${url}]:`, error);
            throw error;
        }
    }

    async get(endpoint, options = {}) {
        const data = await this.request(endpoint, { ...options, method: 'GET' });
        return { data, status: 200 };
    }

    async post(endpoint, body = {}, options = {}) {
        const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
        const data = await this.request(endpoint, {
            ...options,
            method: 'POST',
            body: isFormData ? body : JSON.stringify(body || {}),
        });
        return { data, status: 200 };
    }

    async patch(endpoint, body = {}, options = {}) {
        const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
        const data = await this.request(endpoint, {
            ...options,
            method: 'PATCH',
            body: isFormData ? body : JSON.stringify(body || {}),
        });
        return { data, status: 200 };
    }

    async put(endpoint, body = {}, options = {}) {
        const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
        const data = await this.request(endpoint, {
            ...options,
            method: 'PUT',
            body: isFormData ? body : JSON.stringify(body || {}),
        });
        return { data, status: 200 };
    }

    async delete(endpoint, options = {}) {
        const data = await this.request(endpoint, { ...options, method: 'DELETE' });
        return { data, status: 200 };
    }

    /**
     * Health check endpoint
     */
    async healthCheck() {
        return this.request('/health');
    }

    /**
     * Process farmer query through orchestrator
     */
    async processQuery(query, sessionId = null) {
        const payload = {
            query,
            session_id: sessionId,
        };

        return this.request('/orchestrator/process', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    /**
     * Get workflow status
     */
    async getWorkflowStatus(workflowId) {
        return this.request(`/orchestrator/workflow/${workflowId}/status`);
    }

    /**
     * Get session data
     */
    async getSession(sessionId) {
        return this.request(`/orchestrator/session/${sessionId}`);
    }

    /**
     * Update session preferences
     */
    async updateSession(sessionId, preferences) {
        return this.request(`/orchestrator/session/${sessionId}`, {
            method: 'PUT',
            body: JSON.stringify(preferences),
        });
    }

    /**
     * Get agent status for a specific workflow
     */
    async getAgentStatus(workflowId, agentName) {
        return this.request(`/orchestrator/workflow/${workflowId}/agent/${agentName}/status`);
    }

    /**
     * Get reasoning tree for a workflow
     */
    async getReasoningTree(workflowId) {
        return this.request(`/orchestrator/workflow/${workflowId}/reasoning`);
    }

    /**
     * Submit voice input
     */
    async submitVoiceInput(audioBlob, sessionId = null) {
        const formData = new FormData();
        formData.append('audio', audioBlob);
        if (sessionId) {
            formData.append('session_id', sessionId);
        }

        return this.request('/orchestrator/voice/process', {
            method: 'POST',
            headers: {}, // Let browser set Content-Type for FormData
            body: formData,
        });
    }

    /**
     * Get voice output (text-to-speech)
     */
    async getVoiceOutput(text, language = 'en') {
        return this.request('/orchestrator/voice/synthesize', {
            method: 'POST',
            body: JSON.stringify({ text, language }),
        });
    }

    /**
     * Get workflow history for a session
     */
    async getWorkflowHistory(sessionId) {
        return this.request(`/orchestrator/session/${sessionId}/workflows`);
    }

    /**
     * Get chat history of sessions
     */
    async getHistory() {
        return this.request('/super-agent/history');
    }

    /**
     * Cancel ongoing workflow
     */
    async cancelWorkflow(workflowId) {
        return this.request(`/orchestrator/workflow/${workflowId}/cancel`, {
            method: 'POST',
        });
    }

    /**
     * Get system status and available agents
     */
    async getSystemStatus() {
        return this.request('/orchestrator/status');
    }
}

// Create singleton instance
const apiService = new ApiService();

const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

export const api = {
    auth: {
        getSession: async () => {
            try {
                return await apiService.request('/auth/session');
            } catch (e) {
                return null;
            }
        },
    },
    admin: {
        me: async () => {
            return apiService.request('/admin/me', {
                headers: {
                    ...getAuthHeaders(),
                },
            });
        },
        listUsers: async ({ q, role, is_active, onboarding_completed, page = 1, page_size = 25 } = {}) => {
            const params = new URLSearchParams();
            params.set('page', String(page));
            params.set('page_size', String(page_size));
            if (q) params.set('q', q);
            if (role) params.set('role', role);
            if (is_active !== undefined && is_active !== null && is_active !== '') params.set('is_active', String(is_active));
            if (onboarding_completed !== undefined && onboarding_completed !== null && onboarding_completed !== '') params.set('onboarding_completed', String(onboarding_completed));

            return apiService.request(`/admin/users?${params.toString()}`, {
                headers: {
                    ...getAuthHeaders(),
                },
            });
        },
        suspendUser: async (userId, { reason, until } = {}) => {
            return apiService.request(`/admin/users/${userId}/suspend`, {
                method: 'POST',
                headers: {
                    ...getAuthHeaders(),
                },
                body: JSON.stringify({ reason, until }),
            });
        },
        unsuspendUser: async (userId) => {
            return apiService.request(`/admin/users/${userId}/unsuspend`, {
                method: 'POST',
                headers: {
                    ...getAuthHeaders(),
                },
            });
        },
        listFarms: async ({ user_id, q, page = 1, page_size = 25 } = {}) => {
            const params = new URLSearchParams();
            params.set('page', String(page));
            params.set('page_size', String(page_size));
            if (user_id !== undefined && user_id !== null && user_id !== '') params.set('user_id', String(user_id));
            if (q) params.set('q', q);

            return apiService.request(`/admin/farms?${params.toString()}`, {
                headers: {
                    ...getAuthHeaders(),
                },
            });
        },
        listIotDevices: async ({ farm_id, status, page = 1, page_size = 50 } = {}) => {
            const params = new URLSearchParams();
            params.set('page', String(page));
            params.set('page_size', String(page_size));
            if (farm_id !== undefined && farm_id !== null && farm_id !== '') params.set('farm_id', String(farm_id));
            if (status) params.set('status', status);

            return apiService.request(`/admin/iot/devices?${params.toString()}`, {
                headers: {
                    ...getAuthHeaders(),
                },
            });
        },
        listAiInteractions: async ({ farm_id, agent_name, success, page = 1, page_size = 25 } = {}) => {
            const params = new URLSearchParams();
            params.set('page', String(page));
            params.set('page_size', String(page_size));
            if (farm_id !== undefined && farm_id !== null && farm_id !== '') params.set('farm_id', String(farm_id));
            if (agent_name) params.set('agent_name', agent_name);
            if (success !== undefined && success !== null && success !== '') params.set('success', String(success));

            return apiService.request(`/admin/ai/interactions?${params.toString()}`, {
                headers: {
                    ...getAuthHeaders(),
                },
            });
        },
        listAuditEvents: async ({ actor_user_id, action_type, target_type, target_id, page = 1, page_size = 50 } = {}) => {
            const params = new URLSearchParams();
            params.set('page', String(page));
            params.set('page_size', String(page_size));
            if (actor_user_id !== undefined && actor_user_id !== null && actor_user_id !== '') params.set('actor_user_id', String(actor_user_id));
            if (action_type) params.set('action_type', action_type);
            if (target_type) params.set('target_type', target_type);
            if (target_id) params.set('target_id', target_id);

            return apiService.request(`/admin/audit/events?${params.toString()}`, {
                headers: {
                    ...getAuthHeaders(),
                },
            });
        },
    },
    hardware: {
        getDevices: async () => {
            try {
                const res = await apiService.request('/hardware/devices');
                return Array.isArray(res) ? res : (res?.devices || []);
            } catch (e) {
                return [];
            }
        },
    },
    fields: {
        getFields: async () => {
            try {
                const res = await apiService.request('/fields');
                return Array.isArray(res) ? res : (res?.fields || []);
            } catch (e) {
                return [];
            }
        },
    },
    logs: {
        addLog: async (payload) => {
            try {
                return await apiService.request('/logs', {
                    method: 'POST',
                    body: JSON.stringify(payload),
                });
            } catch (e) {
                return null;
            }
        },
    },
};

export default apiService;
export { apiService };
