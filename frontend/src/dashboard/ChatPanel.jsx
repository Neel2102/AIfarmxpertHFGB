import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, Bot, BarChart3, Droplets, ThermometerSun, FlaskConical, Sprout, Calendar, Zap, Circle, Bug, Cloud, TrendingUp, Clock, Truck, MapPin, DollarSign, Leaf, Package, ShoppingCart, Shield, GraduationCap, Users, Camera, Mic, MicOff, Paperclip, X } from 'lucide-react';
import { useOrchestrator } from '../contexts/OrchestratorContext';
import '../styles/Dashboard/ChatPanel.css';
import '../styles/Dashboard/ChatPanel-reasoning.css';

// Fallback to localhost:8000 if the env variable isn't set yet
const API_BASE_URL = '/api';

/** Read the stored JWT and return an Authorization header object. */
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const ChatPanel = ({ agent, farmData, sessionId }) => {
  const navigate = useNavigate();
  const { messages: contextMessages } = useOrchestrator();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // ── Media state ──────────────────────────────────────────────────────────
  const [attachedImage, setAttachedImage] = useState(null);   // { file, preview }
  const [attachedFile, setAttachedFile]   = useState(null);   // { file }
  const [isRecording, setIsRecording]     = useState(false);
  const [audioBlob, setAudioBlob]         = useState(null);   // Blob
  const imageInputRef  = useRef(null);
  const fileInputRef   = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef   = useRef([]);

  useEffect(() => {
    if (contextMessages && contextMessages.length > 0) {
      setMessages(
        contextMessages.map((m) => ({
          ...m,
          content: typeof m?.content === 'string'
            ? m.content
                .replace(/<[^>]*>/g, '')
                .replace(/\b\w+">/g, '')
                .replace(/\bclass="[^"]*"/g, '')
            : m?.content,
        }))
      );
    } else {
      setMessages([{
        id: Date.now(),
        type: 'system',
        content: `Welcome to ${getAgentDisplayName(agent)} !`,
        timestamp: new Date().toISOString()
      }]);
    }
  }, [agent, contextMessages]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isDropdownOpen && !event.target.closest('.agent-dropdown')) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputValue]);

  const getAgentDisplayName = (name) => {
    const map = {
      'super-agent': 'SuperAgent',
      'crop_selector': 'Crop Selector Agent',
      'seed_selection': 'Seed Selection Agent',
      'soil_health': 'Soil Health Agent',
      'fertilizer_advisor': 'Fertilizer Advisor Agent',
      'irrigation_planner': 'Irrigation Planner Agent',
      'pest_disease_diagnostic': 'Pest & Disease Diagnostic Agent',
      'weather_watcher': 'Weather Watcher Agent',
      'growth_stage_monitor': 'Growth Stage Monitor Agent',
      'task_scheduler': 'Task Scheduler Agent',
      'machinery_manager': 'Machinery & Equipment Agent',
      'drone_commander': 'Drone Command Agent',
      'layout_mapper': 'Farm Layout & Mapping Agent',
      'yield_predictor': 'Yield Predictor Agent',
      'profit_optimization': 'Profit Optimization Agent',
      'sustainability_tracker': 'Carbon & Sustainability Agent',
      'market_intelligence': 'Market Intelligence Agent'
    };
    return map[name] || name;
  };

  const agentOptions = [
    // Super Agent
    { id: 'orchestrator', name: 'Super Agent', icon: Bot, path: '/dashboard/orchestrator' },

    // Crop Planning & Growth
    { id: 'crop-selector', name: 'Crop Selector', icon: Sprout, path: '/dashboard/orchestrator/crop-selector' },
    { id: 'seed-selection', name: 'Seed Selection', icon: Circle, path: '/dashboard/orchestrator/seed-selection' },
    { id: 'soil-health', name: 'Soil Health', icon: FlaskConical, path: '/dashboard/orchestrator/soil-health' },
    { id: 'fertilizer-advisor', name: 'Fertilizer Advisor', icon: Droplets, path: '/dashboard/orchestrator/fertilizer-advisor' },
    { id: 'irrigation-planner', name: 'Irrigation Planner', icon: ThermometerSun, path: '/dashboard/orchestrator/irrigation-planner' },
    { id: 'pest-diagnostic', name: 'Pest & Disease Diagnostic', icon: Bug, path: '/dashboard/orchestrator/pest-diagnostic' },
    { id: 'weather-watcher', name: 'Weather Watcher', icon: Cloud, path: '/dashboard/orchestrator/weather-watcher' },
    { id: 'growth-monitor', name: 'Growth Stage Monitor', icon: TrendingUp, path: '/dashboard/orchestrator/growth-monitor' },

    // Farm Operations & Automation
    { id: 'task-scheduler', name: 'Task Scheduler', icon: Clock, path: '/dashboard/orchestrator/task-scheduler' },
    { id: 'machinery-manager', name: 'Machinery & Equipment', icon: Truck, path: '/dashboard/orchestrator/machinery-manager' },
    { id: 'drone-commander', name: 'Drone Command', icon: Zap, path: '/dashboard/orchestrator/drone-commander' },
    { id: 'layout-mapper', name: 'Farm Layout & Mapping', icon: MapPin, path: '/dashboard/orchestrator/layout-mapper' },

    // Analytics
    { id: 'yield-predictor', name: 'Yield Predictor', icon: BarChart3, path: '/dashboard/orchestrator/yield-predictor' },
    { id: 'profit-optimizer', name: 'Profit Optimization', icon: DollarSign, path: '/dashboard/orchestrator/profit-optimizer' },
    { id: 'sustainability-tracker', name: 'Carbon & Sustainability', icon: Leaf, path: '/dashboard/orchestrator/sustainability-tracker' },
    { id: 'market-intelligence', name: 'Market Intelligence', icon: Calendar, path: '/dashboard/orchestrator/market-intelligence' },

    // Supply Chain & Market Access
    { id: 'logistics-storage', name: 'Logistics & Storage', icon: Package, path: '/dashboard/orchestrator/logistics-storage' },
    { id: 'input-procurement', name: 'Input Procurement', icon: ShoppingCart, path: '/dashboard/orchestrator/input-procurement' },
    { id: 'crop-insurance-risk', name: 'Crop Insurance & Risk', icon: Shield, path: '/dashboard/orchestrator/crop-insurance-risk' },

    // Farmer Support & Education
    { id: 'farmer-coach', name: 'Farmer Coach', icon: GraduationCap, path: '/dashboard/orchestrator/farmer-coach' },
    { id: 'compliance-certification', name: 'Compliance & Certification', icon: Shield, path: '/dashboard/orchestrator/compliance-certification' },
    { id: 'community-engagement', name: 'Community Engagement', icon: Users, path: '/dashboard/orchestrator/community-engagement' }
  ];

  const handleAgentChange = (selectedAgent) => {
    navigate(selectedAgent.path);
    setIsDropdownOpen(false);
  };

  const getCurrentAgentName = () => {
    const currentAgent = agentOptions.find(option => option.id === agent);
    return currentAgent ? currentAgent.name : getAgentDisplayName(agent);
  };

  const cleanText = (text) => {
    if (!text) return '';
    return text
      .replace(/<[^>]*>/g, '')
      .replace(/\b\w+">/g, '')
      .replace(/\bclass="[^"]*"/g, '')
      .replace(/^["']|["']$/g, '') 
      .replace(/^\s*(-{1,}|—{1,})\s*$/gm, '')
      .replace(/\n\s*\n\s*\n/g, '\n\n')
      .replace(/\n\s*-\s*-\s*/g, '\n- ')
      .replace(/\n\s*-\s*/g, '\n- ')
      .replace(/\n\s*\*\s*/g, '\n- ')
      .trim();
  };

  const renderMarkdownText = (text) => {
    if (!text) return null;

    const codeBlocks = [];
    let result = String(text);

    result = result.replace(/```([\s\S]*?)```/g, (_m, code) => {
      const idx = codeBlocks.length;
      codeBlocks.push(String(code || '').trimEnd());
      return `__CODEBLOCK_${idx}__`;
    });

    const renderInline = (raw) => {
      const s = String(raw ?? '');
      const parts = [];
      const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
      let lastIndex = 0;
      let match;
      while ((match = pattern.exec(s)) !== null) {
        const idx = match.index;
        if (idx > lastIndex) {
          parts.push(s.slice(lastIndex, idx));
        }
        const token = match[0];
        if (token.startsWith('`') && token.endsWith('`')) {
          parts.push(<code key={`${idx}-code`} className="inline-code">{token.slice(1, -1)}</code>);
        } else if (token.startsWith('**') && token.endsWith('**')) {
          parts.push(<strong key={`${idx}-b`} className="bold-text">{token.slice(2, -2)}</strong>);
        } else if (token.startsWith('*') && token.endsWith('*')) {
          parts.push(<em key={`${idx}-i`} className="italic-text">{token.slice(1, -1)}</em>);
        } else {
          parts.push(token);
        }
        lastIndex = idx + token.length;
      }
      if (lastIndex < s.length) {
        parts.push(s.slice(lastIndex));
      }
      return parts;
    };

    const lines = result.split('\n');
    return lines.map((line, lineIndex) => {
      const codeMatch = line.match(/__CODEBLOCK_(\d+)__/);
      if (codeMatch) {
        const idx = Number(codeMatch[1]);
        const code = codeBlocks[idx] || '';
        return (
          <pre key={lineIndex} className="code-block">
            {code}
          </pre>
        );
      }

      if (line.trim() === '') {
        return <div key={lineIndex} className="text-line empty-line"></div>;
      }

      if (line.trim().startsWith('#### ')) {
        const title = line.trim().slice(5);
        return (
          <h4 key={lineIndex} className="markdown-header">
            {renderInline(title)}
          </h4>
        );
      }

      if (line.trim().startsWith('### ')) {
        const title = line.trim().slice(4);
        return (
          <h4 key={lineIndex} className="markdown-header">
            {renderInline(title)}
          </h4>
        );
      }

      if (line.trim().startsWith('## ')) {
        const title = line.trim().slice(3);
        return (
          <h3 key={lineIndex} className="markdown-header">
            {renderInline(title)}
          </h3>
        );
      }

      if (line.trim().startsWith('# ')) {
        const title = line.trim().slice(2);
        return (
          <h2 key={lineIndex} className="markdown-header">
            {renderInline(title)}
          </h2>
        );
      }

      if (line.trim().endsWith(':')) {
        return (
          <div key={lineIndex} className="text-line section-header">
            <span>{renderInline(line)}</span>
          </div>
        );
      }
      if (line.trim().startsWith('-') || line.trim().startsWith('*')) {
        const cleanLine = line.replace(/^[\s]*[-*]\s*/, '');
        return (
          <div key={lineIndex} className="text-line bullet-point">
            <span>{renderInline(cleanLine)}</span>
          </div>
        );
      }
      if (/^\d+\.\s/.test(line.trim())) {
        return (
          <div key={lineIndex} className="text-line numbered-point">
            <span>{renderInline(line)}</span>
          </div>
        );
      }
      return (
        <div key={lineIndex} className="text-line regular-text">
          <span>{renderInline(line)}</span>
        </div>
      );
    });
  };

  const renderStructuredText = (text) => {
    const cleanedText = cleanText(text);
    return renderMarkdownText(cleanedText);
  };

  const getDataSourcesFromToolsUsed = (toolsUsed) => {
    const tools = Array.isArray(toolsUsed) ? toolsUsed : [];
    const sources = [];

    if (tools.includes('market') || tools.includes('mandi')) {
      sources.push('APMC / Mandi market prices');
    }
    if (tools.includes('weather')) {
      sources.push('Weather API');
    }
    if (tools.includes('soil')) {
      sources.push('Soil analysis');
    }
    if (tools.includes('crop')) {
      sources.push('Crop planning database/tools');
    }
    if (tools.includes('fertilizer')) {
      sources.push('Fertilizer recommendations');
    }
    if (tools.includes('irrigation')) {
      sources.push('Irrigation planning');
    }
    if (tools.includes('iot')) {
      sources.push('IoT sensor readings');
    }
    if (tools.includes('web_search')) {
      sources.push('Web search');
    }

    return sources;
  };

  const formatTime = (timestamp) => new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // ==========================================
  // MEDIA HELPER FUNCTIONS
  // ==========================================

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setAttachedImage({ file, preview: ev.target.result });
    reader.readAsDataURL(file);
    // Clear file attachment if switching
    setAttachedFile(null);
    setAudioBlob(null);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAttachedFile({ file });
    setAttachedImage(null);
    setAudioBlob(null);
  };

  const clearAttachments = () => {
    setAttachedImage(null);
    setAttachedFile(null);
    setAudioBlob(null);
    if (imageInputRef.current)  imageInputRef.current.value = '';
    if (fileInputRef.current)   fileInputRef.current.value = '';
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(t => t.stop());
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setIsRecording(true);
      setAttachedImage(null);
      setAttachedFile(null);
    } catch (err) {
      console.error('Microphone access denied:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // ==========================================
  // UNIFIED API ROUTING LOGIC
  // ==========================================
  const sendMessage = async () => {
    const text = inputValue.trim();
    const hasAudio   = !!audioBlob;
    const hasImage   = !!attachedImage;
    const hasFile    = !!attachedFile;

    if (!text && !hasAudio && !hasImage && !hasFile) return;
    if (isLoading) return;

    // 1. Add User Message (with attachment label)
    let userContent = text;
    if (hasImage)   userContent = `[📷 Image: ${attachedImage.file.name}] ${text}`;
    if (hasFile)    userContent = `[📎 ${attachedFile.file.name}] ${text}`;
    if (hasAudio)   userContent = `[🎤 Voice message] ${text}`;

    const userMessage = { id: Date.now(), type: 'user', content: userContent, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // 2. Add Streaming Placeholder
    const assistantMessageId = Date.now() + 1;
    setMessages((prev) => [...prev, { id: assistantMessageId, type: 'assistant', content: '', timestamp: new Date().toISOString(), isStreaming: true }]);

    try {
      let data = null;

      // ── Voice: audio blob → /api/chat/voice ──────────────────────────────
      if (hasAudio) {
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');
        formData.append('language', 'en');

        const response = await fetch(`${API_BASE_URL}/chat/voice`, { method: 'POST', body: formData, headers: getAuthHeaders() });
        if (!response.ok) throw new Error(`Voice error: ${response.status}`);

        // Response is MP3 audio
        const audioArrayBuffer = await response.arrayBuffer();
        const audioUrl = URL.createObjectURL(new Blob([audioArrayBuffer], { type: 'audio/mpeg' }));
        const transcript  = decodeURIComponent(response.headers.get('X-Transcript') || '');
        const textAnswer  = decodeURIComponent(response.headers.get('X-Text-Response') || '');

        setMessages((prev) => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: textAnswer || 'Voice response received.', audioUrl, transcript, isStreaming: false }
            : msg
        ));
        clearAttachments();
        return;
      }

      // ── Image: → /api/chat/vision ─────────────────────────────────────────
      if (hasImage) {
        const formData = new FormData();
        formData.append('file', attachedImage.file);
        if (text) formData.append('prompt', text);

        const response = await fetch(`${API_BASE_URL}/chat/vision`, { method: 'POST', body: formData, headers: getAuthHeaders() });
        if (!response.ok) throw new Error(`Vision error: ${response.status}`);
        data = await response.json();

        setMessages((prev) => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: data.response || 'Image analyzed.', visionResult: data.vision_result, isStreaming: false }
            : msg
        ));
        clearAttachments();
        return;
      }

      // ── Document: → /api/chat/document ───────────────────────────────────
      if (hasFile) {
        const formData = new FormData();
        formData.append('file', attachedFile.file);
        formData.append('prompt', text || 'Analyze this document');

        const response = await fetch(`${API_BASE_URL}/chat/document`, { method: 'POST', body: formData, headers: getAuthHeaders() });
        if (!response.ok) throw new Error(`Document error: ${response.status}`);
        data = await response.json();

        setMessages((prev) => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: data.response || 'Document analyzed.', isStreaming: false }
            : msg
        ));
        clearAttachments();
        return;
      }

      // ── Text chat: → /api/chat/orchestrate ───────────────────────────────
      const response = await fetch(`${API_BASE_URL}/chat/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });

      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
      data = await response.json();

      const content = data?.response || data?.message || 'No response received.';
      setMessages((prev) => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content, agent_responses: Array.isArray(data?.agent_responses) ? data.agent_responses : [], isStreaming: false }
          : msg
      ));

    } catch (e) {
      console.error('Chat error:', e);
      setMessages((prev) => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: `Error: ${e.message || 'Could not connect to AI. Ensure backend is running.'}`, isStreaming: false }
          : msg
      ));
    } finally {
      setIsLoading(false);
      clearAttachments();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const setSuggestionText = (text) => {
    setInputValue(text);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  // ==========================================
  // VISION DIAGNOSTIC CARD RENDERER
  // ==========================================
  const renderVisionCard = (visionResult) => {
    if (!visionResult) return null;
    const confidence = Math.round((parseFloat(visionResult.confidence) || 0) * 100);
    const severity = visionResult.severity || 'unknown';
    const severityColor = { none: '#22c55e', mild: '#eab308', moderate: '#f97316', severe: '#ef4444', unknown: '#94a3b8' }[severity] || '#94a3b8';
    return (
      <div style={{ background: 'linear-gradient(135deg,#0f172a,#1e293b)', border: '1px solid #334155', borderRadius: '12px', padding: '16px', marginTop: '10px', color: '#e2e8f0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <span style={{ fontSize: '20px' }}>🔬</span>
          <span style={{ fontWeight: 700, fontSize: '15px', color: '#f8fafc' }}>Pest & Disease Diagnosis</span>
        </div>
        <div style={{ display: 'grid', gap: '8px' }}>
          <div><span style={{ color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Diagnosis</span><div style={{ fontWeight: 600, color: '#f8fafc', marginTop: '2px' }}>{visionResult.diagnosis || 'Unknown'}</div></div>
          <div style={{ display: 'flex', gap: '16px' }}>
            <div><span style={{ color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase' }}>Confidence</span><div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}><div style={{ flex: 1, height: '6px', background: '#334155', borderRadius: '3px', minWidth: '80px' }}><div style={{ width: `${confidence}%`, height: '100%', background: '#22c55e', borderRadius: '3px' }}></div></div><span style={{ fontSize: '12px', fontWeight: 600 }}>{confidence}%</span></div></div>
            <div><span style={{ color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase' }}>Severity</span><div style={{ marginTop: '4px', display: 'inline-block', padding: '2px 10px', borderRadius: '20px', background: severityColor + '22', border: `1px solid ${severityColor}`, color: severityColor, fontSize: '12px', fontWeight: 600, textTransform: 'capitalize' }}>{severity}</div></div>
          </div>
          {visionResult.description && <div><span style={{ color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase' }}>Observation</span><div style={{ color: '#cbd5e1', fontSize: '13px', marginTop: '2px' }}>{visionResult.description}</div></div>}
          {visionResult.recommended_treatment?.length > 0 && (
            <div><span style={{ color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase' }}>Recommended Treatment</span><ul style={{ margin: '4px 0 0 0', padding: '0 0 0 16px', color: '#cbd5e1', fontSize: '13px' }}>{visionResult.recommended_treatment.map((t, i) => <li key={i}>{t}</li>)}</ul></div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="communication-panel">
      <h3>{agent === 'super-agent' ? 'Farm Orchestrator Chat' : `${getAgentDisplayName(agent)} Chat`}</h3>
      <div className="message-container">
        {messages.map((m) => (
          <div key={m.id} className="message" data-type={m.type}>
            <div className="message-header">
              <span className="message-agent">{m.type === 'user' ? 'You' : (agent === 'super-agent' ? 'Farm Orchestrator' : getAgentDisplayName(agent))}</span>
              <span className="message-time">{formatTime(m.timestamp)}</span>
            </div>
            <div className="message-content">
              {m.type === 'assistant' ? (
                <div>
                  {renderStructuredText(m.content)}
                  {m.isStreaming && (
                    <div className="typing-indicator"><span></span><span></span><span></span></div>
                  )}
                  {/* Vision Diagnostic Card */}
                  {m.visionResult && !m.isStreaming && renderVisionCard(m.visionResult)}
                  {/* Audio playback for voice responses */}
                  {m.audioUrl && !m.isStreaming && (
                    <div style={{ marginTop: '10px' }}>
                      <audio controls autoPlay src={m.audioUrl} style={{ width: '100%', borderRadius: '8px' }} />
                      {m.transcript && <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>🎤 Heard: "{m.transcript}"</div>}
                    </div>
                  )}
                  {/* Agent chips */}
                  {m.agent_responses?.length > 0 && !m.isStreaming && (
                    <div className="consulted-agents-row" style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '11px', color: '#9ca3af', alignSelf: 'center', fontWeight: 500 }}>INPUTS FROM:</span>
                      {m.agent_responses.filter(a => a.success).map((agentR, i) => (
                        <span key={i} style={{ fontSize: '11px', background: '#f8fafc', color: '#64748b', padding: '4px 10px', borderRadius: '12px', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 500 }}>
                          ⚡ {getAgentDisplayName(agentR.agent_name)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                m.content
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      {/* Hidden file inputs */}
      <input ref={imageInputRef} type="file" accept="image/*" capture="environment" style={{ display: 'none' }} onChange={handleImageSelect} />
      <input ref={fileInputRef}  type="file" accept=".pdf,.csv,.txt,.docx" style={{ display: 'none' }} onChange={handleFileSelect} />

      <div className="chat-input-container">
        <div className="agent-selector-container">
          <div className="agent-dropdown">
            <button className="agent-dropdown-button" onClick={() => setIsDropdownOpen(!isDropdownOpen)}>
              <Bot size={16} />
              <span>{getCurrentAgentName()}</span>
              <ChevronDown size={16} className={`dropdown-arrow ${isDropdownOpen ? 'open' : ''}`} />
            </button>
            {isDropdownOpen && (
              <div className="agent-dropdown-menu">
                {agentOptions.map((option, index) => {
                  const Icon = option.icon;
                  const isGroupSeparator = index === 1 || index === 9 || index === 13;
                  const isCurrentAgent = option.id === agent || (agent === 'super-agent' && option.id === 'orchestrator');
                  return (
                    <button key={option.id} className={`agent-dropdown-item ${isGroupSeparator ? 'group-separator' : ''} ${isCurrentAgent ? 'active' : ''}`} onClick={() => handleAgentChange(option)}>
                      <Icon size={16} />
                      <span>{option.name}</span>
                      {isCurrentAgent && <span className="current-indicator">✓</span>}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* ── Attachment Preview ─────────────────────────────────────────── */}
        {(attachedImage || attachedFile || audioBlob) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: '#1e293b', borderRadius: '8px', marginBottom: '6px', border: '1px solid #334155' }}>
            {attachedImage && <img src={attachedImage.preview} alt="preview" style={{ width: '40px', height: '40px', objectFit: 'cover', borderRadius: '6px' }} />}
            <span style={{ fontSize: '13px', color: '#cbd5e1', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {attachedImage ? attachedImage.file.name : attachedFile ? attachedFile.file.name : '🎤 Voice message ready'}
            </span>
            <button onClick={clearAttachments} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '2px' }}><X size={14} /></button>
          </div>
        )}

        {/* ── Input Row ─────────────────────────────────────────────────── */}
        <div className="chat-input-wrapper" style={{ alignItems: 'flex-end' }}>
          {/* Media buttons left of textarea */}
          <div style={{ display: 'flex', gap: '4px', padding: '6px 4px' }}>
            {/* Camera / Image upload */}
            <button
              title="Upload crop photo"
              onClick={() => imageInputRef.current?.click()}
              disabled={isLoading || isRecording}
              style={{ background: attachedImage ? '#166534' : 'none', border: '1px solid #334155', borderRadius: '8px', padding: '7px', cursor: 'pointer', color: attachedImage ? '#4ade80' : '#94a3b8', display: 'flex', alignItems: 'center' }}
            >
              <Camera size={17} />
            </button>
            {/* Microphone / Record */}
            <button
              title={isRecording ? 'Stop recording' : 'Record voice message'}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading}
              style={{ background: isRecording ? '#7f1d1d' : audioBlob ? '#1e3a5f' : 'none', border: `1px solid ${isRecording ? '#ef4444' : '#334155'}`, borderRadius: '8px', padding: '7px', cursor: 'pointer', color: isRecording ? '#ef4444' : audioBlob ? '#60a5fa' : '#94a3b8', display: 'flex', alignItems: 'center' }}
            >
              {isRecording ? <MicOff size={17} /> : <Mic size={17} />}
            </button>
            {/* File / Document upload */}
            <button
              title="Attach PDF, CSV, or TXT"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || isRecording}
              style={{ background: attachedFile ? '#1e3a5f' : 'none', border: '1px solid #334155', borderRadius: '8px', padding: '7px', cursor: 'pointer', color: attachedFile ? '#60a5fa' : '#94a3b8', display: 'flex', alignItems: 'center' }}
            >
              <Paperclip size={17} />
            </button>
          </div>

          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={attachedImage ? 'Describe the issue or add context...' : attachedFile ? 'What would you like to know about this document?' : audioBlob ? 'Add text context (optional)...' : 'Ask me anything about farming...'}
            rows="1"
            disabled={isLoading}
            style={{ flex: 1 }}
          />
          <button
            className={`send-button ${isLoading ? 'loading' : ''}`}
            onClick={sendMessage}
            disabled={isLoading || (!inputValue.trim() && !attachedImage && !attachedFile && !audioBlob)}
            aria-label="Send message"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22,2 15,22 11,13 2,9"></polygon>
            </svg>
          </button>
        </div>

        <div className="input-suggestions">
          <span className="suggestion-label">Try asking:</span>
          <button className="suggestion-chip" onClick={() => setSuggestionText("What crops should I plant this season?")}>Crop recommendations</button>
          <button className="suggestion-chip" onClick={() => setSuggestionText("How can I improve my soil health?")}>Soil health</button>
          <button className="suggestion-chip" onClick={() => setSuggestionText("What's the weather forecast for my area?")}>Weather forecast</button>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;