import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

async def test_tools():
    print("=== Testing Crop Planning & Operations Tools ===\n")

    # 1. Market Scraper
    print("1. Testing MarketScraperTool...")
    try:
        from farmxpert.tools.crop_planning.market_scraper import MarketScraperTool
        scraper = MarketScraperTool()
        prices = scraper.fetch_market_prices("Wheat", "Gujarat")
        print(f"   [SUCCESS] Fetched {len(prices)} price records.")
        print(f"   Sample: {prices[0] if prices else 'None'}")
    except Exception as e:
        print(f"   [FAILED] {e}")

    print("\n2. Testing WeatherClientTool...")
    try:
        from farmxpert.tools.crop_planning.weather_client import WeatherClientTool
        weather = WeatherClientTool()
        forecast = weather.get_forecast("Amrelim")
        print(f"   [SUCCESS] Fetched forecast for {forecast.get('city', {}).get('name', 'Unknown')}")
        print(f"   Source: {forecast.get('source', 'Unknown')}")
    except Exception as e:
        print(f"   [FAILED] {e}")

    print("\n3. Testing SoilSensorTool...")
    try:
        from farmxpert.tools.crop_planning.soil_sensor import SoilSensorTool
        sensor = SoilSensorTool()
        data = sensor.get_realtime_data("sensor_01")
        print(f"   [SUCCESS] Sensor Data: Moisture={data.get('moisture_percent')}% pH={data.get('ph_level')}")
    except Exception as e:
        print(f"   [FAILED] {e}")

    print("\n4. Testing TaskOptimizerTool...")
    try:
        from farmxpert.tools.operations.task_optimizer import TaskOptimizerTool
        optimizer = TaskOptimizerTool()
        tasks = [
            {"id": 1, "title": "Irrigation", "priority": "high", "estimated_hours": 4},
            {"id": 2, "title": "Weeding", "priority": "low", "estimated_hours": 2},
            {"id": 3, "title": "Pest Control", "priority": "critical", "estimated_hours": 1} # critical mapped to high if not handled
        ]
        result = optimizer.optimize_schedule(tasks)
        print(f"   [SUCCESS] Scheduled {len(result.get('optimized_schedule', []))} tasks.")
        print(f"   Schedule: {[t['title'] for t in result.get('optimized_schedule', [])]}")
    except Exception as e:
        print(f"   [FAILED] {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_tools())
