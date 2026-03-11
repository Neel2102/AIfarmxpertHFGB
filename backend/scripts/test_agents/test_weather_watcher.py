import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to python path for simple testing
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from farmxpert.agents.agronomy.weather_watcher_agent import WeatherWatcherAgent

async def test_weather_watcher():
    print("Initializing WeatherWatcherAgent...")
    agent = WeatherWatcherAgent()
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    test_input = {
        "query": "What's the weather like in New Delhi for farming today?",
        "context": {
            "location": {
                "latitude": 28.6139,
                "longitude": 77.2090
            },
            "location_text": "New Delhi"
        }
    }
    
    print(f"\nSending input: {json.dumps(test_input, indent=2)}\n")
    try:
        response = await agent.handle(test_input)
        print("\n--- Response Received ---")
        print(json.dumps(response, indent=2))
        print("\nTest passed! WeatherWatcherAgent successfully processed input.")
    except Exception as e:
        print(f"Error during agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_weather_watcher())
