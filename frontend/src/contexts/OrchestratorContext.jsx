import React, { createContext, useContext, useReducer, useEffect } from 'react';
import apiService from '../services/api';

// Action types
const ACTIONS = {
    SET_LOADING: 'SET_LOADING',
    SET_ERROR: 'SET_ERROR',
    SET_SESSION: 'SET_SESSION',
    SET_WORKFLOW: 'SET_WORKFLOW',
    UPDATE_AGENT_STATUS: 'UPDATE_AGENT_STATUS',
    ADD_MESSAGE: 'ADD_MESSAGE',
    SET_REASONING_TREE: 'SET_REASONING_TREE',
    CLEAR_WORKFLOW: 'CLEAR_WORKFLOW',
    SET_SYSTEM_STATUS: 'SET_SYSTEM_STATUS',
    SET_HISTORY: 'SET_HISTORY',
    CLEAR_MESSAGES: 'CLEAR_MESSAGES',
    RESET_SESSION: 'RESET_SESSION',
};

// Initial state
const initialState = {
    loading: false,
    error: null,
    session: null,
    currentWorkflow: null,
    agentStatuses: {},
    messages: [],
    reasoningTree: null,
    systemStatus: null,
    chatHistory: [],
};

// Reducer function
function orchestratorReducer(state, action) {
    switch (action.type) {
        case ACTIONS.SET_LOADING:
            return { ...state, loading: action.payload };

        case ACTIONS.SET_ERROR:
            return { ...state, error: action.payload, loading: false };

        case ACTIONS.SET_SESSION:
            return { ...state, session: action.payload };

        case ACTIONS.SET_WORKFLOW:
            return {
                ...state,
                currentWorkflow: action.payload,
                loading: false,
                error: null
            };

        case ACTIONS.UPDATE_AGENT_STATUS:
            return {
                ...state,
                agentStatuses: {
                    ...state.agentStatuses,
                    [action.payload.agentName]: action.payload.status
                }
            };

        case ACTIONS.ADD_MESSAGE:
            if (Array.isArray(action.payload)) {
                return { ...state, messages: action.payload };
            }
            return {
                ...state,
                messages: [...state.messages, action.payload]
            };

        case 'SET_MESSAGES':
            const newMessages = typeof action.payload === 'function' 
                ? action.payload(state.messages) 
                : action.payload;
            return { ...state, messages: newMessages };

        case ACTIONS.SET_REASONING_TREE:
            return { ...state, reasoningTree: action.payload };

        case ACTIONS.CLEAR_WORKFLOW:
            return {
                ...state,
                currentWorkflow: null,
                agentStatuses: {},
                reasoningTree: null,
                error: null
            };

        case ACTIONS.SET_SYSTEM_STATUS:
            return { ...state, systemStatus: action.payload };

        case ACTIONS.SET_HISTORY:
            return { ...state, chatHistory: action.payload };

        case ACTIONS.CLEAR_MESSAGES:
            return { ...state, messages: [] };

        case ACTIONS.RESET_SESSION:
            return { 
                ...state, 
                session: null, 
                messages: [],
                currentWorkflow: null,
                agentStatuses: {},
                reasoningTree: null 
            };

        default:
            return state;
    }
}

// Create context
const OrchestratorContext = createContext();

