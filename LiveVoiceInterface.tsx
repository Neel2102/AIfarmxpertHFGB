import React, { useEffect, useRef, useState } from 'react';
import { GoogleGenAI, LiveServerMessage, Modality, Type, FunctionDeclaration } from "@google/genai";
import { Mic, MicOff, X, Activity, Volume2, WifiOff } from 'lucide-react';
import { api } from '../services/api';

// --- AUDIO UTILS ---
function createBlob(data: Float32Array): { data: string, mimeType: string } {
  const l = data.length;
  const int16 = new Int16Array(l);
  for (let i = 0; i < l; i++) {
    // Clamp and convert float (-1 to 1) to int16
    const s = Math.max(-1, Math.min(1, data[i]));
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  
  // Manual manual Base64 encoding of the Int16 buffer
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

function decodeBase64(base64: string): Uint8Array {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

export const LiveVoiceInterface: React.FC = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [status, setStatus] = useState<'idle' | 'connecting' | 'listening' | 'speaking' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');
    
    // Audio Context Refs
    const inputContextRef = useRef<AudioContext | null>(null);
    const outputContextRef = useRef<AudioContext | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const sessionRef = useRef<any>(null); // To store the session object
    const nextStartTimeRef = useRef<number>(0);
    const audioSourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());
    
    // Canvas for Visualizer
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationFrameRef = useRef<number>(0);

    // Tool Definitions
    const getFarmStatusTool: FunctionDeclaration = {
        name: 'getFarmStatus',
        description: 'Get real-time telemetry and status of farm devices.',
        parameters: {
            type: Type.OBJECT,
            properties: {},
        }
    };

    const startSession = async () => {
        try {
            setStatus('connecting');
            setErrorMessage('');

            // 1. Initialize Audio Contexts
            const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
            inputContextRef.current = new AudioContext({ sampleRate: 16000 });
            outputContextRef.current = new AudioContext({ sampleRate: 24000 });
            nextStartTimeRef.current = outputContextRef.current.currentTime;

            // 2. Initialize Gemini Client
            const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
            
            // 3. Connect to Live API
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
                        console.log('Session Opened');
                        setIsConnected(true);
                        setStatus('listening');
                        
                        // Stream audio from the microphone to the model.
                        try {
                            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                            streamRef.current = stream;
                            
                            const source = inputContextRef.current!.createMediaStreamSource(stream);
                            const processor = inputContextRef.current!.createScriptProcessor(4096, 1, 1);
                            processorRef.current = processor;

                            processor.onaudioprocess = (e) => {
                                if (isMuted) return;
                                const inputData = e.inputBuffer.getChannelData(0);
                                const blob = createBlob(inputData);
                                
                                sessionPromise.then(session => {
                                    session.sendRealtimeInput({ media: blob });
                                });
                                
                                // Simple visualizer drive
                                drawVisualizer(inputData, 'input');
                            };

                            source.connect(processor);
                            processor.connect(inputContextRef.current!.destination);
                            
                        } catch (err) {
                            console.error('Mic Error:', err);
                            setStatus('error');
                            setErrorMessage('Microphone access denied.');
                        }
                    },
                    onmessage: async (msg: LiveServerMessage) => {
                        // Handle Tools
                        if (msg.toolCall) {
                            setStatus('speaking'); // Model is "thinking/acting"
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

                        // Handle Audio
                        const audioData = msg.serverContent?.modelTurn?.parts?.[0]?.inlineData?.data;
                        if (audioData) {
                            setStatus('speaking');
                            playAudioChunk(audioData);
                        }

                        // Handle Interruption
                        if (msg.serverContent?.interrupted) {
                            console.log('Interrupted');
                            stopAllAudio();
                            setStatus('listening');
                        }

                        // Turn Complete
                        if (msg.serverContent?.turnComplete) {
                            setStatus('listening');
                        }
                    },
                    onclose: () => {
                        console.log('Session Closed');
                        cleanup();
                    },
                    onerror: (err) => {
                        console.error('Session Error', err);
                        setStatus('error');
                        setErrorMessage('Connection lost.');
                        cleanup();
                    }
                }
            });
            
            // Store session promise reference if needed, though mostly handled in callbacks
            sessionRef.current = sessionPromise;

        } catch (e) {
            console.error(e);
            setStatus('error');
            setErrorMessage('Failed to initialize voice session.');
        }
    };

    const playAudioChunk = async (base64Data: string) => {
        if (!outputContextRef.current) return;
        
        try {
            const rawBytes = decodeBase64(base64Data);
            const dataInt16 = new Int16Array(rawBytes.buffer);
            const float32 = new Float32Array(dataInt16.length);
            
            for (let i = 0; i < dataInt16.length; i++) {
                float32[i] = dataInt16[i] / 32768.0;
            }
            
            // Visualizer drive for output
            drawVisualizer(float32, 'output');

            const buffer = outputContextRef.current.createBuffer(1, float32.length, 24000);
            buffer.copyToChannel(float32, 0);

            const source = outputContextRef.current.createBufferSource();
            source.buffer = buffer;
            source.connect(outputContextRef.current.destination);
            
            // Schedule
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
            console.error("Audio Decode Error", e);
        }
    };

    const stopAllAudio = () => {
        audioSourcesRef.current.forEach(s => s.stop());
        audioSourcesRef.current.clear();
        if (outputContextRef.current) {
            nextStartTimeRef.current = outputContextRef.current.currentTime;
        }
    };

    const cleanup = () => {
        setIsConnected(false);
        setStatus('idle');
        
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop());
        }
        if (processorRef.current) {
            processorRef.current.disconnect();
        }
        if (inputContextRef.current) {
            inputContextRef.current.close();
        }
        if (outputContextRef.current) {
            outputContextRef.current.close();
        }
        stopAllAudio();
    };

    const toggleMute = () => {
        setIsMuted(!isMuted);
    };

    // --- VISUALIZER ---
    const drawVisualizer = (data: Float32Array, mode: 'input' | 'output') => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Simple RMS calc for amplitude
        let sum = 0;
        for (let i = 0; i < data.length; i += 10) { // skip for speed
            sum += data[i] * data[i];
        }
        const rms = Math.sqrt(sum / (data.length / 10));
        const height = Math.min(canvas.height, rms * canvas.height * 10); // scale up

        // We aren't doing a full loop here, just reacting to chunks to trigger css anims or simple draws
        // For a smoother look, we'd use AnalyserNode, but raw PCM chunks are discrete.
        // Let's just use CSS animation based on state for now, it's cleaner for React.
    };

    useEffect(() => {
        return () => cleanup();
    }, []);

    return (
        <div className="flex flex-col h-full bg-slate-900 text-white relative overflow-hidden">
            
            {/* Background Pulse Animation */}
            <div className={`absolute inset-0 flex items-center justify-center transition-opacity duration-500 ${status === 'speaking' ? 'opacity-100' : 'opacity-20'}`}>
                <div className="w-64 h-64 bg-emerald-500 rounded-full blur-[100px] animate-pulse"></div>
            </div>

            {/* Header */}
            <div className="relative z-10 p-6 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <Activity className={`text-emerald-500 ${status === 'idle' ? '' : 'animate-pulse'}`} />
                    <span className="font-bold text-xl tracking-wider">LIVE MODE</span>
                </div>
                {status === 'connecting' && <span className="text-sm text-emerald-400 animate-pulse">Establishing Secure Uplink...</span>}
                {status === 'error' && <span className="text-sm text-red-400 flex items-center gap-2"><WifiOff size={14}/> {errorMessage}</span>}
            </div>

            {/* Main Visualizer Area */}
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

            {/* Controls */}
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
            
            {/* Hidden Canvas for data processing if needed later */}
            <canvas ref={canvasRef} className="hidden" width="300" height="100"></canvas>
        </div>
    );
};