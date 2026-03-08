"""
Centralized Tools - All API Calls and External Data Sources
No magic, no complex inheritance - just straightforward functions.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

from farmxpert.config.settings import settings
from farmxpert.services.gemini_service import gemini_service

# ============================================================================
# LOCATION & GEOGRAPHY TOOLS
# ============================================================================

def get_location_coordinates(location: str) -> Dict[str, Any]:
    """
    Get coordinates for a location string
    
    Args:
        location: Location name (city, state, or address)
        
    Returns:
        Dictionary with lat, lon, and formatted address
    """
    # For now, return common Indian agricultural locations
    # In production, integrate with Google Geocoding API
    
    location_map = {
        "punjab": {"lat": 30.7333, "lon": 76.7794, "state": "Punjab"},
        "maharashtra": {"lat": 19.0760, "lon": 72.8777, "state": "Maharashtra"},
        "delhi": {"lat": 28.6139, "lon": 77.2090, "state": "Delhi"},
        "gujarat": {"lat": 23.2156, "lon": 72.6369, "state": "Gujarat"},
        "uttar pradesh": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh"},
        "karnataka": {"lat": 15.3173, "lon": 75.7139, "state": "Karnataka"},
        "tamil nadu": {"lat": 11.1271, "lon": 78.6569, "state": "Tamil Nadu"},
        "rajasthan": {"lat": 27.0238, "lon": 74.2179, "state": "Rajasthan"},
        "west bengal": {"lat": 22.9868, "lon": 87.8550, "state": "West Bengal"},
        "madhya pradesh": {"lat": 22.9734, "lon": 78.6569, "state": "Madhya Pradesh"},
    }
    
    location_lower = location.lower().strip()
    
    # Direct match
    if location_lower in location_map:
        return location_map[location_lower]
    
    # Partial match
    for key, coords in location_map.items():
        if key in location_lower or location_lower in key:
            return coords
    
    # Default to central India if not found
    return {"lat": 20.5937, "lon": 78.9629, "state": "Unknown"}

def parse_location_string(location: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse location from string or dict format
    
    Args:
        location: Location as string or dict
        
    Returns:
        Standardized location dict with lat, lon, state, etc.
    """
    if isinstance(location, dict):
        # Already in dict format, just ensure required fields
        return {
            "lat": location.get("lat") or location.get("latitude"),
            "lon": location.get("lon") or location.get("longitude"),
            "state": location.get("state", "Unknown"),
            "district": location.get("district", ""),
            "city": location.get("city", ""),
            "address": location.get("address", "")
        }
    
    # String location - get coordinates
    coords = get_location_coordinates(location)
    return {
        "lat": coords["lat"],
        "lon": coords["lon"],
        "state": coords["state"],
        "district": "",
        "city": location,
        "address": location
    }

# ============================================================================
# WEATHER TOOLS
# ============================================================================

