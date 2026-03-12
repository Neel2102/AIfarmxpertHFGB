import React, { useState, useEffect } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, MessageSquare, Map, Mic, Users, Cpu, Settings,
  History, Plus, Sun, Moon, X, ChevronRight, Trash2
} from 'lucide-react';
import { useOrchestrator } from '../contexts/OrchestratorContext';
import apiService from '../services/api';
import { useAuth } from "../contexts/AuthContext";
import '../styles/Dashboard/Sidebar.css';

const Sidebar = ({ onLogout }) => {
  const navigate = useNavigate();
  const { chatHistory, session, loadSessionMessages, resetSession, loadHistory } = useOrchestrator();
  const { } = useAuth();

  const [isOpen, setIsOpen] = useState(true);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("theme") || "dark";
  });
  const [expandedCategories, setExpandedCategories] = useState({
    main_menu: true,
    history: true,
  });

  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [animationKeys, setAnimationKeys] = useState({
    main_menu: 0,
    history: 0,
  });
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);

      // Auto-close sidebar on mobile, auto-open on desktop
      if (mobile) {
        setIsOpen(false);
      } else {
        setIsOpen(true);
      }
    };

    // Set initial state
    handleResize();

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Reflect sidebar open/closed state on the root element for CSS to react to
  useEffect(() => {
    const root = document.documentElement;
    if (isOpen) {
      root.classList.add("sidebar-open");
      root.classList.remove("sidebar-closed");
    } else {
      root.classList.add("sidebar-closed");
      root.classList.remove("sidebar-open");
    }
  }, [isOpen]);

  // Handle theme
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  // Close profile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        showProfileMenu &&
        !event.target.closest(".sidebar-user-profile-sidebar")
      ) {
        setShowProfileMenu(false);
      }
    };

    if (showProfileMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showProfileMenu]);

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === "dark" ? "light" : "dark"));
  };

  const toggleCategory = (category) => {
    setExpandedCategories((prev) => {
      const newState = { ...prev, [category]: !prev[category] };

      if (newState[category]) {
        setAnimationKeys((prevKeys) => ({
          ...prevKeys,
          [category]: prevKeys[category] + 1,
        }));
      }

      return newState;
    });
  };

  const handleNavigation = (path) => {
    navigate(path);
    if (isMobile) {
      setIsOpen(false);
    }
  };

  // eslint-disable-next-line no-unused-vars
  const _toggleProfileMenu = () => {
    setShowProfileMenu(!showProfileMenu);
  };

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  const closeSidebar = () => {
    setIsOpen(false);
  };

  const handleDeleteChatHistory = async (sessionId, e) => {
    e.stopPropagation();
    console.log('[Sidebar] Attempting to delete session:', sessionId);
    const confirmed = window.confirm('Are you sure you want to delete this chat history?');
    if (!confirmed) return;
    try {
      console.log('[Sidebar] Sending DELETE request to:', `/super-agent/history/${sessionId}`);
      const result = await apiService.request(`/super-agent/history/${sessionId}`, { method: 'DELETE' });
      console.log('[Sidebar] DELETE success:', result);
      // Refresh history after deletion
      if (loadHistory) {
        console.log('[Sidebar] Reloading history...');
        await loadHistory();
      }
      // If deleted session was active, reset to new session
      if (session?.id === sessionId) {
        console.log('[Sidebar] Deleted session was active, resetting');
        resetSession();
        handleNavigation('/dashboard/orchestrator');
      }
    } catch (error) {
      console.error('[Sidebar] Failed to delete chat history:', error);
      alert(`Failed to delete chat history: ${error.message || 'Unknown error'}`);
    }
  };

  const sortedChatHistory = Array.isArray(chatHistory)
    ? [...chatHistory].sort((a, b) => {
      const ta = a?.updated_at ? Date.parse(a.updated_at) : 0;
      const tb = b?.updated_at ? Date.parse(b.updated_at) : 0;
      return tb - ta;
    })
    : [];

  return (
    <>
      {/* Hamburger Toggle Button - Visible on all screens */}
      <button
        className="sidebar-toggle-btn-sidebar"
        onClick={toggleSidebar}
        aria-label={isOpen ? "Close sidebar" : "Open sidebar"}
      >
        <svg
          viewBox="0 0 24 24"
          width="24"
          height="24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {isOpen ? (
            <>
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </>
          ) : (
            <>
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </>
          )}
        </svg>
      </button>

      {/* Overlay for mobile */}
      {isMobile && isOpen && (
        <div className="sidebar-overlay-sidebar" onClick={closeSidebar}></div>
      )}

      {/* Sidebar */}
      <div
        className={`sidebar-sidebar ${isOpen ? "sidebar-open-sidebar" : ""}`}
      >
        <div
          className={`sidebar-sidebar-content ${isOpen ? "sidebar-open-sidebar1" : ""
            }`}
        >
          <div className="sidebar-header-sidebar">
            <div className="logo-container-sidebar">
              <img src="/leaf.png" alt="FarmXpert" className="logo-icon-sidebar" />
              <div className="logo-text-sidebar">
                <h1 className="logo-title-sidebar">FarmXpert</h1>
                <p className="logo-tagline-sidebar">AI-Powered Farming</p>
              </div>
            </div>

            {isMobile && (
              <button className="close-btn-sidebar" onClick={closeSidebar}>
                <span className="close-icon-sidebar">×</span>
              </button>
            )}
          </div>

          <div className="theme-toggle-container-sidebar">
            <button
              className={`theme-toggle-sidebar ${theme === "dark" ? "dark-mode-sidebar" : "light-mode-sidebar"
                }`}
              onClick={toggleTheme}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
            >
              <div className="toggle-slider-sidebar">
                {theme === "dark" ? (
                  <svg
                    className="toggle-icon-svg-sidebar"
                    viewBox="0 0 24 24"
                    width="12"
                    height="12"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                    <circle cx="12" cy="12" r="1" fill="currentColor" />
                    <circle
                      cx="15"
                      cy="9"
                      r="0.5"
                      fill="currentColor"
                      opacity="0.6"
                    />
                    <circle
                      cx="9"
                      cy="15"
                      r="0.5"
                      fill="currentColor"
                      opacity="0.6"
                    />
                  </svg>
                ) : (
                  <svg
                    className="toggle-icon-svg-sidebar"
                    viewBox="0 0 24 24"
                    width="12"
                    height="12"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle
                      cx="12"
                      cy="12"
                      r="4"
                      fill="currentColor"
                      opacity="0.9"
                    />
                    <line x1="12" y1="1" x2="12" y2="3" />
                    <line x1="12" y1="21" x2="12" y2="23" />
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                    <line x1="1" y1="12" x2="3" y2="12" />
                    <line x1="21" y1="12" x2="23" y2="12" />
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                  </svg>
                )}
              </div>
            </button>
            <span className="theme-label-sidebar">
              {theme === "dark" ? "Dark" : "Light"} Mode
            </span>
          </div>

          <div className="agent-categories-sidebar">
            <div className="agent-category-sidebar">
              <div
                className="category-header-sidebar"
                onClick={() => toggleCategory("main_menu")}
              >
                <div className="category-left-sidebar">
                  <svg
                    className="category-icon-sidebar"
                    viewBox="0 0 24 24"
                    width="16"
                    height="16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <line x1="3" y1="12" x2="21" y2="12" />
                    <line x1="3" y1="6" x2="21" y2="6" />
                    <line x1="3" y1="18" x2="21" y2="18" />
                  </svg>
                  <span className="category-title-sidebar">Main Menu</span>
                </div>
                <span
                  className={`category-toggle-sidebar ${expandedCategories.main_menu ? "expanded-sidebar" : ""
                    }`}
                >
                  <svg viewBox="0 0 24 24" width="16" height="16">
                    <path d="M7 10l5 5 5-5z" fill="currentColor" />
                  </svg>
                </span>
              </div>

              <div
                className={`agent-list-sidebar ${expandedCategories.main_menu ? "expanded-sidebar" : ""
                  }`}
                key={`main_menu_${animationKeys.main_menu}`}
              >
                <NavLink
                  className={({ isActive }) => `agent-item-sidebar ${isActive ? 'active' : ''}`}
                  to="/dashboard/today"
                  onClick={() => handleNavigation("/dashboard/today")}
                >
                  <LayoutDashboard className="agent-icon-sidebar" size={20} />
                  <span className="agent-name-sidebar">Today</span>
                  <span className="agent-status-sidebar active-sidebar"></span>
                </NavLink>

                <NavLink
                  className={({ isActive }) => `agent-item-sidebar ${isActive ? 'active' : ''}`}
                  to="/dashboard/farm-information"
                  onClick={() => handleNavigation("/dashboard/farm-information")}
                >
                  <LayoutDashboard className="agent-icon-sidebar" size={20} />
                  <span className="agent-name-sidebar">Soil & Sensors</span>
                  <span className="agent-status-sidebar active-sidebar"></span>
                </NavLink>

                <NavLink
                  className={({ isActive }) => `agent-item-sidebar ${isActive ? 'active' : ''}`}
                  to="/dashboard/orchestrator"
                  onClick={() => handleNavigation("/dashboard/orchestrator")}
                >
                  <MessageSquare className="agent-icon-sidebar" size={20} />
                  <span className="agent-name-sidebar">Smart Chat</span>
                  <span className="agent-status-sidebar active-sidebar"></span>
                </NavLink>

                <NavLink
                  className={({ isActive }) =>
                    `agent-item-sidebar ${isActive ? "active" : ""}`}
                  to="/dashboard/farm-map"
                  onClick={() => handleNavigation("/dashboard/farm-map")}
                >
                  <Map className="agent-icon-sidebar" size={20} />
                  <span className="agent-name-sidebar">Farm Map</span>
                  <span className="agent-status-sidebar active-sidebar"></span>
                </NavLink>

                <NavLink
                  className={({ isActive }) =>
                    `agent-item-sidebar ${isActive ? "active" : ""}`}
                  to="/dashboard/voice"
                  onClick={() => handleNavigation("/dashboard/voice")}
                >
                  <Mic className="agent-icon-sidebar" size={20} />
                  <span className="agent-name-sidebar">Hands-Free Voice</span>
                  <span className="agent-status-sidebar active-sidebar"></span>
                </NavLink>

                <NavLink
                  className={({ isActive }) =>
                    `agent-item-sidebar ${isActive ? "active" : ""}`}
                  to="/dashboard/agents"
                  onClick={() => handleNavigation("/dashboard/agents")}
                >
                  <Users className="agent-icon-sidebar" size={20} />
                  <span className="agent-name-sidebar">Agent Catalog</span>
                  <span className="agent-status-sidebar active-sidebar"></span>
                </NavLink>

                <NavLink
                  className={({ isActive }) =>
                    `agent-item-sidebar ${isActive ? "active" : ""}`}
                  to="/dashboard/hardware-iot"
                  onClick={() => handleNavigation("/dashboard/hardware-iot")}
                >
                  <Cpu className="agent-icon-sidebar" size={20} />
                  <span className="agent-name-sidebar">Hardware IoT</span>
                  <span className="agent-status-sidebar active-sidebar"></span>
                </NavLink>

                <NavLink
                  className={({ isActive }) =>
                    `agent-item-sidebar ${isActive ? "active" : ""}`}
                  to="/dashboard/setting"
                  onClick={() => handleNavigation("/dashboard/setting")}
                >
                  <Settings className="agent-icon-sidebar" size={20} />
                  <span className="agent-name-sidebar">Settings</span>
                  <span className="agent-status-sidebar active-sidebar"></span>
                </NavLink>
              </div>
            </div>

            {/* Chat History Category */}
            <div className="agent-category-sidebar">
              <div
                className="category-header-sidebar"
                onClick={() => toggleCategory("history")}
              >
                <div className="category-left-sidebar">
                  <History className="category-icon-sidebar" size={16} />
                  <span className="category-title-sidebar">Chat History</span>
                </div>
                <div className="category-actions-sidebar">
                  <button 
                    className="new-chat-btn-sidebar" 
                    onClick={(e) => {
                      e.stopPropagation();
                      resetSession();
                      handleNavigation("/dashboard/orchestrator");
                    }}
                    title="Start New Chat"
                  >
                    <Plus size={14} />
                  </button>
                  <span
                    className={`category-toggle-sidebar ${expandedCategories.history ? "expanded-sidebar" : ""
                      }`}
                  >
                    <svg viewBox="0 0 24 24" width="16" height="16">
                      <path d="M7 10l5 5 5-5z" fill="currentColor" />
                    </svg>
                  </span>
                </div>
              </div>

              <div
                className={`agent-list-sidebar ${expandedCategories.history ? "expanded-sidebar" : ""
                  }`}
                key={`history_${animationKeys.history}`}
              >
                {sortedChatHistory.length > 0 ? (
                  sortedChatHistory.map((s) => (
                    <div
                      key={s.session_id}
                      className={`agent-item-sidebar ${session?.id === s.session_id ? "active" : ""}`}
                      role="button"
                      tabIndex={0}
                      onClick={async (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('[Sidebar] Clicked history session:', s.session_id, s.title);
                        await loadSessionMessages(s.session_id);
                        console.log('[Sidebar] loadSessionMessages completed, navigating to orchestrator');
                        handleNavigation("/dashboard/orchestrator");
                      }}
                      onKeyDown={async (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          e.stopPropagation();
                          console.log('[Sidebar] Clicked history session:', s.session_id, s.title);
                          await loadSessionMessages(s.session_id);
                          console.log('[Sidebar] loadSessionMessages completed, navigating to orchestrator');
                          handleNavigation("/dashboard/orchestrator");
                        }
                      }}
                    >
                      <MessageSquare className="agent-icon-sidebar" size={18} />
                      <div className="agent-info-container-sidebar">
                        <span className="agent-name-sidebar">{s.title || "New chat"}</span>
                        <span className="agent-meta-sidebar">
                          {(typeof s.message_count === 'number' ? s.message_count : 0)} messages
                        </span>
                      </div>
                      <button
                        className="chat-history-delete-btn"
                        onClick={(e) => handleDeleteChatHistory(s.session_id, e)}
                        title="Delete chat history"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="empty-history-sidebar">
                    No history yet
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="sidebar-footer-sidebar">
            <div className="footer-text-sidebar">
              <span> 2024 FarmXpert</span>
              <span>v2.1.0</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;