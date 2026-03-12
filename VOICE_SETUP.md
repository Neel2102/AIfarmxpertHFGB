# Voice Feature Setup Instructions

## Issue Summary
The voice feature requires a Google AI API key to function. Without it, the voice agent will not be able to process speech or generate responses.

## Solution

### 1. Get Google AI API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 2. Add API Key to Environment

#### Option A: Update .env file (Recommended)
Add these lines to your `.env` file:
```
REACT_APP_API_KEY=your-google-ai-api-key-here
API_KEY=your-google-ai-api-key-here
```

#### Option B: Update .env.example and copy
1. Update `.env.example` (already done in this fix)
2. Copy it to `.env`: `cp .env.example .env`
3. Replace `your-google-ai-api-key-here` with your actual API key

### 3. Restart Services
```bash
docker compose restart frontend backend
```

### 4. Test the Voice Feature
1. Navigate to http://localhost:3000/dashboard/voice
2. Click "Tap to start" or "START VOICE SESSION"
3. Allow microphone permissions when prompted
4. The voice agent should now connect and respond

## Current Status
✅ Backend API endpoints fixed (no more 500 errors)
✅ Sidebar responsive issues fixed
✅ Voice interface ready (needs API key)
⚠️ Google AI API key required for voice functionality

## Troubleshooting
- If voice doesn't work, check browser console for API key errors
- Ensure microphone permissions are granted
- Verify the API key is correctly set in environment variables
