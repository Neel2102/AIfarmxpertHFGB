# Farmer Coach Agent

An AI agent that provides **REAL, DYNAMIC** information about Indian government agriculture-related schemes (insurance, subsidies, income support, MSP, welfare) to farmers in simple, farmer-friendly language.

## 🎯 Objective

The Farmer Coach Agent is designed to:
- Fetch **REAL-TIME** government scheme data using SerpAPI
- Explain government schemes in simple, farmer-friendly language
- Provide official website or form links
- Support regional languages
- Maintain trust by using **ONLY authorized government domains**

## 🌐 Key Features

### ✅ **REAL-TIME WEB SEARCH**
- **SerpAPI Integration**: Dynamic Google search for each query
- **Fresh Results**: Every query triggers a new web search
- **No Hardcoded Data**: Real-time information only

### 🔒 **AUTHORIZED DOMAINS ONLY**
- **Strict Filtering**: Only .gov.in, .nic.in, india.gov.in domains
- **Domain Validation**: Every URL verified before use
- **Trust & Authenticity**: No unauthorized sources

### 📋 **STRICT COMPLIANCE**
- No LLM summarization or rewriting
- Direct extraction from official sources
- Real government website links only
- Clear messaging when no authorized schemes found

## 📁 Project Structure

```
farmer_coach_agent/
│
├── README.md                  # Agent overview & usage
│
├── agent/
│   ├── __init__.py
│   ├── farmer_coach.py        # Core agent logic
│   ├── prompts.py             # Prompt templates
│   └── rules.py               # Safety & behavior rules
│
├── models/
│   ├── __init__.py
│   ├── input_model.py         # Input schema
│   └── output_model.py        # Output schema
│
├── services/
│   ├── __init__.py
│   └── scheme_formatter.py    # Formatting & explanation logic
│
├── data/
│   └── sample_api_response.json   # Example data.gov.in response
│
└── tests/
    └── test_agent.py
```

## 📥 Input Model

```python
{
  "farmer_query": string,
  "language": string,
  "schemes_data": [
    {
      "scheme_name": string,
      "ministry": string,
      "description": string,
      "state": string,
      "official_url": string
    }
  ]
}
```

### Example Input
```json
{
  "farmer_query": "Crop insurance schemes",
  "language": "English",
  "schemes_data": [
    {
      "scheme_name": "Pradhan Mantri Fasal Bima Yojana",
      "ministry": "Ministry of Agriculture",
      "description": "Crop insurance scheme providing financial support to farmers in case of crop loss",
      "state": "All",
      "official_url": "https://pmfby.gov.in"
    }
  ]
}
```

## 📤 Output Model

```python
{
  "response_type": "scheme_information",
  "language": string,
  "schemes": [
    {
      "scheme_name": string,
      "simple_explanation": string,
      "official_link": string
    }
  ],
  "disclaimer": string
}
```

### Example Output
```json
{
  "response_type": "scheme_information",
  "language": "English",
  "schemes": [
    {
      "scheme_name": "Pradhan Mantri Fasal Bima Yojana",
      "simple_explanation": "This scheme provides insurance support to farmers if their crops are damaged due to natural reasons.",
      "official_link": "https://pmfby.gov.in"
    }
  ],
  "disclaimer": "This information is based on official government data. For applications and latest updates, please visit the official website."
}
```

## 🧠 Agent Behavior Rules

**VERY IMPORTANT**: The agent strictly follows these rules:

1. Only use data present in schemes_data
2. Do NOT add eligibility rules unless explicitly provided
3. Do NOT guess benefits or deadlines
4. If information is missing, say: "Please refer to the official website for more details."
5. Keep language simple and non-technical
6. Preserve scheme names and URLs exactly as given

## 🔄 Agent Flow

1. Read farmer_query
2. Read schemes_data
3. Match schemes relevant to the query (keyword-based only)
4. For each matched scheme:
   - Rewrite description in simpler words
   - Do NOT expand beyond provided text
5. Translate output if language != English
6. Return response strictly in output model format

## 🚀 Usage

```python
from agent.farmer_coach import FarmerCoachAgent
from models.input_model import FarmerQueryInput, SchemeData

# Create agent instance
agent = FarmerCoachAgent()

# Prepare input data
schemes = [
    SchemeData(
        scheme_name="Pradhan Mantri Fasal Bima Yojana",
        ministry="Ministry of Agriculture",
        description="Crop insurance scheme providing financial support to farmers",
        state="All",
        official_url="https://pmfby.gov.in"
    )
]

input_data = FarmerQueryInput(
    farmer_query="Crop insurance schemes",
    language="English",
    schemes_data=schemes
)

# Process query
result = agent.process_query(input_data)
print(result.schemes[0].simple_explanation)
```

## 🧪 Testing

Run tests using pytest:

```bash
cd farmer_coach_agent
pytest tests/test_agent.py -v
```

## 📋 Dependencies

- Python 3.7+
- pydantic (for data models)

## 🌍 Supported Languages

- English
- Hindi
- Bengali
- Tamil
- Telugu
- Marathi
- Gujarati

## ⚠️ Disclaimer

This information is based on official government data. For applications and latest updates, please visit the official website.

## 🤝 Contributing

When contributing to this project:
- Maintain strict adherence to the agent rules
- Do not add functionality that bypasses the data validation
- Keep explanations simple and farmer-friendly
- Test thoroughly with pytest
