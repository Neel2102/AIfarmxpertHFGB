# 🌾 Crop Selector Agent

An AI decision-orchestrator designed for **Indian small and marginal farmers** that selects and recommends suitable crops by integrating outputs from multiple specialized agents.

## 🎯 Purpose

The Crop Selector Agent helps farmers:
- ✅ Avoid crop failure
- ✅ Reduce climate and market risk  
- ✅ Choose crops aligned with water, soil, and seasonal conditions
- ✅ Maintain stable income rather than speculative gains

**Core Principle**: Risk-minimization over profit maximization

## 🏗️ Architecture

The system follows an **orchestrator pattern** where the Crop Selector Agent integrates outputs from specialized agents:

```
┌─────────────────┐    ┌─────────────────┐
│   Farmer Input  │    │  Weather Agent  │
└────────┬────────┘    └────────┬────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ Crop Selector   │◄───┤   Soil Agent    │
│     Agent       │    └────────┬────────┘
└────────┬────────┘             │
         │                      ▼
         ▼              ┌─────────────────┐
┌─────────────────┐    │  Water Agent    │
│  Market Agent   │◄───└────────┬────────┘
└────────┬────────┘             │
         │                      ▼
         ▼              ┌─────────────────┐
┌─────────────────┐    │   Pest Agent    │
│Government Agent │◄───└─────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Recommendations│
└─────────────────┘
```

## 📁 Project Structure

```
crop_selector/
├── crop_selector_agent.py    # Main orchestrator agent
├── mock_agents.py           # Mock specialized agents for testing
├── example_usage.py         # Usage examples and demonstrations
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── tests/                  # Test files (to be added)
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd crop_selector

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from crop_selector_agent import CropSelectorAgent, FarmerContext
from mock_agents import MockAgentOrchestrator

# Initialize agents
crop_selector = CropSelectorAgent()
orchestrator = MockAgentOrchestrator()

# Define farmer context
farmer = FarmerContext(
    location={"state": "Punjab", "district": "Ludhiana"},
    season="Kharif",
    land_size_acre=5.0,
    risk_preference="Low"
)

# Get outputs from specialized agents
agent_outputs = orchestrator.get_all_agent_outputs(
    farmer.location["state"], 
    farmer.location["district"], 
    farmer.season
)

# Get crop recommendations
advice = crop_selector.get_advice_text(
    farmer,
    agent_outputs["weather"],
    agent_outputs["soil"],
    agent_outputs["water"],
    agent_outputs["pest"],
    agent_outputs["market"],
    agent_outputs["government"]
)

print(advice)
```

### Run Examples

```bash
python example_usage.py
```

## 📊 Input/Output Formats

### Farmer Context
```json
{
  "location": { "state": "Punjab", "district": "Ludhiana" },
  "season": "Kharif",
  "land_size_acre": 5.0,
  "risk_preference": "Low"
}
```

### Agent Outputs
Each specialized agent provides structured outputs (see `crop_selector_agent.py` for dataclass definitions).

### Final Recommendations
The system provides recommendations in three risk categories:
- 🟢 **Safest**: Score ≥ 0.70
- 🟡 **Balanced**: Score 0.55–0.69  
- 🔴 **Higher Risk**: Score < 0.55

## ⚖️ Risk-Weighted Scoring

The system uses a weighted scoring approach:

| Factor              | Weight |
| ------------------- | ------ |
| Weather suitability | 30%    |
| Water availability  | 25%    |
| Soil compatibility  | 20%    |
| Market stability    | 15%    |
| Pest risk           | 10%    |

Qualitative scoring: Low (0.3), Medium (0.6), High (0.9)

## 🛡️ Safety Rules

The agent follows strict safety rules:
- ❌ Never recommends water-intensive crops under scarcity
- ❌ Never recommends banned or unsafe crops
- ❌ Never suggests monocropping blindly
- ✅ Always communicates risk honestly
- ✅ Prefers lowest downside risk when uncertain

## 🧪 Testing

The system includes comprehensive mock agents for testing:
- **WeatherAgent**: Simulates weather patterns by region
- **SoilAgent**: Simulates soil analysis by state
- **WaterAgent**: Simulates water availability
- **PestAgent**: Simulates pest pressure by season
- **MarketAgent**: Simulates market conditions and MSP support
- **GovernmentAgent**: Simulates policy support

### Test Scenarios

The example usage includes:
1. Punjab farmer (Kharif) - Favorable conditions
2. Maharashtra farmer (Rabi) - Water constraints
3. Rajasthan farmer (Zaid) - High-risk environment
4. Edge cases and error handling

## 🔧 Integration Options

### 1. Direct Python Integration
```python
from crop_selector_agent import CropSelectorAgent
# Use directly in your Python application
```

### 2. API Integration (Future)
```python
# Planned FastAPI endpoint
response = requests.post('/api/crop-recommendations', json=farmer_context)
```

### 3. LangChain Integration (Future)
```python
# Planned LangChain wrapper
from crop_selector_langchain import CropSelectorChain
chain = CropSelectorChain()
result = chain.run(farmer_context)
```

### 4. CrewAI Integration (Future)
```python
# Planned CrewAI agent
from crop_selector_crewai import CropSelectorCrew
crew = CropSelectorCrew()
result = crew.kickoff(farmer_context)
```

## 🌍 Regional Coverage

Currently supports major Indian agricultural states:
- Punjab, Maharashtra, Tamil Nadu
- Uttar Pradesh, Rajasthan, West Bengal
- Karnataka, Gujarat

Seasonal coverage:
- **Kharif** (Monsoon): Rice, Cotton, Maize, Pulses
- **Rabi** (Winter): Wheat, Mustard, Chickpea, Vegetables  
- **Zaid** (Summer): Vegetables, Fruits, Melons

## 📈 Future Enhancements

### Planned Features
- [ ] Real-time weather API integration
- [ ] Soil testing data integration
- [ ] Market price feeds
- [ ] Government scheme API integration
- [ ] Voice/IVR interface
- [ ] Mobile app integration
- [ ] Confidence scoring improvements
- [ ] Historical yield data integration

### Framework Support
- [ ] LangChain integration
- [ ] CrewAI integration  
- [ ] AutoGen integration
- [ ] Custom LLM wrapper examples

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

[Add your license here]

## 📞 Support

For questions or support:
- Create an issue in the repository
- Check the examples in `example_usage.py`
- Review the dataclass definitions in `crop_selector_agent.py`

---

**Built with ❤️ for Indian farmers**
