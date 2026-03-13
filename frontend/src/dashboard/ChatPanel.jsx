import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Bot, BarChart3, Droplets, ThermometerSun, FlaskConical, Sprout, 
  Calendar, Circle, Bug, Cloud, TrendingUp, Clock, Truck, 
  MapPin, Camera, Mic, MicOff, Paperclip, X, Check, Menu, Plus
} from 'lucide-react';
import { useOrchestrator } from '../contexts/OrchestratorContext';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Dashboard/ChatPanel.css';
import '../styles/Dashboard/ChatPanel-reasoning.css';

const API_BASE_URL = '/api';

const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const ChatPanel = ({ agent, farmData, sessionId: propSessionId }) => {
  const navigate = useNavigate();
  const { 
    messages: contextMessages, 
    loadSessionMessages, 
    resetSession,
    session,
    loading: contextLoading,
    setMessages
  } = useOrchestrator();
  const { user } = useAuth();

  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Use the effective session ID from either props or context
  const sessionId = propSessionId || session?.id;

  // ── Multi-Agent State ──
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [showAgentDrawer, setShowAgentDrawer] = useState(false);

  // ── Media State ──
  const [attachedImage, setAttachedImage] = useState(null);
  const [attachedFile, setAttachedFile] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const imageInputRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // ── Media State ──


  useEffect(() => {
    // Re-sync chat history when switching agents or sessions
    if (sessionId && loadSessionMessages) {
      loadSessionMessages(sessionId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, agent, session?.id]);


  const handleNewChat = () => {
    if (resetSession) resetSession();
    // Clear local states if any
    setAttachedImage(null);
    setAttachedFile(null);
    setAudioBlob(null);
    setInputValue('');
  };

  // Process messages for display
  const messages = contextMessages.length > 0 
    ? contextMessages.map((m) => ({
        ...m,
        content: typeof m?.content === 'string'
          ? m.content.replace(/<[^>]*>/g, '').replace(/\b\w+">/g, '').replace(/\bclass="[^"]*"/g, '')
          : m?.content,
      }))
    : [];

  // Debug: log messages to see if they are loaded
  console.log('[ChatPanel] contextMessages length:', contextMessages.length, contextMessages);
  console.log('[ChatPanel] processed messages length:', messages.length, messages);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputValue]);

  const getAgentDisplayName = (name) => {
    const map = {
      'super-agent': 'SuperAgent',
      'crop_selector': 'Crop Selector',
      'seed_selection': 'Seed Selection',
      'soil_health_agent': 'Soil Health',
      'fertilizer_agent': 'Fertilizer Advisor',
      'irrigation_agent': 'Irrigation Planner',
      'pest_disease_diagnostic': 'Pest Diagnostic',
      'weather_watcher': 'Weather Watcher',
      'growth_stage_monitor': 'Growth Monitor',
      'task_scheduler_agent': 'Task Scheduler',
      'machinery_manager': 'Machinery Manager',
      'layout_mapper': 'Layout Mapper',
      'yield_predictor': 'Yield Predictor',
      'market_intelligence_agent': 'Market Intel'
    };
    return map[name] || name;
  };

  const agentOptions = [
    { id: 'crop_selector', name: 'Crop Selector', icon: Sprout },
    { id: 'seed_selection', name: 'Seed Selection', icon: Circle },
    { id: 'soil_health_agent', name: 'Soil Health', icon: FlaskConical },
    { id: 'fertilizer_agent', name: 'Fertilizer Advisor', icon: Droplets },
    { id: 'irrigation_agent', name: 'Irrigation Planner', icon: ThermometerSun },
    { id: 'pest_disease_diagnostic', name: 'Pest Diagnostic', icon: Bug },
    { id: 'weather_watcher', name: 'Weather Watcher', icon: Cloud },
    { id: 'growth_stage_monitor', name: 'Growth Monitor', icon: TrendingUp },
    { id: 'task_scheduler_agent', name: 'Task Scheduler', icon: Clock },
    { id: 'machinery_manager', name: 'Machinery', icon: Truck },
    { id: 'layout_mapper', name: 'Farm Layout', icon: MapPin },
    { id: 'yield_predictor', name: 'Yield Predictor', icon: BarChart3 },
    { id: 'market_intelligence_agent', name: 'Market Intel', icon: Calendar },
  ];

  const toggleAgent = (agentId) => {
    setSelectedAgents(prev => {
      if (prev.includes(agentId)) return prev.filter(id => id !== agentId);
      return [...prev, agentId];
    });
  };

  const cleanText = (text) => {
    if (!text) return '';
    return text.replace(/<[^>]*>/g, '')
               .replace(/\bclass="[^"]*"/g, '')
               .trim();
  };

  const renderMarkdownText = (text) => {
    if (!text) return null;
    let result = String(text);
    const codeBlocks = [];

    result = result.replace(/```([\s\S]*?)```/g, (_m, code) => {
      const idx = codeBlocks.length;
      codeBlocks.push(String(code || '').trimEnd());
      return `__CODEBLOCK_${idx}__`;
    });

    const renderInline = (s) => {
      const parts = [];
      const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
      let lastIndex = 0;
      let match;
      while ((match = pattern.exec(s)) !== null) {
        if (match.index > lastIndex) parts.push(s.slice(lastIndex, match.index));
        const token = match[0];
        if (token.startsWith('`') && token.endsWith('`')) {
          parts.push(<code key={match.index} className="inline">{token.slice(1, -1)}</code>);
        } else if (token.startsWith('**') && token.endsWith('**')) {
          parts.push(<strong key={match.index}>{token.slice(2, -2)}</strong>);
        } else if (token.startsWith('*') && token.endsWith('*')) {
          parts.push(<em key={match.index}>{token.slice(1, -1)}</em>);
        } else {
          parts.push(token);
        }
        lastIndex = match.index + token.length;
      }
      if (lastIndex < s.length) parts.push(s.slice(lastIndex));
      return parts.length ? parts : s;
    };

    const lines = result.split('\n');
    return (
      <div className="farm-markdown">
        {lines.map((line, lineIndex) => {
          const codeMatch = line.match(/__CODEBLOCK_(\d+)__/);
          if (codeMatch) {
            const code = codeBlocks[Number(codeMatch[1])] || '';
            return <pre key={lineIndex} className="code-block"><code>{code}</code></pre>;
          }
          if (line.trim() === '') return <br key={lineIndex} />;
          if (line.trim().startsWith('#### ')) return <h4 key={lineIndex}>{renderInline(line.trim().slice(5))}</h4>;
          if (line.trim().startsWith('### ')) return <h3 key={lineIndex}>{renderInline(line.trim().slice(4))}</h3>;
          if (line.trim().startsWith('## ')) return <h2 key={lineIndex}>{renderInline(line.trim().slice(3))}</h2>;
          if (line.trim().startsWith('# ')) return <h1 key={lineIndex}>{renderInline(line.trim().slice(2))}</h1>;
          if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
            return <li key={lineIndex}>{renderInline(line.trim().slice(2))}</li>;
          }
          return <p key={lineIndex}>{renderInline(line)}</p>;
        })}
      </div>
    );
  };

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setAttachedImage({ file, preview: ev.target.result });
    reader.readAsDataURL(file);
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
    if (imageInputRef.current) imageInputRef.current.value = '';
    if (fileInputRef.current) fileInputRef.current.value = '';
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

  const sendMessage = async () => {
    const text = inputValue.trim();
    const hasAudio = !!audioBlob;
    const hasImage = !!attachedImage;
    const hasFile = !!attachedFile;

    if (!text && !hasAudio && !hasImage && !hasFile) return;
    if (isLoading) return;

    let userContent = text;
    if (hasImage) userContent = `[📷 Image: ${attachedImage.file.name}] ${text}`;
    if (hasFile) userContent = `[📎 ${attachedFile.file.name}] ${text}`;
    if (hasAudio) userContent = `[🎤 Voice message] ${text}`;

    const userMessage = { id: Date.now(), type: 'user', content: userContent, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    const assistantMessageId = Date.now() + 1;
    setMessages((prev) => [...prev, { id: assistantMessageId, type: 'assistant', content: '', timestamp: '', isStreaming: true }]);

    try {
      let data = null;

      // Voice processing
      if (hasAudio) {
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');
        formData.append('language', 'en');

        const response = await fetch(`${API_BASE_URL}/chat/voice`, { method: 'POST', body: formData, headers: getAuthHeaders() });
        if (!response.ok) throw new Error(`Voice error: ${response.status}`);

        const audioArrayBuffer = await response.arrayBuffer();
        const audioUrl = URL.createObjectURL(new Blob([audioArrayBuffer], { type: 'audio/mpeg' }));
        const transcript = decodeURIComponent(response.headers.get('X-Transcript') || '');
        const textAnswer = decodeURIComponent(response.headers.get('X-Text-Response') || '');

        setMessages((prev) => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: textAnswer || 'Voice response received.', audioUrl, transcript, isStreaming: false }
            : msg
        ));
        clearAttachments();
        return;
      }

      // Image processing
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

      // Document processing
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

      // Standard Text Orchestrator
      const response = await fetch(`${API_BASE_URL}/chat/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ 
          message: text, 
          session_id: sessionId,
          user_id: user?.id,
          context: { selected_agents: selectedAgents }
        }),
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
      let errorMessage = e.message || 'Could not connect to AI. Ensure backend is running.';
      if (e.message?.includes('429')) errorMessage = "Experiencing heavy traffic (API rate limit). Please wait a moment and try your query again. 🌱";
      if (e.message?.includes('500') || e.message?.includes('503')) errorMessage = "The farm orchestrator is currently unavailable. We're working on getting it back online! 🚜";

      setMessages((prev) => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: errorMessage, isStreaming: false }
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

  const renderVisionCard = (visionResult) => {
    if (!visionResult) return null;
    const confidence = Math.round((parseFloat(visionResult.confidence) || 0) * 100);
    const severityColor = { none: '#10b981', mild: '#eab308', moderate: '#f97316', severe: '#ef4444', unknown: '#94a3b8' }[visionResult.severity || 'unknown'] || '#94a3b8';
    return (
      <div className="farm-vision-card">
        <div className="farm-vision-title"><Bug size={16} /> Pest & Disease Diagnosis</div>
        <div className="farm-vision-grid">
          <div>
            <div className="farm-vision-label">Diagnosis</div>
            <div className="farm-vision-value">{visionResult.diagnosis || 'Unknown'}</div>
          </div>
          <div className="farm-vision-inline">
            <div>
              <div className="farm-vision-label">Confidence: {confidence}%</div>
              <div className="farm-vision-bar-bg"><div className="farm-vision-bar-fill" style={{ width: `${confidence}%` }}></div></div>
            </div>
            <div>
              <div className="farm-vision-label">Severity</div>
              <div className="farm-vision-severity" style={{ color: severityColor }}>{visionResult.severity || 'unknown'}</div>
            </div>
          </div>
          {visionResult.description && <div><div className="farm-vision-label">Observation</div><div className="farm-vision-value">{visionResult.description}</div></div>}
          {visionResult.recommended_treatment?.length > 0 && (
            <div>
              <div className="farm-vision-label">Recommended Treatment</div>
              <ul className="farm-vision-list">
                {visionResult.recommended_treatment.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="farm-chat-layout">

      {/* ── Main Chat Area ── */}
      <main className="farm-chat-main">
        <header className="farm-chat-header">
          <h2><span>🚜</span> Farm Orchestrator</h2>
        </header>

        <div className="farm-messages-container">
          {messages.length <= 1 && (messages.length === 0 || messages[0].type === 'system') && (
            <div className="farm-welcome-overlay">
              <div className="farm-welcome-content">
                <div className="farm-welcome-orb" />
                <div className="farm-welcome-orb secondary" />
                <div className="farm-welcome-inner">
                  <div className="farm-welcome-icon-wrapper">
                    <div className="farm-welcome-icon-bg" />
                    <Bot size={48} className="farm-welcome-bot" />
                  </div>
                  <h1 className="farm-welcome-title">Welcome to FarmXpert AI</h1>
                  <p className="farm-welcome-subtitle">
                    Your personal agricultural intelligence coordinator. I'm connected to your 
                    <strong> {farmData.farm_name}</strong> and ready to assist with real-time insights.
                  </p>
                  
                  <div className="farm-welcome-features">
                    <div className="farm-feature-item">
                      <div className="feature-icon-box weather"><Cloud size={18} /></div>
                      <span>Weather Analysis</span>
                    </div>
                    <div className="farm-feature-item">
                      <div className="feature-icon-box soil"><FlaskConical size={18} /></div>
                      <span>Soil Health</span>
                    </div>
                    <div className="farm-feature-item">
                      <div className="feature-icon-box growth"><TrendingUp size={18} /></div>
                      <span>Growth Monitor</span>
                    </div>
                    <div className="farm-feature-item">
                      <div className="feature-icon-box market"><Calendar size={18} /></div>
                      <span>Market Intel</span>
                    </div>
                  </div>

                  <div className="farm-welcome-prompt">
                    Type a question below or pick a specialist to get started.
                  </div>
                </div>
              </div>
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className={`farm-message-row ${m.type}`}>
              <div className="farm-message-inner">
                {m.type !== 'system' && (
                  <div className={`farm-avatar ${m.type === 'user' ? 'user-bg' : 'assistant-bg'}`}>
                    {m.type === 'user' ? 'U' : <Bot size={18} />}
                  </div>
                )}
                
                <div className="farm-message-content">
                  {m.type !== 'system' && <span className="farm-message-author">{m.type === 'user' ? 'You' : 'Farm Orchestrator'}</span>}
                  
                  {m.type === 'assistant' ? (
                    <>
                      {renderMarkdownText(cleanText(m.content))}
                      
                      {m.isStreaming && <div className="farm-typing"><span></span><span></span><span></span></div>}
                      
                      {m.visionResult && !m.isStreaming && renderVisionCard(m.visionResult)}
                      
                      {m.audioUrl && !m.isStreaming && (
                        <div className="farm-audio-block">
                          <audio controls autoPlay src={m.audioUrl} className="farm-audio-player" />
                          {m.transcript && <div className="farm-audio-transcript">🎤 Heard: "{m.transcript}"</div>}
                        </div>
                      )}

                      {!m.isStreaming && m.agent_responses && m.agent_responses.length > 0 && (
                        <div className="farm-context-block">
                          <div className="farm-context-header"><Check size={14} color="#10b981" /> Sources Consulted</div>
                          <div className="farm-context-chips">
                            {m.agent_responses.map((a, i) => (
                              <span key={i} className={`farm-context-chip ${a.success ? 'success' : 'error'}`}>{getAgentDisplayName(a.agent_name)}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  ) : m.type === 'system' ? (
                     <div className="farm-system-text">{m.content}</div>
                  ) : (
                    m.content
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* ── Input Area ── */}
        <div className="farm-input-area">
          <div className="farm-input-container">
            
            {/* Agent Drawer Controls */}
            <div className="farm-agent-selector">
              <button className={`farm-agent-toggle ${selectedAgents.length > 0 ? 'active' : ''}`} onClick={() => setShowAgentDrawer(!showAgentDrawer)}>
                {selectedAgents.length === 0 ? '✨ Auto-Route (SuperAgent) ▼' : `👥 ${selectedAgents.length} Agent(s) Selected ▼`}
              </button>
            </div>
            
            {showAgentDrawer && (
              <div className="farm-agent-drawer">
                <div className="farm-agent-drawer-header"><span>Pick specific agents to handle your query exclusively:</span></div>
                <div className="farm-agent-pill-list">
                  {agentOptions.map(opt => (
                    <button key={opt.id} className={`farm-agent-pill ${selectedAgents.includes(opt.id) ? 'selected' : ''}`} onClick={() => toggleAgent(opt.id)}>
                      <opt.icon size={13} /> {opt.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="farm-input-box">
              {/* Attachments Preview */}
              {(attachedImage || attachedFile || audioBlob) && (
                <div className="farm-input-attachments">
                  {attachedImage && (
                    <div className="farm-attachment-pill">
                      <img src={attachedImage.preview} alt="preview" />
                      <span>{attachedImage.file.name}</span>
                      <button className="farm-attachment-close" onClick={clearAttachments}><X size={14} /></button>
                    </div>
                  )}
                  {attachedFile && (
                    <div className="farm-attachment-pill">
                      <Paperclip size={14} /> <span>{attachedFile.file.name}</span>
                      <button className="farm-attachment-close" onClick={clearAttachments}><X size={14} /></button>
                    </div>
                  )}
                  {audioBlob && (
                    <div className="farm-attachment-pill">
                      <Mic size={14} color="#3b82f6" /> <span>Voice recording prepared</span>
                      <button className="farm-attachment-close" onClick={clearAttachments}><X size={14} /></button>
                    </div>
                  )}
                </div>
              )}

              <div className="farm-input-row">
                <button className="farm-tool-btn" onClick={() => imageInputRef.current?.click()} disabled={isLoading || isRecording}><Camera size={18} /></button>
                <button className={`farm-tool-btn ${isRecording ? 'recording' : audioBlob ? 'has-audio' : ''}`} onClick={isRecording ? stopRecording : startRecording} disabled={isLoading}>
                  {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
                </button>
                <button className="farm-tool-btn" onClick={() => fileInputRef.current?.click()} disabled={isLoading || isRecording}><Paperclip size={18} /></button>
                
                <textarea
                  ref={textareaRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Message Farm Orchestrator..."
                  disabled={isLoading}
                  className="farm-textarea"
                  rows={1}
                />

                <button className={`farm-send-btn ${isLoading ? 'loading' : ''} ${inputValue.trim() || attachedImage || attachedFile || audioBlob ? 'active' : ''}`} onClick={sendMessage} disabled={isLoading || (!inputValue.trim() && !attachedImage && !attachedFile && !audioBlob)}>
                  {isLoading ? <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg> : <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>}
                </button>
              </div>
            </div>
            
            <div className="farm-input-footer">
               Farm Orchestrator may make mistakes. Always verify critical decisions with an agronomist. 
            </div>
          </div>
        </div>

        {/* Hidden File Inputs */}
        <input ref={imageInputRef} type="file" accept="image/*" capture="environment" style={{ display: 'none' }} onChange={handleImageSelect} />
        <input ref={fileInputRef} type="file" accept=".pdf,.csv,.txt,.docx" style={{ display: 'none' }} onChange={handleFileSelect} />
      </main>
    </div>
  );
};

export default ChatPanel;