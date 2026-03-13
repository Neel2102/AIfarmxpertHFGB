import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, MicOff, Play, Square, Loader, Loader2, Volume2, AlertCircle, Check, User, Bot } from 'lucide-react';
import '../styles/Dashboard/VoiceRecorder.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function VoiceRecorder() {
  const [status, setStatus] = useState('idle');
  const [liveText, setLiveText] = useState('');
  const [conversations, setConversations] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');

  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef('');
  const silenceTimerRef = useRef(null);
  const audioRef = useRef(null);
  const conversationEndRef = useRef(null);
  const isRecordingRef = useRef(false);

  const [isSpeakingVolume, setIsSpeakingVolume] = useState(false);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const micStreamRef = useRef(null);
  const animationFrameRef = useRef(null);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversations]);

  // ── Reset to idle (guaranteed reset) ──
  const resetToIdle = useCallback(() => {
    isRecordingRef.current = false;
    setIsSpeakingVolume(false);
    
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(t => t.stop());
      micStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    setStatus('idle');
    setLiveText('');
  }, []);

  // ── Audio Volume Visualization Loop ──
  const updateVolumeLevel = useCallback(() => {
    if (!analyserRef.current || !isRecordingRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    // Calculate average volume
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    const average = sum / dataArray.length;
    
    // Threshold for speaking (0-255 scale)
    setIsSpeakingVolume(average > 15);
    
    animationFrameRef.current = requestAnimationFrame(updateVolumeLevel);
  }, []);

  // ── Send text to orchestrator ──
  const sendTextToOrchestrator = useCallback(async (text) => {
    if (!text.trim()) {
      resetToIdle();
      return;
    }

    setConversations(prev => [...prev, { role: 'user', text }]);
    setStatus('processing');
    setLiveText('');

    // Stop mic visualizations immediately
    setIsSpeakingVolume(false);
    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/voice/text-chat`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ text, language: 'en' }),
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const data = await response.json();

      const audioUrl = data.audio_url ? `${API_URL}${data.audio_url}` : null;
      setConversations(prev => [
        ...prev,
        { role: 'ai', text: data.response || 'No response received.', audioUrl, agentResponses: data.agent_responses },
      ]);

      if (audioUrl) {
        setStatus('playing');
        try {
          const audio = new Audio(audioUrl);
          audioRef.current = audio;
          audio.onended = () => resetToIdle();
          audio.onerror = () => resetToIdle();
          await audio.play();
        } catch (playErr) {
          console.warn('Audio autoplay blocked:', playErr);
          resetToIdle();
        }
      } else {
        resetToIdle();
      }
    } catch (err) {
      console.error('Voice text-chat error:', err);
      setConversations(prev => [
        ...prev,
        { role: 'ai', text: 'Sorry, I had trouble processing that. Please try again.' },
      ]);
      resetToIdle();
    }
  }, [resetToIdle]);

  // ── Start Recording with Web Speech API ──
  const startRecording = useCallback(async () => {
    setErrorMessage('');

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setStatus('error');
      setErrorMessage('Speech recognition is not supported. Please use Google Chrome.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;
      
      // Setup AudioContext for Volume Analysis
      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioContextCtor();
      audioContextRef.current = audioCtx;
      
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyserRef.current = analyser;
      
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);
      
    } catch (micErr) {
      setStatus('error');
      setErrorMessage('Microphone access denied. Please allow microphone permissions and try again.');
      return;
    }

    // Create and configure recognition
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    finalTranscriptRef.current = '';
    setLiveText('');
    isRecordingRef.current = true;

    recognition.onstart = () => {
      console.log('Speech recognition started');
      setStatus('recording');
      updateVolumeLevel(); // Start volume checking loop
    };

    recognition.onresult = (event) => {
      let interim = '';
      let newFinal = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          newFinal += t;
        } else {
          interim += t;
        }
      }

      if (newFinal) {
        finalTranscriptRef.current = (finalTranscriptRef.current + ' ' + newFinal).trim();
      }

      const combined = (finalTranscriptRef.current + ' ' + interim).trim();
      setLiveText(combined);

      // Auto-stop after 2.5s of silence
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = setTimeout(() => {
        console.log('Silence timeout — stopping recognition');
        try { recognition.stop(); } catch (e) { /* noop */ }
      }, 2500);
    };

    recognition.onend = () => {
      console.log('Speech recognition ended');
      isRecordingRef.current = false;
      setIsSpeakingVolume(false);
      
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      const finalText = finalTranscriptRef.current.trim();
      if (finalText) {
        sendTextToOrchestrator(finalText);
      } else {
        resetToIdle();
      }
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      isRecordingRef.current = false;
      setIsSpeakingVolume(false);

      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        setStatus('error');
        setErrorMessage('Microphone permission denied. Please allow and try again.');
      } else if (event.error === 'no-speech') {
        // No speech detected — just reset, don't show error
        resetToIdle();
      } else if (event.error === 'aborted') {
        // User or system aborted — handled in onend
      } else if (event.error === 'network') {
        setStatus('error');
        setErrorMessage('Network error. Speech recognition requires internet in Chrome.');
      } else {
        setStatus('error');
        setErrorMessage(`Speech error: ${event.error}`);
      }
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch (startErr) {
      console.error('Failed to start recognition:', startErr);
      setStatus('error');
      setErrorMessage('Could not start speech recognition. Please try again.');
    }
  }, [sendTextToOrchestrator, resetToIdle, updateVolumeLevel]);

  // ── Stop Recording ──
  const stopRecording = useCallback(() => {
    if (recognitionRef.current && isRecordingRef.current) {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      try { recognitionRef.current.stop(); } catch (e) { /* noop */ }
    }
  }, []);

  // ── Handle button click ──
  const handleButtonClick = () => {
    if (status === 'recording') {
      stopRecording();
    } else if (status === 'playing') {
      // Stop audio and reset
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        audioRef.current = null;
      }
      resetToIdle();
    } else if (status === 'idle' || status === 'error') {
      startRecording();
    }
    // 'processing' — do nothing, let it finish
  };

  // ── Cleanup on unmount ──
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) { /* noop */ }
      }
      if (audioRef.current) {
        audioRef.current.pause();
      }
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (micStreamRef.current) {
        micStreamRef.current.getTracks().forEach(t => t.stop());
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, []);

  const getStatusText = () => {
    switch (status) {
      case 'idle': return 'Tap to speak';
      case 'recording': return 'Listening...';
      case 'processing': return 'Thinking...';
      case 'playing': return 'Speaking... (tap to stop)';
      case 'error': return 'Tap to retry';
      default: return 'Ready';
    }
  };

  const getMicIcon = () => {
    switch (status) {
      case 'recording':
        return <Square className="voice-recorder-mic-icon" />;
      case 'processing':
        return <Loader className="voice-recorder-mic-icon voice-recorder-spin" />;
      case 'playing':
        return <Volume2 className="voice-recorder-mic-icon" />;
      case 'error':
        return <AlertCircle className="voice-recorder-mic-icon" />;
      default:
        return <Mic className="voice-recorder-mic-icon" />;
    }
  };

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

  return (
    <div className="voice-recorder-page">
      {/* ── Conversation Area ── */}
      <div className="voice-recorder-conversation-container">
        {conversations.length === 0 ? (
          <div className="voice-recorder-empty-state">
        <img 
          src="/voice-agent-graphic.png" 
          alt="AI Farming Assistant" 
          className="voice-recorder-empty-icon" 
          style={{ opacity: 0.8, width: '280px', height: 'auto', marginBottom: '1rem' }}
        />
        <h2 className="voice-recorder-empty-title">AI Farming Assistant</h2>
        <p className="voice-recorder-empty-subtitle">
          I'm ready to listen. Ask me about crop suggestions, soil health, or weather updates.
        </p>
      </div>
        ) : (
          conversations.map((msg, idx) => (
            <div key={idx} className={`voice-recorder-msg ${msg.role}`}>
              <div className="voice-recorder-msg-label">
                {msg.role === 'user' ? (
                  <><User size={14} className="mr-1" /> You</>
                ) : (
                  <><Bot size={14} className="mr-1" /> FarmXpert AI</>
                )}
              </div>
              {msg.text}

              {msg.agentResponses && msg.agentResponses.length > 0 && (
                <div className="voice-recorder-agents-block">
                  <div className="voice-recorder-agents-header">
                    <Check size={14} color="#10b981" /> Sources Consulted
                  </div>
                  <div className="voice-recorder-agents-chips">
                    {msg.agentResponses.map((a, i) => (
                      <span key={i} className={`voice-recorder-agent-chip ${a.success ? 'success' : 'error'}`}>
                        {getAgentDisplayName(a.agent_name)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {msg.audioUrl && (
                <div className="voice-recorder-audio-player">
                  <audio controls preload="none" src={msg.audioUrl}>
                    Your browser does not support audio.
                  </audio>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={conversationEndRef} />
      </div>

      {/* ── Bottom Controls ── */}
      <div className="voice-recorder-controls-wrapper">
        
        {/* Error Alert */}
        {status === 'error' && errorMessage && (
          <div className="voice-recorder-error">
            <AlertCircle size={16} />
            {errorMessage}
          </div>
        )}

        {/* Live Transcription Box */}
        {(status === 'recording' || (status === 'processing' && liveText)) && (
          <div className="voice-recorder-live-box">
            <div className="voice-recorder-live-label">
              <Mic size={14} />
              <span>{status === 'recording' ? 'You are saying...' : 'You said:'}</span>
            </div>
            <div className="voice-recorder-live-text">
              {liveText || <span className="voice-recorder-live-placeholder">Listening for your voice...</span>}
              {status === 'recording' && <span className="voice-recorder-cursor">|</span>}
            </div>
          </div>
        )}

        <div className="voice-recorder-statusbar">
          <div className="voice-recorder-pill">
            <span className={`voice-recorder-dot ${status}`} />
            <span>{status === 'idle' ? 'Ready' : status.charAt(0).toUpperCase() + status.slice(1)}</span>
          </div>
        </div>

        <button
          type="button"
          className={`voice-recorder-mic-btn ${status} ${status === 'processing' ? 'disabled' : ''} ${isSpeakingVolume ? 'active-speaking' : ''}`}
          onClick={handleButtonClick}
          disabled={status === 'processing'}
          aria-label={status === 'recording' ? 'Stop recording' : 'Start recording'}
        >
          {getMicIcon()}
        </button>
      </div>
    </div>
  );
}
