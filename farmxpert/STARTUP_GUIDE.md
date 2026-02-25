# 🚀 FarmXpert Startup Guide

Complete guide to get FarmXpert running on your system.

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm (for frontend)
- **Gemini API Key** (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

## 🏃‍♂️ Quick Start

### 1. Backend Setup

```powershell
# Navigate to farmxpert directory
cd farmxpert

# Install Python dependencies
pip install -r requirements.txt

# Create .env file with your Gemini API key
New-Item -ItemType File -Path ".env" -Force
Add-Content -Path ".env" -Value "GEMINI_API_KEY=your-actual-gemini-api-key-here"
Add-Content -Path ".env" -Value "APP_NAME=FarmXpert API"
Add-Content -Path ".env" -Value "APP_ENV=development"
Add-Content -Path ".env" -Value "APP_HOST=0.0.0.0"
Add-Content -Path ".env" -Value "APP_PORT=8000"

# Start the backend server
python start.py
```

### 2. Frontend Setup (in another terminal)

```powershell
# Install frontend dependencies
cd frontend
npm install

# Start the frontend development server
npm start
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Manual Setup (Alternative)

### Backend Only

```powershell
# Install dependencies
pip install -r requirements.txt

# Start server manually
python -m uvicorn farmxpert.interfaces.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Only

```powershell
cd frontend
npm install
npm start
```

## 🧪 Testing the System

### Test Backend API

```powershell
# Health check
curl http://localhost:8000/health/live

# List agents
curl http://localhost:8000/agents

# Test orchestration
curl -X POST http://localhost:8000/orchestrate -H "Content-Type: application/json" -d '{"query": "What should I grow this season?", "context": {"season": "rabi", "location": "ahmedabad"}}'
```

### Test Frontend

1. Open http://localhost:3000
2. Navigate through different pages
3. Try the AI chat feature
4. Check the analytics dashboard

## 📱 Features Available

### 🌾 Dashboard
- Welcome section with quick actions
- Performance metrics
- Weather overview
- Recent activity

### 🤖 AI Chat
- Interactive chat with farming AI
- Quick action buttons
- Real-time responses
- Multi-agent orchestration

### 🔧 Agents Management
- View all 22+ AI agents
- Organized by categories
- Agent status and controls
- Direct invocation

### 📊 Analytics
- Crop yield trends
- Profit analysis
- Soil health metrics
- Weather data

### ⚙️ Settings
- Profile management
- API key configuration
- Notification preferences
- System settings

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```powershell
   # Kill process using port 8000
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

2. **Node.js not found**
   - Install Node.js from https://nodejs.org/
   - Restart your terminal

3. **Python dependencies error**
   ```powershell
   # Try with --user flag
   pip install --user -r requirements.txt
   ```

4. **Gemini API key error**
   - Make sure your API key is correct
   - Check if the key has proper permissions
   - Verify the .env file format

### Getting Help

- Check the logs in the terminal
- Verify all services are running
- Ensure ports 3000 and 8000 are available
- Check your internet connection for API calls

## 🔄 Development Workflow

### Backend Development
1. Make changes to Python files
2. Server auto-reloads with uvicorn --reload
3. Test API endpoints

### Frontend Development
1. Make changes to React files
2. Browser auto-refreshes with hot reload
3. Test UI components

### Full Stack Testing
1. Start both backend and frontend
2. Test complete workflows
3. Verify API integration

## 📦 Production Deployment

### Backend
```powershell
# Build for production
pip install -r requirements.txt

# Run with production server
python -m uvicorn farmxpert.interfaces.api.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```powershell
cd frontend
npm run build
# Deploy the 'build' folder to your hosting service
```

## 🎯 Next Steps

1. **Explore the AI Agents**: Try different farming scenarios
2. **Customize Settings**: Configure your API keys and preferences
3. **Test Analytics**: View your farm's performance metrics
4. **Chat with AI**: Ask farming questions and get expert advice

## 📞 Support

If you encounter any issues:
1. Check this guide first
2. Review the terminal logs
3. Verify your API keys
4. Ensure all dependencies are installed

---

**Happy Farming with FarmXpert! 🌾🤖**
