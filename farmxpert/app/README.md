# FarmXpert Application Core

This directory contains the core application logic for FarmXpert - an AI-powered agricultural assistant built with a modular monolith architecture using FastAPI and the orchestrator pattern.

## 🏗️ Architecture Overview

FarmXpert uses a **modular monolith** architecture with an **orchestrator pattern** to coordinate multiple specialized AI agents while maintaining logical boundaries and clean separation of concerns.

### Key Components

```
app/
├── agents/                    # Specialized AI agents
│   ├── market_intelligence/   # Market analysis and pricing
│   ├── task_scheduler/        # Farm task planning and scheduling
│   └── weather_watcher/       # Weather monitoring and alerts
├── orchestrator/              # Central coordination layer
│   ├── agent.py              # Main orchestrator logic
│   └── services/             # Shared services (LLM, etc.)
├── shared/                    # Shared utilities and models
└── config.py                 # Application configuration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FastAPI
- Required API keys (see Environment Setup)

### Environment Setup

Create a `.env` file in the project root with:

```bash
# Weather APIs
OPENWEATHER_API_KEY=your_openweather_api_key
WEATHERAPI_KEY=your_weatherapi_key

# AI/LLM APIs
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Other APIs
DATA_GOV_API_KEY=your_data_gov_api_key
SMS_API_KEY=your_sms_api_key

# Optional
REDIS_URL=your_redis_url
```

### Running the Application

```bash
# From project root
python start_server.py

# Or using uvicorn directly
python -m uvicorn farmxpert.interfaces.api.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

## 🤖 AI Agents

### 1. Weather Watcher (`agents/weather_watcher/`)
**Purpose**: Real-time weather monitoring and agricultural weather analysis

**Features**:
- Current weather conditions
- Weather alerts and warnings
- Agricultural weather insights
- Multi-source weather data integration

**Usage**:
```python
from app.agents.weather_watcher.service import WeatherWatcherService

service = WeatherWatcherService()
weather_data = service.get_weather("ahmedabad")
```

### 2. Market Intelligence (`agents/market_intelligence/`)
**Purpose**: Crop market analysis, pricing, and selling recommendations

**Features**:
- Real-time market prices
- Best market recommendations
- Revenue estimation
- Market trend analysis

**Usage**:
```python
from app.agents.market_intelligence.service import MarketIntelligenceService

service = MarketIntelligenceService()
market_data = service.analyze_market("cotton")
```

### 3. Task Scheduler (`agents/task_scheduler/`)
**Purpose**: Intelligent farm task planning and prioritization

**Features**:
- Priority-based task scheduling
- Weather-aware planning
- Resource allocation
- AI-powered task optimization

**Usage**:
```python
from app.agents.task_scheduler.service import TaskSchedulerService

service = TaskSchedulerService()
tasks = service.generate_daily_plan("cotton", "vegetative")
```

## 🎯 Orchestrator Pattern

The orchestrator (`orchestrator/agent.py`) serves as the central coordination layer:

### Key Responsibilities

1. **Agent Routing**: Determines which agents to call based on user queries
2. **Data Aggregation**: Collects and combines results from multiple agents
3. **LLM Integration**: Generates intelligent summaries using AI models
4. **Error Handling**: Graceful fallbacks and error management
5. **Response Formatting**: Structures responses for different interfaces

### Usage Example

```python
from app.orchestrator.agent import OrchestratorAgent

orchestrator = OrchestratorAgent()

# Single agent query
response = orchestrator.handle_request({
    "query": "weather in ahmedabad",
    "session_id": "user123"
})

# Multi-agent comprehensive query
response = orchestrator.handle_request({
    "query": "farming advice for cotton",
    "session_id": "user123"
})
```

## 🔧 Configuration

### Main Configuration (`config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./farmxpert.db"
    
    # External APIs
    openweather_api_key: str = ""
    gemini_api_key: str = ""
    
    class Config:
        env_file = ".env"
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `DATA_GOV_API_KEY` | Data.gov API key | Optional |

## 📡 API Endpoints

### Chat Interface
```http
POST /chat
Content-Type: application/json

{
    "query": "weather in ahmedabad",
    "session_id": "user123"
}
```

### Task Scheduler
```http
POST /task-schedule?crop=cotton&growth_stage=vegetative
Content-Type: application/json

{
    "location": "ahmedabad",
    "resources": {
        "water": "sufficient",
        "labor": "available"
    }
}
```

### Agent Status
```http
GET /status
```

## 🧪 Testing

### Running Tests

```bash
# Test all agents
python test_all_agents.py

# Test specific agent
python test_weather_agent.py

# Test API endpoints
python test_api_endpoints.py
```

### Test Coverage

- Unit tests for individual agents
- Integration tests for orchestrator
- API endpoint tests
- LLM service tests

## 🔍 Debugging

### Enable Debug Mode

```python
# In config.py
DEBUG = True

# Or via environment
DEBUG=true python start_server.py
```

### Common Debugging Tools

1. **Agent Debugging**:
```python
from app.orchestrator.agent import OrchestratorAgent
orchestrator = OrchestratorAgent()
orchestrator.debug_mode = True
```

2. **LLM Service Debugging**:
```python
from app.orchestrator.services.llm_service import OrchestratorLLMService
service = OrchestratorLLMService()
service.debug_mode = True
```

3. **API Debugging**:
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "weather in ahmedabad", "session_id": "debug"}'
```

## 🚨 Error Handling

### Agent-Level Errors

Each agent implements proper error handling:

```python
try:
    result = agent.process_request(request)
except APIKeyError:
    return {"error": "Invalid API key"}
except RateLimitError:
    return {"error": "Rate limit exceeded"}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"error": "Internal server error"}
```

### Orchestrator-Level Errors

The orchestrator provides fallback mechanisms:

1. **LLM Fallback**: Uses template-based responses if AI fails
2. **Agent Fallback**: Continues with available agents if one fails
3. **Graceful Degradation**: Provides partial results if possible

## 📊 Monitoring

### Health Checks

```http
GET /health
```

### Metrics

The application provides built-in metrics:

- Agent response times
- LLM service performance
- API endpoint usage
- Error rates

### Logging

Structured logging with different levels:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Agent request processed")
logger.warning("Rate limit approaching")
logger.error("API call failed", exc_info=True)
```

## 🔄 Development Workflow

### Adding a New Agent

1. **Create Agent Directory**:
```bash
mkdir app/agents/new_agent
```

2. **Implement Agent Service**:
```python
# app/agents/new_agent/service.py
class NewAgentService:
    def process_request(self, request):
        # Agent logic here
        return result
```

3. **Register with Orchestrator**:
```python
# app/orchestrator/agent.py
def _resolve_agents(request):
    # Add agent matching logic
    if "new_agent_keyword" in query:
        agents.append("new_agent")
```

4. **Add Tests**:
```python
# tests/test_new_agent.py
def test_new_agent():
    # Test implementation
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Document all public methods
- Write comprehensive tests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the main project README for details.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting guide
2. Review existing issues
3. Create a new issue with detailed information
4. Include logs and error messages

## 🔮 Future Enhancements

- [ ] Additional agent integrations
- [ ] Advanced analytics dashboard
- [ ] Mobile app API
- [ ] Real-time notifications
- [ ] Multi-language support
- [ ] Advanced ML models

---

**FarmXpert Application Core** - Building the future of smart farming! 🌾✨
