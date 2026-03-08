import { GoogleGenAI, Type, Schema } from "@google/genai";
import { AGENTS } from '../constants';
import { ChatMessage } from '../types';
import { api } from './api';

// Schema for structured JSON response
const RESPONSE_SCHEMA: Schema = {
  type: Type.OBJECT,
  properties: {
    agentId: { type: Type.STRING },
    agentName: { type: Type.STRING },
    response: { type: Type.STRING },
    suggestedActions: { 
      type: Type.ARRAY,
      items: { type: Type.STRING }
    }
  },
  required: ['agentId', 'agentName', 'response']
};

const ORCHESTRATOR_SYSTEM_INSTRUCTION = `
You are the "FarmXpert Orchestrator", the central brain of a smart farming system.
You have access to a team of specialized AI agents.
Your goal is to help the farmer by understanding their request and delegating the response to the most appropriate agent.

Here are your available agents:
${AGENTS.map(a => `- ID: "${a.id}", Name: "${a.name}", Role: "${a.description}"`).join('\n')}

INSTRUCTIONS:
1. Analyze the user's input (Text and optionally Images).
2. Decide which agent is best suited to answer. 
   - If the user provides an image of a plant leaf or bug, delegate to "pest_disease".
   - If the query is general or about management, YOU (the Orchestrator) answer.
3. Adopt the persona of that selected agent.
4. Provide a helpful, professional, and domain-specific answer.
5. You MUST return your response in a strict JSON format.
`;

export const sendMessageToOrchestrator = async (
  message: string,
  history: ChatMessage[],
  targetAgentId: string | null = null,
  image?: { data: string, mimeType: string } | null
): Promise<{ agentId: string; agentName: string; response: string; suggestedActions?: string[]; isQueued?: boolean }> => {
  
  // OFFLINE CHECK
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
    // Initialize the client inside the function to ensure fresh config/keys if needed
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    const model = 'gemini-3-pro-preview';
    
    // 1. Fetch Real-Time Context
    const user = await api.auth.getSession();
    const devices = await api.hardware.getDevices();
    const fields = await api.fields.getFields();
    
    const liveContext = `
    --- REAL-TIME FARM CONTEXT ---
    USER: ${user ? `${user.name} (${user.role})` : 'Guest'}
    FARM: ${user ? user.farmName : 'Unknown Farm'}
    
    MAPPED FIELDS:
    ${fields.length > 0 ? fields.map(f => `- Field Name: "${f.name}", Crop: "${f.crop}", Area: ${f.area}ha, Center Lat/Lng: ${JSON.stringify(f.coordinates[0])}`).join('\n') : 'No fields mapped yet.'}

    LIVE TELEMETRY (Sensors/Drones/Machinery):
    ${devices.map(d => `- [${d.type.toUpperCase()}] ${d.name} (${d.status}): ${JSON.stringify(d.readings)}`).join('\n')}
    ------------------------------
    `;

    // 2. Determine System Instruction
    let systemInstruction = ORCHESTRATOR_SYSTEM_INSTRUCTION + '\n' + liveContext;
    
    if (targetAgentId && targetAgentId !== 'orchestrator') {
      const agent = AGENTS.find(a => a.id === targetAgentId);
      if (agent) {
        // Direct Agent Mode: We force the model to be this specific agent
        systemInstruction = `
          You are the "${agent.name}" (${agent.id}).
          Description: ${agent.description}
          Persona: ${agent.persona}
          
          ${liveContext}

          You are speaking directly to the farmer. DO NOT pretend to be an orchestrator.
          Answer purely from your domain of expertise using the live context provided.
          
          You MUST return your response in a strict JSON format matching the schema provided.
          For the 'agentId' field in JSON, always use "${agent.id}".
          For the 'agentName' field in JSON, always use "${agent.name}".
        `;
      }
    }

    // 3. Convert app history to API history format (including past images)
    const recentHistory = history.slice(-10).map(msg => {
      const parts: any[] = [{ text: msg.text }];
      if (msg.attachment?.type === 'image') {
        // Remove data URL prefix for API if stored in history
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
        parts: parts,
      };
    });

    const chat = ai.chats.create({
      model: model,
      history: recentHistory,
      config: {
        systemInstruction: systemInstruction,
        responseMimeType: "application/json",
        responseSchema: RESPONSE_SCHEMA,
      },
    });

    // 4. Construct current message content (Text + Optional Image)
    const currentMessageParts: any[] = [{ text: message || " " }]; // Ensure text is never empty
    
    if (image) {
       const base64Data = image.data.replace(/^data:image\/[a-z]+;base64,/, "");
       currentMessageParts.push({
           inlineData: {
               data: base64Data,
               mimeType: image.mimeType
           }
       });
    }

    // Fix: Explicitly cast the message payload to avoid TypeScript strict checking issues with the SDK types
    const result = await chat.sendMessage({ message: currentMessageParts } as any);

    const text = result.text;
    if (!text) throw new Error("No response from Gemini");

    let parsed;
    try {
        parsed = JSON.parse(text);
    } catch (e) {
        // Fallback if model returns Markdown json block or raw text
        const cleaned = text.replace(/```json/g, '').replace(/```/g, '').trim();
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

    // LOG SUCCESSFUL INTERACTION
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
    console.error("Gemini API Error:", error);
    
    // LOG FAILED INTERACTION
    const latency = Date.now() - startTime;
    await api.logs.addLog({
      timestamp: Date.now(),
      userQuery: message + (image ? " [Image Uploaded]" : ""),
      selectedAgentId: targetAgentId || 'orchestrator',
      agentName: 'System Error',
      response: (error as Error).message,
      latencyMs: latency,
      status: 'error'
    });

    return {
      agentId: targetAgentId || 'orchestrator',
      agentName: targetAgentId ? (AGENTS.find(a => a.id === targetAgentId)?.name || 'Agent') : 'FarmXpert Orchestrator',
      response: "I'm having trouble connecting to the agent network right now. Please check your connection and try again.",
      suggestedActions: ["Retry"]
    };
  }
};