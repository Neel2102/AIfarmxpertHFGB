import React, { useEffect, useRef, useState } from 'react';
import { GoogleGenAI, Modality, Type } from "@google/genai";
import { Mic, MicOff, Activity, Volume2, WifiOff } from 'lucide-react';
import { api } from '../services/api';
import "../styles/Dashboard/HandsFreeVoice.css";

function createBlob(data) {
  const l = data.length;
  const int16 = new Int16Array(l);
  for (let i = 0; i < l; i++) {
    const s = Math.max(-1, Math.min(1, data[i]));
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }

  const buffer = new Uint8Array(int16.buffer);
  let binary = '';
  const len = buffer.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(buffer[i]);
  }
  return {
    data: btoa(binary),
    mimeType: 'audio/pcm;rate=16000',
  };
}

function decodeBase64(base64) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

const API_KEY = process.env.REACT_APP_API_KEY || process.env.API_KEY;

export async function sendMessageToOrchestrator(message, history, targetAgentId = null, image = null) {
  if (!navigator.onLine) {
    return {
      agentId: targetAgentId || 'orchestrator',
      agentName: 'Offline Manager',
      response: 'You are currently offline. Your request has been queued and will be processed automatically when connection is restored.',
      suggestedActions: [],
      isQueued: true
    };
  }

  const startTime = Date.now();

  try {
    const ai = new GoogleGenAI({ apiKey: API_KEY });
    const model = 'gemini-3-pro-preview';

    const user = await api.auth.getSession();
    const devices = await api.hardware.getDevices();
    const fields = await api.fields.getFields();

    const liveContext = `
    --- REAL-TIME FARM CONTEXT ---
    USER: ${user ? `${user.name} (${user.role})` : 'Guest'}
    FARM: ${user ? user.farmName : 'Unknown Farm'}

    MAPPED FIELDS:
    ${fields.length > 0 ? fields.map(f => `- Field Name: "${f.name}", Crop: "${f.crop}", Area: ${f.area}ha, Center Lat/Lng: ${JSON.stringify((f.coordinates && f.coordinates[0]) || {})}`).join('\n') : 'No fields mapped yet.'}

    LIVE TELEMETRY (Sensors/Drones/Machinery):
    ${devices.map(d => `- [${String(d.type || '').toUpperCase()}] ${d.name}: ${JSON.stringify(d.readings || {})}`).join('\n')}
    ------------------------------
    `;

    const RESPONSE_SCHEMA = {
      type: Type.OBJECT,
      properties: {
        agentId: { type: Type.STRING },
        agentName: { type: Type.STRING },
        response: { type: Type.STRING },
        suggestedActions: { type: Type.ARRAY, items: { type: Type.STRING } }
      },
      required: ['agentId', 'agentName', 'response']
    };

    const systemInstruction = `${liveContext}`;

    const recentHistory = (history || []).slice(-10).map(msg => {
      const parts = [{ text: msg.text }];
      if (msg.attachment?.type === 'image') {
        const base64Data = msg.attachment.content.replace(/^data:image\/[a-z]+;base64,/, "");
        parts.push({
          inlineData: {
            data: base64Data,
            mimeType: msg.attachment.mimeType
          }
        });
      }
      return {
        role: msg.role === 'user' ? 'user' : 'model',
        parts
      };
    });

    const chat = ai.chats.create({
      model,
      history: recentHistory,
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        responseSchema: RESPONSE_SCHEMA,
      },
    });

    const currentMessageParts = [{ text: message || " " }];
    if (image) {
      const base64Data = image.data.replace(/^data:image\/[a-z]+;base64,/, "");
      currentMessageParts.push({ inlineData: { data: base64Data, mimeType: image.mimeType } });
    }

    const result = await chat.sendMessage({ message: currentMessageParts });
    const text = result.text;
    if (!text) throw new Error("No response from Gemini");

    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch (e) {
      const cleaned = String(text).replace(/```json/g, '').replace(/```/g, '').trim();
      try {
        parsed = JSON.parse(cleaned);
      } catch (e2) {
        parsed = {
          agentId: targetAgentId || 'orchestrator',
          agentName: 'System',
          response: text,
          suggestedActions: []
        };
      }
    }

    const latency = Date.now() - startTime;
    await api.logs.addLog({
      timestamp: Date.now(),
      userQuery: message + (image ? " [Image Uploaded]" : ""),
      selectedAgentId: parsed.agentId,
      agentName: parsed.agentName,
      response: parsed.response,
      latencyMs: latency,
      status: 'success'
    });

    return parsed;
  } catch (error) {
    const latency = Date.now() - startTime;
    await api.logs.addLog({
      timestamp: Date.now(),
      userQuery: message + (image ? " [Image Uploaded]" : ""),
      selectedAgentId: targetAgentId || 'orchestrator',
      agentName: 'System Error',
      response: error?.message || String(error),
      latencyMs: latency,
      status: 'error'
    });

    return {
      agentId: targetAgentId || 'orchestrator',
      agentName: targetAgentId ? 'Agent' : 'FarmXpert Orchestrator',
      response: "I'm having trouble connecting to the agent network right now. Please check your connection and try again.",
      suggestedActions: ["Retry"]
    };
  }
}

