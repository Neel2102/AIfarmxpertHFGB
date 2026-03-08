import sys
import os
import asyncio
import json

# Add project root to path
sys.path.append(os.getcwd())

async def run_full_system_check():
    print("==================================================")
    print("      FARMXPERT FULL SYSTEM VERIFICATION FLOW     ")
    print("==================================================")

    # ---------------------------------------------------------
    # 1. CROP PLANNING (Market, Weather, Soil)
    # ---------------------------------------------------------
    print("\n[PHASE 1] CROP PLANNING")
    try:
        from farmxpert.tools.crop_planning.market_scraper import MarketScraperTool
        from farmxpert.tools.crop_planning.weather_client import WeatherClientTool
        from farmxpert.tools.crop_planning.soil_sensor import SoilSensorTool
        
        market = MarketScraperTool()
        weather = WeatherClientTool()
        soil = SoilSensorTool()
        
        print("   -> Checking Market Prices (Wheat/Gujarat)...")
        prices = market.fetch_market_prices("Wheat", "Gujarat")
        print(f"      Item 1: {prices[0] if prices else 'No Data'}")
        
        print("   -> Checking Weather Forecast (Amreli)...")
        forecast = weather.get_forecast("Amreli")
        print(f"      Condition: {forecast.get('list', [{}])[0].get('weather', [{}])[0].get('description', 'Unknown')}")
        
        print("   -> Reading Soil Sensors (Field A)...")
        readings = soil.get_realtime_data("sensor_A")
        print(f"      Moisture: {readings.get('moisture_percent')}% | pH: {readings.get('ph_level')}")
        
    except Exception as e:
        print(f"   [FAILED] Phase 1: {e}")

    # ---------------------------------------------------------
    # 2. FARM OPERATIONS (Task Optimization, Machinery)
    # ---------------------------------------------------------
    print("\n[PHASE 2] FARM OPERATIONS")
    try:
        from farmxpert.tools.operations.task_optimizer import TaskOptimizerTool
        from farmxpert.tools.operations.machinery_tracker import MachineryTrackerTool
        
        optimizer = TaskOptimizerTool()
        tracker = MachineryTrackerTool()
        
        tasks = [
            {"id": "t1", "title": "Sowing", "priority": "high", "estimated_hours": 8},
            {"id": "t2", "title": "Fencing Repair", "priority": "low", "estimated_hours": 4}
        ]
        
        print("   -> Optimizing Task Schedule...")
        schedule = optimizer.optimize_schedule(tasks)
        print(f"      Optimized Order: {[t['title'] for t in schedule.get('optimized_schedule', [])]}")
        
        print("   -> Checking Machinery Alerts...")
        alerts = tracker.get_maintenance_alerts(farm_id=1)
        print(f"      Active Alerts: {len(alerts)}")
        
    except Exception as e:
        print(f"   [FAILED] Phase 2: {e}")

    # ---------------------------------------------------------
    # 3. ANALYTICS (Yield Prediction)
    # ---------------------------------------------------------
    print("\n[PHASE 3] ANALYTICS")
    try:
        from farmxpert.tools.analytics.yield_engine import YieldEngineTool
        
        yield_engine = YieldEngineTool()
        
        print("   -> Predicting Yield (Wheat, 5 acres)...")
        inputs = {
            "soil_data": {"ph": 7.0, "organic_matter": 2.0},
            "weather_data": {"rain_risk": "low"}
        }
        prediction = yield_engine.predict_yield("Wheat", 5.0, inputs)
        print(f"      Prediction: {prediction.get('predicted_yield_tons')} tons (Conf: {prediction.get('confidence_score')})")
        
    except Exception as e:
        print(f"   [FAILED] Phase 3: {e}")

    # ---------------------------------------------------------
    # 4. SUPPLY CHAIN (Logistics)
    # ---------------------------------------------------------
    print("\n[PHASE 4] SUPPLY CHAIN")
    try:
        from farmxpert.tools.supply_chain.logistics_manager import LogisticsManagerTool
        
        logistics = LogisticsManagerTool()
        farm_loc = (21.5, 71.0) # Approx Amreli
        
        print("   -> Finding Storage & Calculating Route...")
        storages = logistics.find_nearest_storage(farm_loc)
        if storages:
            nearest = storages[0]
            route = logistics.calculate_route(farm_loc, (nearest["lat"], nearest["lon"]))
            print(f"      Nearest: {nearest['name']} ({nearest['distance_km']} km)")
            print(f"      Est Transport Cost: ₹{route.get('estimated_cost_inr')}")
        else:
            print("      No storage found nearby.")
            
    except Exception as e:
        print(f"   [FAILED] Phase 4: {e}")

    # ---------------------------------------------------------
    # 5. SUPPORT (Community)
    # ---------------------------------------------------------
    print("\n[PHASE 5] SUPPORT & COMMUNITY")
    try:
        from farmxpert.tools.support.community_forum import CommunityForumTool
        
        forum = CommunityForumTool()
        
        print("   -> Fetching Trending Topics...")
        trends = forum.get_trending_topics()
        print(f"      Top Topic: {trends[0]['title'] if trends else 'None'}")
        
        print("   -> Searching Solved Issues ('yellow leaf')...")
        issues = forum.search_similar_issues("yellow leaf")
        print(f"      Found similar: {issues[0]['question'] if issues else 'None'}")
        
    except Exception as e:
        print(f"   [FAILED] Phase 5: {e}")

    print("\n==================================================")
    print("      SYSTEM VERIFICATION COMPLETE                ")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_full_system_check())
