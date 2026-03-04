# FarmXpert: Multi-Agent AI Platform for Precision Farming

FarmXpert is an AI-powered farming advisory system that uses Gemini API and real database data to provide intelligent farming recommendations.


### Software Requirements
- Python 3.9+
- Node.js 16.x+
- PostgreSQL 13+
- Git

## 🏗️ System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Edge Devices  │────▶│  FarmXpert API  │◀───▶│  Gemini AI API  │
│  (IoT Sensors)  │     │  (FastAPI)      │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │                 │     │                 │
                        │  PostgreSQL DB  │◀───▶│  React Frontend  │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
```

## �🚀 Quick Start

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

### Local Development
1. Start backend: `python start.py`
2. Start frontend: `cd frontend && npm start`
3. Open http://localhost:3000
4. View farm dashboard with real data
5. Use AI agents for farming advice

### Production Deployment
For production deployment, we recommend using:
- **Web Server**: Nginx or Apache
- **Process Manager**: PM2 or Gunicorn
- **Containerization**: Docker with docker-compose
- **Monitoring**: Prometheus + Grafana

### IoT Device Setup
1. Flash Raspberry Pi OS on SD card
2. Install required packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3-pip python3-venv git
   ```
3. Clone the repository and install dependencies
4. Configure environment variables for device-specific settings
5. Run the edge service: `python edge/device_manager.py`

## 📁 Project Structure

```
farmxpert/
├── agents/           # AI Agent implementations
├── core/            # Core system components
├── models/          # Database models
├── repositories/    # Data access layer
├── services/        # Gemini API service
├── interfaces/      # FastAPI application
├── frontend/        # React frontend
├── edge/            # IoT edge device code
│   ├── sensors/     # Sensor drivers and interfaces
│   └── device_manager.py  # Main edge device controller
├── scripts/         # Database initialization
└── docs/            # Documentation
    ├── api/         # API documentation
    └── hardware/    # Hardware setup guides
```

## 📶 Network Requirements

- **Bandwidth**: Minimum 5Mbps for basic operation, 20Mbps recommended for video streaming
- **Latency**: < 100ms for real-time operations
- **Ports**: 
  - 3000: Frontend development server
  - 8000: Backend API server
  - 1883: MQTT (for IoT devices, optional)
  - 80/443: Standard HTTP/HTTPS ports for production

## 🔧 Maintenance

### System Updates
Regularly update dependencies:
```bash
# Backend
pip install -r requirements.txt --upgrade

# Frontend
cd frontend
npm update
```

### Hardware Maintenance
- Clean sensors monthly
- Check battery levels weekly for field devices
- Perform system health checks using the admin dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**FarmXpert** - AI-powered precision farming guidance. Developed with ❤️ for sustainable agriculture.