export default function HandsFreeVoice() {
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [status, setStatus] = useState('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const inputContextRef = useRef(null);
  const outputContextRef = useRef(null);
  const streamRef = useRef(null);
  const processorRef = useRef(null);
  const workletNodeRef = useRef(null);
  const mediaSourceRef = useRef(null);
  const zeroGainRef = useRef(null);
  const sessionRef = useRef(null);
  const nextStartTimeRef = useRef(0);
  const audioSourcesRef = useRef(new Set());
  const canvasRef = useRef(null);

  const getFarmStatusTool = {
    name: 'getFarmStatus',
    description: 'Get real-time telemetry and status of farm devices.',
    parameters: {
      type: Type.OBJECT,
      properties: {},
    }
  };

  const stopAllAudio = () => {
    audioSourcesRef.current.forEach(s => s.stop());
    audioSourcesRef.current.clear();
    if (outputContextRef.current) {
      nextStartTimeRef.current = outputContextRef.current.currentTime;
    }
  };

  const cleanup = async () => {
    setStatus('idle');
    setIsConnected(false);

    // 1. Capture current refs and IMMEDIATELY nullify them to prevent any other logic from grabbing them
    const inCtx = inputContextRef.current;
    const outCtx = outputContextRef.current;
    const stream = streamRef.current;

    inputContextRef.current = null;
    outputContextRef.current = null;
    streamRef.current = null;

    // 2. Stop playback
    stopAllAudio();

    // 3. Stop media stream tracks
    if (stream) {
      try {
        stream.getTracks().forEach(t => t.stop());
      } catch (e) { }
    }

    // 4. Safely close contexts
    const closeContext = async (ctx, name) => {
      if (!ctx || ctx.state === 'closed') return;
      if (ctx._closing) return; // Custom guard for race conditions
      ctx._closing = true;
      try {
        await ctx.close();
      } catch (e) {
        if (e.name !== 'InvalidStateError') {
          console.warn(`Error closing ${name} context:`, e);
        }
      }
    };

    await Promise.all([
      closeContext(inCtx, 'input'),
      closeContext(outCtx, 'output')
    ]);

    // 6. Cleanup transient nodes
    if (mediaSourceRef.current) {
      try { mediaSourceRef.current.disconnect(); } catch (e) { }
      mediaSourceRef.current = null;
    }
    if (workletNodeRef.current) {
      try {
        workletNodeRef.current.port.onmessage = null;
        workletNodeRef.current.disconnect();
      } catch (e) { }
      workletNodeRef.current = null;
    }
    if (zeroGainRef.current) {
      try { zeroGainRef.current.disconnect(); } catch (e) { }
      zeroGainRef.current = null;
    }
    if (processorRef.current) {
      try { processorRef.current.disconnect(); } catch (e) { }
      processorRef.current = null;
    }
  };

  const playAudioChunk = async (base64Data) => {
    if (!outputContextRef.current) return;

    try {
      const rawBytes = decodeBase64(base64Data);
      const dataInt16 = new Int16Array(rawBytes.buffer);
      const float32 = new Float32Array(dataInt16.length);
      for (let i = 0; i < dataInt16.length; i++) {
        float32[i] = dataInt16[i] / 32768.0;
      }

      const buffer = outputContextRef.current.createBuffer(1, float32.length, 24000);
      buffer.copyToChannel(float32, 0);

      const source = outputContextRef.current.createBufferSource();
      source.buffer = buffer;
      source.connect(outputContextRef.current.destination);

      const now = outputContextRef.current.currentTime;
      const start = Math.max(now, nextStartTimeRef.current);
      source.start(start);
      nextStartTimeRef.current = start + buffer.duration;

      audioSourcesRef.current.add(source);
      source.onended = () => {
        audioSourcesRef.current.delete(source);
        if (audioSourcesRef.current.size === 0) {
          setStatus('listening');
        }
      };
    } catch (e) {
      // no-op
    }
  };

  const startSession = async () => {
    try {
      // Clear any existing session artifacts before starting a new one
      await cleanup();

      setStatus('connecting');
      setErrorMessage('');

      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      const inCtx = new AudioContextCtor({ sampleRate: 16000 });
      const outCtx = new AudioContextCtor({ sampleRate: 24000 });

      inputContextRef.current = inCtx;
      outputContextRef.current = outCtx;
      nextStartTimeRef.current = outCtx.currentTime;

      const ai = new GoogleGenAI({ apiKey: API_KEY });

      const sessionPromise = ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
        config: {
          responseModalities: [Modality.AUDIO],
          tools: [{ functionDeclarations: [getFarmStatusTool] }],
          systemInstruction: `You are FarmXpert Voice.
                    You are speaking to a farmer who is likely driving a tractor or has dirty hands.
                    Keep responses SHORT, CONCISE, and ACTION-ORIENTED.
                    Do not read out long lists. Summarize key points.
                    If there is an emergency (red status), state it first.`
        },
        callbacks: {
          onopen: async () => {
            // Check if this context is still the active one
            if (inputContextRef.current !== inCtx) return;

            setIsConnected(true);
            setStatus('listening');

            try {
              const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
              if (inputContextRef.current !== inCtx) {
                stream.getTracks().forEach(t => t.stop());
                return;
              }
              streamRef.current = stream;

              if (inCtx.state === 'suspended') {
                await inCtx.resume();
              }

              const processorName = `farmxpert-pcm-processor-${Math.random().toString(36).substr(2, 9)}`;
              const workletModuleCode = `
class FarmxpertPcmProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buffer = [];
    this._chunkSize = 4096;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    const ch0 = input[0];
    for (let i = 0; i < ch0.length; i++) {
      this._buffer.push(ch0[i]);
      if (this._buffer.length >= this._chunkSize) {
        const chunk = this._buffer.slice(0, this._chunkSize);
        this._buffer = this._buffer.slice(this._chunkSize);
        this.port.postMessage(chunk);
      }
    }
    return true;
  }
}

registerProcessor('${processorName}', FarmxpertPcmProcessor);
              `;

              const blob = new Blob([workletModuleCode], { type: 'application/javascript' });
              const moduleUrl = URL.createObjectURL(blob);
              await inCtx.audioWorklet.addModule(moduleUrl);
              URL.revokeObjectURL(moduleUrl);

              const source = inCtx.createMediaStreamSource(stream);
              mediaSourceRef.current = source;

              const workletNode = new AudioWorkletNode(inCtx, processorName, {
                numberOfInputs: 1,
                numberOfOutputs: 1,
                channelCount: 1,
                channelCountMode: 'explicit',
                channelInterpretation: 'speakers'
              });
              workletNodeRef.current = workletNode;

              const zeroGain = inCtx.createGain();
              zeroGain.gain.value = 0;
              zeroGainRef.current = zeroGain;

              workletNode.port.onmessage = (event) => {
                if (isMuted) return;
                const chunk = event.data;
                if (!chunk || chunk.length === 0) return;
                const float32 = new Float32Array(chunk);
                const pcmBlob = createBlob(float32);
                sessionPromise.then(session => {
                  session.sendRealtimeInput({ media: pcmBlob });
                });
              };

              source.connect(workletNode);
              workletNode.connect(zeroGain);
              zeroGain.connect(inCtx.destination);
            } catch (err) {
              if (inputContextRef.current === inCtx) {
                setStatus('error');
                setErrorMessage('Microphone access denied.');
              }
            }
          },
          onmessage: async (msg) => {
            if (inputContextRef.current !== inCtx) return;

            if (msg.toolCall) {
              setStatus('speaking');
              for (const fc of msg.toolCall.functionCalls) {
                if (fc.name === 'getFarmStatus') {
                  const devices = await api.hardware.getDevices();
                  const summary = devices.map(d => `${d.name}: ${d.status}, Battery ${d.batteryLevel}%`).join('. ');
                  sessionPromise.then(session => {
                    session.sendToolResponse({
                      functionResponses: {
                        id: fc.id,
                        name: fc.name,
                        response: { result: { text: summary } }
                      }
                    });
                  });
                }
              }
            }

            const audioData = msg.serverContent?.modelTurn?.parts?.[0]?.inlineData?.data;
            if (audioData) {
              setStatus('speaking');
              playAudioChunk(audioData);
            }

            if (msg.serverContent?.interrupted) {
              stopAllAudio();
              setStatus('listening');
            }

            if (msg.serverContent?.turnComplete) {
              setStatus('listening');
            }
          },
          onclose: () => {
            if (inputContextRef.current === inCtx) {
              cleanup();
            }
          },
          onerror: () => {
            if (inputContextRef.current === inCtx) {
              setStatus('error');
              setErrorMessage('Connection lost.');
              cleanup();
            }
          }
        }
      });

      sessionRef.current = sessionPromise;
    } catch (e) {
      setStatus('error');
      setErrorMessage('Failed to initialize voice session.');
    }
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  useEffect(() => {
    return () => { cleanup(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex flex-col h-full bg-slate-900 text-white relative overflow-hidden">
      <div className={`absolute inset-0 flex items-center justify-center transition-opacity duration-500 ${status === 'speaking' ? 'opacity-100' : 'opacity-20'}`}>
        <div className="w-64 h-64 bg-emerald-500 rounded-full blur-[100px] animate-pulse"></div>
      </div>

      <div className="relative z-10 p-6 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Activity className={`text-emerald-500 ${status === 'idle' ? '' : 'animate-pulse'}`} />
          <span className="font-bold text-xl tracking-wider">LIVE MODE</span>
        </div>
        {status === 'connecting' && <span className="text-sm text-emerald-400 animate-pulse">Establishing Secure Uplink...</span>}
        {status === 'error' && <span className="text-sm text-red-400 flex items-center gap-2"><WifiOff size={14} /> {errorMessage}</span>}
      </div>

      <div className="flex-1 flex flex-col items-center justify-center relative z-10">
        <div className={`
                    w-48 h-48 rounded-full border-4 flex items-center justify-center transition-all duration-300
                    ${status === 'listening' ? 'border-emerald-500 shadow-[0_0_50px_rgba(16,185,129,0.5)] scale-110' : 'border-slate-700'}
                    ${status === 'speaking' ? 'border-emerald-400 shadow-[0_0_80px_rgba(52,211,153,0.8)] scale-100' : ''}
                `}>
          {status === 'idle' && <MicOff size={48} className="text-slate-600" />}
          {(status === 'listening' || status === 'connecting') && <Mic size={48} className="text-emerald-500" />}
          {status === 'speaking' && <Volume2 size={48} className="text-white animate-bounce" />}
        </div>

        <h2 className="mt-8 text-2xl font-light text-slate-300 text-center">
          {status === 'idle' && "Ready to connect"}
          {status === 'connecting' && "Connecting to Farm Swarm..."}
          {status === 'listening' && "Listening..."}
          {status === 'speaking' && "FarmXpert Speaking..."}
        </h2>

        <p className="mt-4 text-slate-500 max-w-md text-center">
          {status === 'listening' ? "Ask about weather, machinery status, or log a task." : "Hands-free voice interface for field operations."}
        </p>
      </div>

      <div className="relative z-10 p-8 pb-12 flex justify-center gap-6">
        {!isConnected ? (
          <button
            onClick={startSession}
            className="bg-emerald-600 hover:bg-emerald-500 text-white rounded-full px-12 py-6 text-xl font-bold shadow-lg transition-transform hover:scale-105 active:scale-95 flex items-center gap-3"
          >
            <Mic size={24} />
            START VOICE SESSION
          </button>
        ) : (
          <>
            <button
              onClick={toggleMute}
              className={`p-6 rounded-full border-2 transition-colors ${isMuted ? 'bg-red-500/20 border-red-500 text-red-500' : 'bg-slate-800 border-slate-600 text-white'}`}
            >
              {isMuted ? <MicOff size={28} /> : <Mic size={28} />}
            </button>

            <button
              onClick={cleanup}
              className="bg-red-600 hover:bg-red-500 text-white rounded-full px-12 py-6 text-xl font-bold shadow-lg transition-transform hover:scale-105 active:scale-95"
            >
              END SESSION
            </button>
          </>
        )}
      </div>

      <canvas ref={canvasRef} className="hidden" width="300" height="100"></canvas>
    </div>
  );
}