// Provider component
export function OrchestratorProvider({ children }) {
    const [state, dispatch] = useReducer(orchestratorReducer, initialState);

    // Initialize system status on mount
    useEffect(() => {
        initializeSystem();
        loadHistory();
    }, []);

    const initializeSystem = async () => {
        try {
            dispatch({ type: ACTIONS.SET_LOADING, payload: true });
            const status = await apiService.getSystemStatus();
            dispatch({ type: ACTIONS.SET_SYSTEM_STATUS, payload: status });
        } catch (error) {
            dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
        }
    };

    const processQuery = async (query, sessionId = null) => {
        try {
            dispatch({ type: ACTIONS.SET_LOADING, payload: true });
            dispatch({ type: ACTIONS.SET_ERROR, payload: null });

            // Add user message
            dispatch({
                type: ACTIONS.ADD_MESSAGE,
                payload: {
                    id: Date.now(),
                    type: 'user',
                    content: query,
                    timestamp: new Date().toISOString()
                }
            });

            const response = await apiService.processQuery(query, sessionId);

            // Set workflow
            dispatch({ type: ACTIONS.SET_WORKFLOW, payload: response.workflow });

            // Set session if provided
            if (response.session) {
                dispatch({ type: ACTIONS.SET_SESSION, payload: response.session });
            }

            // Add system response
            dispatch({
                type: ACTIONS.ADD_MESSAGE,
                payload: {
                    id: Date.now() + 1,
                    type: 'system',
                    content: response.response,
                    timestamp: new Date().toISOString(),
                    workflowId: response.workflow?.id
                }
            });

            await loadHistory();

            return response;
        } catch (error) {
            dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
            throw error;
        }
    };

    const loadHistory = async () => {
        try {
            const result = await apiService.getHistory();
            const sessions = Array.isArray(result)
                ? result
                : (result?.sessions || []);
            dispatch({ type: ACTIONS.SET_HISTORY, payload: sessions });
            return sessions;
        } catch (error) {
            console.error('Failed to load history:', error);
            // Don't throw to not disrupt the main flow
            return [];
        }
    };

    const loadSessionMessages = async (sessionId) => {
        console.log('[OrchestratorContext] loadSessionMessages called with sessionId:', sessionId);
        try {
            dispatch({ type: ACTIONS.SET_LOADING, payload: true });

            dispatch({
                type: ACTIONS.SET_SESSION,
                payload: { id: sessionId }
            });

            localStorage.setItem('farmxpert_session_id', sessionId);
            console.log('[OrchestratorContext] session id saved to localStorage:', sessionId);

            // Get history for this session specifically
            const result = await apiService.request(`/super-agent/history?session_id=${sessionId}`);
            console.log('[OrchestratorContext] API result for session messages:', result);
            console.log('[OrchestratorContext] typeof result:', typeof result, 'Array.isArray?', Array.isArray(result));

            // Handle different response structures
            let messagesData = null;
            if (Array.isArray(result)) {
                messagesData = result;
            } else if (result && result.messages && Array.isArray(result.messages)) {
                messagesData = result.messages;
            } else if (result && result.data && Array.isArray(result.data)) {
                messagesData = result.data;
            }

            console.log('[OrchestratorContext] messagesData extracted:', messagesData);

            if (messagesData && messagesData.length > 0) {
                // Convert simple text messages format to UI messages
                const formattedMessages = messagesData.map((m, idx) => ({
                    id: Date.now() + idx,
                    type: m.role === 'user' ? 'user' : 'assistant',
                    content: m.content || m.message || String(m),
                    timestamp: new Date().toISOString()
                }));

                dispatch({ type: 'SET_MESSAGES', payload: formattedMessages });
                dispatch({ type: ACTIONS.SET_LOADING, payload: false });
                console.log('[OrchestratorContext] messages loaded and dispatched:', formattedMessages.length);
                return formattedMessages;
            }

            dispatch({ type: 'SET_MESSAGES', payload: [] });
            dispatch({ type: ACTIONS.SET_LOADING, payload: false });
            console.log('[OrchestratorContext] no messages found for session:', sessionId);
            return [];
        } catch (error) {
            console.error('[OrchestratorContext] Failed to load session messages:', error);
            dispatch({ type: ACTIONS.SET_LOADING, payload: false });
            return [];
        }
    };

    const getWorkflowStatus = async (workflowId) => {
        try {
            const status = await apiService.getWorkflowStatus(workflowId);

            // Update agent statuses
            if (status.agents) {
                Object.entries(status.agents).forEach(([agentName, agentStatus]) => {
                    dispatch({
                        type: ACTIONS.UPDATE_AGENT_STATUS,
                        payload: { agentName, status: agentStatus }
                    });
                });
            }

            // Update workflow status
            if (status.workflow) {
                dispatch({ type: ACTIONS.SET_WORKFLOW, payload: status.workflow });
            }

            return status;
        } catch (error) {
            dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
            throw error;
        }
    };

    const getReasoningTree = async (workflowId) => {
        try {
            const reasoningTree = await apiService.getReasoningTree(workflowId);
            dispatch({ type: ACTIONS.SET_REASONING_TREE, payload: reasoningTree });
            return reasoningTree;
        } catch (error) {
            dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
            throw error;
        }
    };

    const submitVoiceInput = async (audioBlob, sessionId = null) => {
        try {
            dispatch({ type: ACTIONS.SET_LOADING, payload: true });
            const response = await apiService.submitVoiceInput(audioBlob, sessionId);

            // Process the voice input response
            if (response.query) {
                await processQuery(response.query, sessionId);
            }

            return response;
        } catch (error) {
            dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
            throw error;
        }
    };

    const getVoiceOutput = async (text, language = 'en') => {
        try {
            return await apiService.getVoiceOutput(text, language);
        } catch (error) {
            dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
            throw error;
        }
    };

    const updateSession = async (preferences) => {
        try {
            if (!state.session?.id) {
                throw new Error('No active session');
            }

            const updatedSession = await apiService.updateSession(state.session.id, preferences);
            dispatch({ type: ACTIONS.SET_SESSION, payload: updatedSession });
            return updatedSession;
        } catch (error) {
            dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
            throw error;
        }
    };

    const cancelWorkflow = async (workflowId) => {
        try {
            await apiService.cancelWorkflow(workflowId);
            dispatch({ type: ACTIONS.CLEAR_WORKFLOW });
        } catch (error) {
            dispatch({ type: ACTIONS.SET_ERROR, payload: error.message });
            throw error;
        }
    };

    const resetSession = () => {
        const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('farmxpert_session_id', newSessionId);
        dispatch({ type: ACTIONS.RESET_SESSION });
        dispatch({ type: ACTIONS.SET_SESSION, payload: { id: newSessionId } });
        return newSessionId;
    };

    const clearMessages = () => {
        dispatch({ type: ACTIONS.CLEAR_MESSAGES });
    };

    const clearError = () => {
        dispatch({ type: ACTIONS.SET_ERROR, payload: null });
    };

    const clearWorkflow = () => {
        dispatch({ type: ACTIONS.CLEAR_WORKFLOW });
    };

    const addMessage = (message) => {
        dispatch({ type: ACTIONS.ADD_MESSAGE, payload: message });
    };

    const setMessages = (messages) => {
        dispatch({ type: 'SET_MESSAGES', payload: messages });
    };

    const value = {
        ...state,
        processQuery,
        getWorkflowStatus,
        getReasoningTree,
        submitVoiceInput,
        getVoiceOutput,
        updateSession,
        cancelWorkflow,
        clearError,
        clearWorkflow,
        addMessage,
        setMessages,
        initializeSystem,
        loadHistory,
        loadSessionMessages,
        resetSession,
        clearMessages,
    };

    return (
        <OrchestratorContext.Provider value={value}>
            {children}
        </OrchestratorContext.Provider>
    );
}

// Custom hook to use the orchestrator context
export function useOrchestrator() {
    const context = useContext(OrchestratorContext);
    if (!context) {
        throw new Error('useOrchestrator must be used within an OrchestratorProvider');
    }
    return context;
}