async def get_weather_forecast(location: str, days: int = 7) -> Dict[str, Any]:
    """
    Get weather forecast for a location
    
    Args:
        location: Location name
        days: Number of days to forecast
        
    Returns:
        Weather forecast data
    """
    coords = get_location_coordinates(location)
    
    # Try OpenWeatherMap API if key is available
    if settings.openweather_api_key:
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast"
            params = {
                "lat": coords["lat"],
                "lon": coords["lon"],
                "appid": settings.openweather_api_key,
                "units": "metric",
                "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return parse_openweather_response(data, location)
        except Exception as e:
            print(f"Weather API failed: {e}")
    
    # Fallback to Gemini-generated forecast
    return await generate_gemini_weather_forecast(location, days, coords)

def parse_openweather_response(data: Dict[str, Any], location: str) -> Dict[str, Any]:
    """Parse OpenWeatherMap API response"""
    forecasts = []
    
    for item in data.get("list", []):
        forecast = {
            "date": item.get("dt_txt"),
            "temperature": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "pressure": item["main"]["pressure"],
            "wind_speed": item["wind"]["speed"],
            "description": item["weather"][0]["description"],
            "rain": item.get("rain", {}).get("3h", 0)
        }
        forecasts.append(forecast)
    
    return {
        "location": location,
        "source": "OpenWeatherMap",
        "forecasts": forecasts,
        "current": {
            "temperature": data["list"][0]["main"]["temp"],
            "humidity": data["list"][0]["main"]["humidity"],
            "description": data["list"][0]["weather"][0]["description"]
        }
    }

async def generate_gemini_weather_forecast(location: str, days: int, coords: Dict[str, Any]) -> Dict[str, Any]:
    """Generate weather forecast using Gemini as fallback"""
    
    prompt = f"""
    Generate a realistic {days}-day weather forecast for {location}, {coords['state']}.
    
    Location coordinates: {coords['lat']}, {coords['lon']}
    Current date: {datetime.now().strftime('%Y-%m-%d')}
    
    Provide daily forecasts with:
    - Date
    - Temperature range (min/max in °C)
    - Humidity (%)
    - Rainfall chance (mm)
    - Wind speed (km/h)
    - Weather description
    - Agricultural impact
    
    Format as JSON with this structure:
    {{
        "location": "{location}",
        "source": "Gemini Generated",
        "forecasts": [
            {{
                "date": "YYYY-MM-DD",
                "temp_min": 20,
                "temp_max": 35,
                "humidity": 60,
                "rainfall": 2.5,
                "wind_speed": 10,
                "description": "Partly cloudy",
                "agricultural_impact": "Good conditions for field work"
            }}
        ]
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "weather_forecast"})
        # Try to parse as JSON, fallback to text if needed
        try:
            return json.loads(response)
        except:
            return {
                "location": location,
                "source": "Gemini Generated",
                "forecasts": [],
                "raw_response": response
            }
    except Exception as e:
        return {"error": f"Failed to generate weather forecast: {str(e)}"}

# ============================================================================
# MARKET & PRICING TOOLS
# ============================================================================

async def get_market_prices(commodity: str, location: str = "India") -> Dict[str, Any]:
    """
    Get market prices for agricultural commodities
    
    Args:
        commodity: Commodity name (wheat, rice, etc.)
        location: Location for market prices
        
    Returns:
        Market price data
    """
    # For now, use Gemini to simulate market data
    # In production, integrate with real market APIs like Agmarknet
    
    prompt = f"""
    Generate realistic market price data for {commodity} in {location}.
    
    Current date: {datetime.now().strftime('%Y-%m-%d')}
    
    Provide:
    - Current market price per quintal (₹)
    - Price trend (rising/falling/stable)
    - Best markets to sell
    - Price forecast for next month
    - Quality-based price variations
    
    Format as JSON:
    {{
        "commodity": "{commodity}",
        "location": "{location}",
        "current_price": 2200,
        "price_unit": "per quintal",
        "currency": "INR",
        "trend": "rising",
        "best_markets": ["Delhi", "Mumbai", "Chennai"],
        "price_forecast": 2400,
        "quality_variations": {{
            "A_grade": 2400,
            "B_grade": 2200,
            "C_grade": 1900
        }},
        "market_insights": "Prices expected to rise due to festival demand"
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "market_prices"})
        try:
            return json.loads(response)
        except:
            return {
                "commodity": commodity,
                "location": location,
                "raw_response": response
            }
    except Exception as e:
        return {"error": f"Failed to get market prices: {str(e)}"}

async def get_mandi_prices(state: str, commodity: str = None) -> Dict[str, Any]:
    """
    Get mandi (market) prices for a state
    
    Args:
        state: Indian state name
        commodity: Optional commodity filter
        
    Returns:
        Mandi price data
    """
    prompt = f"""
    Generate realistic mandi price data for {state}{f' for {commodity}' if commodity else ''}.
    
    Include major mandis in the state with current prices for key commodities.
    
    Format as JSON:
    {{
        "state": "{state}",
        "date": "{datetime.now().strftime('%Y-%m-%d')}",
        "mandis": [
            {{
                "name": "Mandi Name",
                "district": "District",
                "commodities": [
                    {{
                        "name": "Wheat",
                        "min_price": 2100,
                        "max_price": 2300,
                        "modal_price": 2200,
                        "arrival_tonnes": 150
                    }}
                ]
            }}
        ]
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "mandi_prices"})
        try:
            return json.loads(response)
        except:
            return {"state": state, "raw_response": response}
    except Exception as e:
        return {"error": f"Failed to get mandi prices: {str(e)}"}

# ============================================================================
# SOIL & CROP TOOLS
# ============================================================================

async def analyze_soil_data(soil_data: Dict[str, Any], location: str) -> Dict[str, Any]:
    """
    Analyze soil data and provide recommendations
    
    Args:
        soil_data: Soil test results and properties
        location: Farm location
        
    Returns:
        Soil analysis and recommendations
    """
    prompt = f"""
    Analyze this soil data for a farm in {location} and provide comprehensive recommendations:
    
    Soil Data: {json.dumps(soil_data, indent=2)}
    
    Provide:
    1. Soil health score (0-100)
    2. Nutrient analysis (NPK status)
    3. pH assessment and recommendations
    4. Organic matter status
    5. Suitable crops for this soil
    6. Fertilizer recommendations
    7. Soil improvement strategies
    
    Format as JSON:
    {{
        "soil_health_score": 75,
        "nutrient_analysis": {{
            "nitrogen": "deficient",
            "phosphorus": "adequate",
            "potassium": "sufficient"
        }},
        "ph_assessment": {{
            "current_ph": 6.2,
            "status": "slightly_acidic",
            "recommendation": "Apply lime if needed"
        }},
        "organic_matter": {{
            "percentage": 1.8,
            "status": "moderate",
            "recommendation": "Add organic compost"
        }},
        "suitable_crops": ["wheat", "maize", "pulses"],
        "fertilizer_recommendations": {{
            "nitrogen": "40 kg/acre",
            "phosphorus": "20 kg/acre",
            "potassium": "15 kg/acre"
        }},
        "improvement_strategies": ["green_manuring", "crop_rotation", "organic_farming"]
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "soil_analysis"})
        try:
            return json.loads(response)
        except:
            return {"soil_data": soil_data, "raw_response": response}
    except Exception as e:
        return {"error": f"Failed to analyze soil: {str(e)}"}

async def get_crop_recommendations(
    location: str, 
    season: str, 
    soil_type: str = "general",
    land_size: float = 1.0
) -> Dict[str, Any]:
    """
    Get crop recommendations based on location, season, and soil
    
    Args:
        location: Farm location
        season: Growing season (Kharif, Rabi, Zaid)
        soil_type: Type of soil
        land_size: Land size in acres
        
    Returns:
        Crop recommendations with details
    """
    coords = get_location_coordinates(location)
    
    prompt = f"""
    Provide crop recommendations for a farm in {location}, {coords['state']}.
    
    Details:
    - Season: {season}
    - Soil type: {soil_type}
    - Land size: {land_size} acres
    - Coordinates: {coords['lat']}, {coords['lon']}
    
    Provide:
    1. Top 5 recommended crops
    2. Yield expectations per acre
    3. Profitability analysis
    4. Market demand
    5. Growing requirements
    6. Risk factors
    
    Format as JSON:
    {{
        "location": "{location}",
        "season": "{season}",
        "recommended_crops": [
            {{
                "name": "Wheat",
                "variety": "HD-2967",
                "yield_expectation": "20-25 quintals/acre",
                "profitability": "high",
                "market_demand": "strong",
                "growing_period": "120-130 days",
                "water_requirement": "moderate",
                "risk_factors": ["frost", "rust"],
                "estimated_cost": "₹15,000/acre",
                "expected_revenue": "₹50,000/acre"
            }}
        ]
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "crop_recommendations"})
        try:
            return json.loads(response)
        except:
            return {"location": location, "season": season, "raw_response": response}
    except Exception as e:
        return {"error": f"Failed to get crop recommendations: {str(e)}"}

# ============================================================================
# FERTILIZER & IRRIGATION TOOLS
# ============================================================================

async def get_fertilizer_recommendations(
    crop: str, 
    soil_data: Dict[str, Any], 
    location: str
) -> Dict[str, Any]:
    """
    Get fertilizer recommendations for a specific crop
    
    Args:
        crop: Crop name
        soil_data: Soil test data
        location: Farm location
        
    Returns:
        Fertilizer recommendations
    """
    prompt = f"""
    Provide fertilizer recommendations for {crop} cultivation.
    
    Crop: {crop}
    Location: {location}
    Soil Data: {json.dumps(soil_data, indent=2)}
    
    Provide:
    1. NPK requirements per acre
    2. Specific fertilizer recommendations
    3. Application schedule
    4. Cost estimates
    5. Organic alternatives
    
    Format as JSON:
    {{
        "crop": "{crop}",
        "npk_requirements": {{
            "nitrogen": "60 kg/acre",
            "phosphorus": "30 kg/acre",
            "potassium": "20 kg/acre"
        }},
        "fertilizer_recommendations": [
            {{
                "fertilizer": "Urea",
                "quantity": "130 kg/acre",
                "application_time": "Basal + top dressing",
                "cost": "₹3,000"
            }}
        ],
        "application_schedule": ["Basal application", "First top dress", "Second top dress"],
        "total_cost": "₹8,000/acre",
        "organic_alternatives": ["vermicompost", "farmyard_manure", "green_manure"]
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "fertilizer_recommendations"})
        try:
            return json.loads(response)
        except:
            return {"crop": crop, "raw_response": response}
    except Exception as e:
        return {"error": f"Failed to get fertilizer recommendations: {str(e)}"}

async def get_irrigation_schedule(
    crop: str, 
    location: str, 
    season: str,
    soil_type: str = "medium"
) -> Dict[str, Any]:
    """
    Get irrigation schedule for a crop
    
    Args:
        crop: Crop name
        location: Farm location
        season: Growing season
        soil_type: Soil type for water retention
        
    Returns:
        Irrigation schedule and recommendations
    """
    prompt = f"""
    Provide irrigation schedule for {crop} cultivation in {location} during {season} season.
    
    Details:
    - Crop: {crop}
    - Location: {location}
    - Season: {season}
    - Soil type: {soil_type}
    
    Provide:
    1. Irrigation schedule (when and how much)
    2. Critical growth stages for irrigation
    3. Water requirement calculations
    4. Irrigation method recommendations
    5. Water conservation tips
    
    Format as JSON:
    {{
        "crop": "{crop}",
        "location": "{location}",
        "irrigation_schedule": [
            {{
                "stage": "Sowing",
                "days_after_sowing": 0,
                "water_depth": "30-40 mm",
                "method": "Flood irrigation"
            }}
        ],
        "total_water_requirement": "500-600 mm",
        "critical_stages": ["crown root initiation", "tillering", "flowering"],
        "recommended_method": "Drip irrigation",
        "conservation_tips": ["mulching", "overnight irrigation", "weed control"]
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "irrigation_schedule"})
        try:
            return json.loads(response)
        except:
            return {"crop": crop, "raw_response": response}
    except Exception as e:
        return {"error": f"Failed to get irrigation schedule: {str(e)}"}

# ============================================================================
# PEST & DISEASE TOOLS
# ============================================================================

async def diagnose_pest_disease(
    symptoms: str, 
    crop: str, 
    location: str
) -> Dict[str, Any]:
    """
    Diagnose pest and disease issues
    
    Args:
        symptoms: Description of symptoms
        crop: Affected crop
        location: Farm location
        
    Returns:
        Diagnosis and treatment recommendations
    """
    prompt = f"""
    Diagnose pest or disease issue based on symptoms.
    
    Crop: {crop}
    Location: {location}
    Symptoms: {symptoms}
    
    Provide:
    1. Likely diagnosis
    2. Cause identification
    3. Treatment recommendations
    4. Prevention measures
    5. Chemical and organic options
    
    Format as JSON:
    {{
        "crop": "{crop}",
        "symptoms": "{symptoms}",
        "diagnosis": "Leaf rust disease",
        "cause": "Fungal infection (Puccinia triticina)",
        "severity": "moderate",
        "treatment": {{
            "chemical": ["Propiconazole 25 EC @ 0.1%"],
            "organic": ["Neem oil spray", "Copper fungicide"],
            "application_method": "Foliar spray"
        }},
        "prevention": ["crop_rotation", "resistant_varieties", "proper_spacing"],
        "urgency": "treat_within_3_days"
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "pest_disease_diagnosis"})
        try:
            return json.loads(response)
        except:
            return {"crop": crop, "symptoms": symptoms, "raw_response": response}
    except Exception as e:
        return {"error": f"Failed to diagnose pest/disease: {str(e)}"}

# ============================================================================
# SCHEME & SUBSIDY TOOLS
# ============================================================================

async def get_government_schemes(
    state: str, 
    category: str = "all",
    farmer_type: str = "small"
) -> Dict[str, Any]:
    """
    Get government schemes and subsidies
    
    Args:
        state: Indian state
        category: Scheme category (seeds, equipment, insurance, etc.)
        farmer_type: Type of farmer (small, marginal, large)
        
    Returns:
        Available government schemes
    """
    prompt = f"""
    Provide information about government agricultural schemes for {state}.
    
    State: {state}
    Category: {category}
    Farmer type: {farmer_type}
    
    Provide:
    1. Relevant schemes
    2. Eligibility criteria
    3. Benefits and subsidies
    4. Application process
    5. Required documents
    
    Format as JSON:
    {{
        "state": "{state}",
        "schemes": [
            {{
                "name": "PM-Kisan Samman Nidhi",
                "category": "income_support",
                "benefit": "₹6,000 per year",
                "eligibility": "Small and marginal farmers",
                "application_process": "Online through PM-Kisan portal",
                "documents": ["Aadhaar", "land_records", "bank_account"],
                "contact": "Agriculture department"
            }}
        ]
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "government_schemes"})
        try:
            return json.loads(response)
        except:
            return {"state": state, "raw_response": response}
    except Exception as e:
        return {"error": f"Failed to get government schemes: {str(e)}"}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Perform web search for agricultural information
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        Search results
    """
    # For now, use Gemini to simulate web search
    # In production, integrate with real search APIs
    
    prompt = f"""
    Search for recent and relevant information about: {query}
    
    Provide {num_results} results with:
    1. Title
    2. Summary
    3. Source
    4. Date
    5. URL (if applicable)
    
    Focus on agricultural websites, government sources, and research institutions.
    
    Format as JSON:
    {{
        "query": "{query}",
        "results": [
            {{
                "title": "Result title",
                "summary": "Brief summary",
                "source": "Source name",
                "date": "2024-01-01",
                "url": "https://example.com"
            }}
        ]
    }}
    """
    
    try:
        response = await gemini_service.generate_response(prompt, {"task": "web_search"})
        try:
            return json.loads(response)
        except:
            return {"query": query, "raw_response": response}
    except Exception as e:
        return {"error": f"Failed to perform web search: {str(e)}"}

def format_currency(amount: float, currency: str = "INR") -> str:
    """Format currency amount"""
    if currency == "INR":
        return f"₹{amount:,.2f}"
    return f"{currency} {amount:,.2f}"

def calculate_profit_margin(
    revenue: float, 
    costs: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate profit margin and related metrics
    
    Args:
        revenue: Total revenue
        costs: Dictionary of cost items
        
    Returns:
        Profit analysis
    """
    total_costs = sum(costs.values())
    profit = revenue - total_costs
    profit_margin = (profit / revenue * 100) if revenue > 0 else 0
    
    return {
        "revenue": revenue,
        "total_costs": total_costs,
        "profit": profit,
        "profit_margin_percent": profit_margin,
        "roi_percent": (profit / total_costs * 100) if total_costs > 0 else 0,
        "break_even_revenue": total_costs
    }
