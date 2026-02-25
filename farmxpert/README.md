# FarmXpert: Multi-Agent AI Platform for Precision Farming

FarmXpert is an AI-powered farming advisory system that uses Gemini API and real database data to provide intelligent farming recommendations.

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd farmxpert

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and DATABASE_URL

# Initialize database
python scripts/init_db.py

# Start server
python start.py
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm start
```

## 🔧 Configuration

Create `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://user:password@localhost/farmxpert_db
```

## 🧠 AI Agents

- **Soil Health Agent**: Analyzes soil data using Gemini API
- **Task Scheduler Agent**: Creates farm task schedules
- **Crop Selector Agent**: Recommends optimal crops
- **Market Intelligence Agent**: Provides market insights
- **Yield Predictor Agent**: Predicts crop yields
- And 17+ more specialized agents...

## 📊 Features

- Real database integration (PostgreSQL)
- Gemini API for intelligent responses
- Modern React frontend
- RESTful API with FastAPI
- Comprehensive farm management
- Real-time data updates

## 🎯 Usage

1. Start backend: `python start.py`
2. Start frontend: `cd frontend && npm start`
3. Open http://localhost:3000
4. View farm dashboard with real data
5. Use AI agents for farming advice

## 📁 Project Structure

```
farmxpert/
├── agents/          # AI Agent implementations
├── core/           # Core system components
├── models/         # Database models
├── repositories/   # Data access layer
├── services/       # Gemini API service
├── interfaces/     # FastAPI application
├── frontend/       # React frontend
└── scripts/        # Database initialization
```

---

**FarmXpert** - AI-powered precision farming guidance.
