# Centralized Tools & Database - Testing Script

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from farmxpert.tools import (
    get_weather_forecast, get_market_prices, analyze_soil_data,
    get_crop_recommendations, get_fertilizer_recommendations,
    get_irrigation_schedule, parse_location_string
)
from farmxpert.database import get_database_session
from farmxpert.core.core_agent_updated import process_farm_request

async def test_tools():
    """Test the centralized tools"""
    
    print("🧪 Testing Centralized Tools")
    print("=" * 50)
    
    # Test 1: Location parsing
    print("\n📍 Test 1: Location Parsing")
    location = parse_location_string("Punjab")
    print(f"✅ Location: {location}")
    
    # Test 2: Weather forecast
    print("\n🌤️ Test 2: Weather Forecast")
    weather = await get_weather_forecast("Punjab", days=3)
    print(f"✅ Weather source: {weather.get('source', 'Unknown')}")
    print(f"📝 Location: {weather.get('location', 'Unknown')}")
    
    # Test 3: Market prices
    print("\n💰 Test 3: Market Prices")
    prices = await get_market_prices("wheat", "Delhi")
    print(f"✅ Commodity: {prices.get('commodity', 'Unknown')}")
    print(f"💵 Current price: {prices.get('current_price', 'N/A')}")
    
    # Test 4: Soil analysis
    print("\n🌱 Test 4: Soil Analysis")
    soil_data = {
        "ph": 6.2,
        "nitrogen": "low",
        "phosphorus": "medium",
        "potassium": "high",
        "organic_matter": 1.8
    }
    soil_analysis = await analyze_soil_data(soil_data, "Punjab")
    print(f"✅ Soil health score: {soil_analysis.get('soil_health_score', 'N/A')}")
    
    # Test 5: Crop recommendations
    print("\n🌾 Test 5: Crop Recommendations")
    crops = await get_crop_recommendations("Maharashtra", "Kharif", "clay", 5.0)
    print(f"✅ Location: {crops.get('location', 'Unknown')}")
    print(f"📊 Recommended crops: {len(crops.get('recommended_crops', []))}")
    
    # Test 6: Fertilizer recommendations
    print("\n🧪 Test 6: Fertilizer Recommendations")
    fertilizer = await get_fertilizer_recommendations("wheat", soil_data, "Punjab")
    print(f"✅ Crop: {fertilizer.get('crop', 'Unknown')}")
    print(f"💰 Total cost: {fertilizer.get('total_cost', 'N/A')}")
    
    # Test 7: Irrigation schedule
    print("\n💧 Test 7: Irrigation Schedule")
    irrigation = await get_irrigation_schedule("wheat", "Punjab", "Rabi")
    print(f"✅ Crop: {irrigation.get('crop', 'Unknown')}")
    print(f"💧 Total water requirement: {irrigation.get('total_water_requirement', 'N/A')}")
    
    print("\n" + "=" * 50)
    print("🎉 All Tools Tests Complete!")

async def test_database():
    """Test database operations"""
    
    print("\n🧪 Testing Database Operations")
    print("=" * 50)
    
    try:
        # Test database connection
        db = get_database_session()
        print("✅ Database connection successful")
        
        # Note: We won't actually create data in this test
        # Just verify the functions are available
        from farmxpert.database import (
            create_user, create_farm, create_crop, save_soil_test,
            get_user_farms, get_farm_summary
        )
        print("✅ All database functions imported successfully")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Database Tests Complete!")

async def test_integrated_core_agent():
    """Test the updated core agent with centralized tools"""
    
    print("\n🧪 Testing Integrated Core Agent")
    print("=" * 50)
    
    # Test 1: Soil health agent with tools
    print("\n🌱 Test 1: Soil Health Agent (with tools)")
    response = await process_farm_request(
        "My soil pH is 5.8, what should I do?",
        "soil_health",
        {
            "location": "Punjab", 
            "crop": "wheat",
            "soil_data": {
                "ph": 5.8,
                "nitrogen": "low",
                "phosphorus": "medium"
            }
        }
    )
    print(f"✅ Success: {response['success']}")
    print(f"🔧 Tools used: {response['metadata']['tools_used']}")
    print(f"📝 Response: {response['response'][:100]}...")
    
    # Test 2: Crop selector with location and weather
    print("\n🌾 Test 2: Crop Selector (with location & weather)")
    response = await process_farm_request(
        "What crops should I plant in clay soil during monsoon?",
        "crop_selector",
        {
            "season": "Kharif", 
            "location": "Maharashtra",
            "soil_type": "clay",
            "land_size_acres": 3.0
        }
    )
    print(f"✅ Success: {response['success']}")
    print(f"🔧 Tools used: {response['metadata']['tools_used']}")
    print(f"💡 Recommendations: {len(response['recommendations'])}")
    
    # Test 3: Market intelligence with real data
    print("\n💰 Test 3: Market Intelligence (with market data)")
    response = await process_farm_request(
        "What are wheat prices now and should I sell?",
        "market_intelligence",
        {
            "location": "Delhi",
            "crop": "wheat",
            "commodity": "wheat"
        }
    )
    print(f"✅ Success: {response['success']}")
    print(f"🔧 Tools used: {response['metadata']['tools_used']}")
    print(f"📊 Data available: {list(response['data']['tool_data'].keys())}")
    
    # Test 4: Irrigation planning with weather integration
    print("\n💧 Test 4: Irrigation Planner (with weather)")
    response = await process_farm_request(
        "When should I irrigate my wheat crop?",
        "irrigation_planner",
        {
            "location": "Punjab",
            "crop": "wheat",
            "season": "Rabi",
            "soil_type": "loamy"
        }
    )
    print(f"✅ Success: {response['success']}")
    print(f"🔧 Tools used: {response['metadata']['tools_used']}")
    
    print("\n" + "=" * 50)
    print("🎉 Integrated Core Agent Tests Complete!")

async def main():
    """Run all tests"""
    
    print("🚀 Testing Centralized Tools & Database Integration")
    print("=" * 60)
    
    # Test tools
    await test_tools()
    
    # Test database
    await test_database()
    
    # Test integrated core agent
    await test_integrated_core_agent()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE!")
    print("\n🎯 Benefits Achieved:")
    print("  ✅ Centralized all API calls in tools.py")
    print("  ✅ Centralized all database operations in database.py")
    print("  ✅ Simplified core_agent.py imports")
    print("  ✅ No more scattered tool classes")
    print("  ✅ Straightforward function calls")
    print("  ✅ Easy debugging and maintenance")
    
    print("\n🔧 Architecture Summary:")
    print("  📁 tools.py - All external API calls")
    print("  📁 database.py - All PostgreSQL operations")
    print("  📁 core_agent.py - Uses tools.py & database.py")
    print("  🎯 Single point of maintenance for each concern")

if __name__ == "__main__":
    asyncio.run(main())
