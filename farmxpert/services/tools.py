from __future__ import annotations
from typing import Dict, Any, List, Optional
import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from farmxpert.config.settings import settings
from farmxpert.services.gemini_service import gemini_service
from farmxpert.services.providers import MandiPriceProvider, SchemesProvider, WeatherProvider


_weather_provider = WeatherProvider()
_mandi_price_provider = MandiPriceProvider()
_schemes_provider = SchemesProvider()


class SoilTool:
    @staticmethod
    async def analyze_soil_with_gemini(soil_data: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Use Gemini to analyze soil data and provide recommendations"""
        prompt = f"""
        Analyze this soil data for a farm in {location} and provide comprehensive recommendations:
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        
        Please provide:
        1. Soil health assessment (0-100 score)
        2. Nutrient deficiencies and excesses
        3. Recommended crops for this soil type
        4. Fertilizer recommendations with specific amounts
        5. Soil improvement suggestions
        6. pH adjustment recommendations if needed
        7. Organic matter improvement strategies
        
        Format your response as a JSON object with these keys:
        - soil_health_score
        - nutrient_analysis
        - suitable_crops
        - fertilizer_recommendations
        - soil_improvements
        - ph_adjustments
        - organic_matter_strategies
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "soil_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze soil: {str(e)}"}
    
    @staticmethod
    async def search_soil_best_practices(crop: str, region: str) -> Dict[str, Any]:
        """Search for soil best practices for specific crop and region"""
        search_query = f"soil preparation best practices {crop} farming {region} India"
        
        try:
            # Use web search to get current best practices
            async with aiohttp.ClientSession() as session:
                # This would integrate with a real search API
                # For now, we'll use Gemini to simulate web search results
                prompt = f"""
                Based on current agricultural research and best practices, provide soil preparation guidelines for {crop} cultivation in {region}, India.
                
                Include:
                1. Soil preparation techniques
                2. Timing for soil preparation
                3. Equipment recommendations
                4. Common mistakes to avoid
                5. Regional specific considerations
                
                Format as JSON with keys: preparation_techniques, timing, equipment, common_mistakes, regional_considerations
                """
                
                response = await gemini_service.generate_response(prompt, {"task": "soil_best_practices"})
                return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to search soil practices: {str(e)}"}


class WeatherTool:
    @staticmethod
    async def get_weather_forecast(location: str, days: int = 7) -> Dict[str, Any]:
        """Get weather forecast.

        Preferred: OpenWeather via WeatherProvider (cached).
        Fallback: Gemini-generated forecast.
        """
        provider_result: Dict[str, Any] | None = None
        try:
            provider_result = await _weather_provider.get_weather_bundle(location, days=days)
            if provider_result.get("success"):
                forecast = (provider_result.get("forecast") or {}).get("data") or {}
                daily = forecast.get("daily")
                alerts = forecast.get("alerts")

                daily_list = daily if isinstance(daily, list) else []
                alerts_dict = alerts if isinstance(alerts, dict) else {}

                return {
                    "location": provider_result.get("location"),
                    "forecast_days": days,
                    "daily_forecast": daily_list,
                    "agricultural_impact": {
                        "alerts": alerts_dict,
                    },
                    "farming_recommendations": [
                        a.get("advice")
                        for a in [
                            (alerts_dict.get("heat_stress") or {}),
                            (alerts_dict.get("dry_spell") or {}),
                        ]
                        if a.get("advice")
                    ],
                    "sources": provider_result.get("sources"),
                    "fetched_at": provider_result.get("fetched_at"),
                    "provider": "WeatherProvider",
                    "raw_provider": provider_result,
                }
        except Exception as e:
            # Do not swallow provider errors silently; fall back but keep the error for visibility.
            provider_result = {
                "success": False,
                "error": f"WeatherProvider exception: {e}",
            }

        try:
            prompt = f"""
            Provide current weather forecast for {location}, India for the next {days} days.
            
            Include:
            1. Temperature (min/max)
            2. Humidity levels
            3. Precipitation probability
            4. Wind speed and direction
            5. Weather conditions
            6. Agricultural impact assessment
            7. Farming recommendations based on weather
            
            Format as JSON with keys: location, forecast_days, daily_forecast, agricultural_impact, farming_recommendations
            """
            response = await gemini_service.generate_response(prompt, {"task": "weather_forecast"})
            parsed = gemini_service._parse_json_response(response) or {}
            daily = parsed.get("daily_forecast")
            impact = parsed.get("agricultural_impact")
            alerts = (impact or {}).get("alerts") if isinstance(impact, dict) else None

            daily_list = daily if isinstance(daily, list) else []
            alerts_dict = alerts if isinstance(alerts, dict) else {}

            # Normalize shape for UI consumers
            parsed["location"] = parsed.get("location") or location
            parsed["forecast_days"] = parsed.get("forecast_days") or days
            parsed["daily_forecast"] = daily_list
            parsed["agricultural_impact"] = {"alerts": alerts_dict}
            parsed["provider"] = parsed.get("provider") or "Gemini"
            if provider_result and not provider_result.get("success"):
                parsed["provider_error"] = provider_result.get("error")
                parsed["raw_provider"] = provider_result

            return parsed
        except Exception as e:
            return {
                "error": f"Failed to get weather forecast: {str(e)}",
                "provider": "Gemini",
                "provider_error": (provider_result or {}).get("error"),
                "raw_provider": provider_result,
                "location": location,
                "forecast_days": days,
                "daily_forecast": [],
                "agricultural_impact": {"alerts": {}},
                "farming_recommendations": [],
            }
    
    @staticmethod
    async def analyze_weather_impact(crop: str, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze weather impact on specific crops"""
        prompt = f"""
        Analyze the impact of this weather data on {crop} cultivation:
        
        Weather Data: {json.dumps(weather_data, indent=2)}
        
        Provide:
        1. Risk assessment for the crop
        2. Recommended protective measures
        3. Irrigation adjustments needed
        4. Pest/disease risk due to weather
        5. Harvest timing considerations
        6. Emergency actions if severe weather
        
        Format as JSON with keys: risk_assessment, protective_measures, irrigation_adjustments, pest_disease_risk, harvest_considerations, emergency_actions
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "weather_impact_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze weather impact: {str(e)}"}
    
    @staticmethod
    async def get_seasonal_advice(region: str, current_month: int) -> Dict[str, Any]:
        """Get seasonal farming advice based on region and time"""
        season_map = {1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "summer", 6: "summer",
                     7: "monsoon", 8: "monsoon", 9: "monsoon", 10: "autumn", 11: "autumn", 12: "winter"}
        
        current_season = season_map.get(current_month, "unknown")
        
        prompt = f"""
        Provide seasonal farming advice for {region}, India during {current_season} (month {current_month}).
        
        Include:
        1. Recommended crops for this season
        2. Soil preparation activities
        3. Irrigation requirements
        4. Pest and disease management
        5. Harvest and post-harvest activities
        6. Market opportunities
        7. Common challenges and solutions
        
        Format as JSON with keys: recommended_crops, soil_preparation, irrigation_needs, pest_management, harvest_activities, market_opportunities, challenges_solutions
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "seasonal_advice"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get seasonal advice: {str(e)}"}


class MarketTool:
    @staticmethod
    async def get_current_prices(crop: str, region: str) -> Dict[str, Any]:
        """Get current market prices using web search and Gemini analysis"""
        prompt = f"""
        Provide current market prices and trends for {crop} in {region}, India.
        
        Include:
        1. Current market price per quintal/kg
        2. Price trend (rising/falling/stable)
        3. Comparison with previous month/year
        4. Regional price variations
        5. Best selling locations/mandis
        6. Quality specifications affecting price
        7. Market demand level
        
        Format as JSON with keys: current_price, price_trend, price_comparison, regional_variations, best_locations, quality_specs, demand_level
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "market_prices"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get market prices: {str(e)}"}
    
    @staticmethod
    async def analyze_market_opportunities(crop: str, region: str) -> Dict[str, Any]:
        """Analyze market opportunities and timing"""
        prompt = f"""
        Analyze market opportunities for {crop} cultivation in {region}, India.
        
        Include:
        1. Best time to sell (seasonal patterns)
        2. Export opportunities
        3. Value-added product possibilities
        4. Government schemes and support
        5. Market risks and mitigation
        6. Profitability analysis
        7. Alternative markets
        
        Format as JSON with keys: best_selling_time, export_opportunities, value_added_products, government_schemes, market_risks, profitability_analysis, alternative_markets
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "market_opportunities"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze market opportunities: {str(e)}"}
    
    @staticmethod
    async def get_supply_chain_info(crop: str, region: str) -> Dict[str, Any]:
        """Get supply chain and logistics information"""
        prompt = f"""
        Provide supply chain and logistics information for {crop} from {region}, India.
        
        Include:
        1. Major mandis and markets
        2. Transportation options and costs
        3. Storage facilities and requirements
        4. Processing units nearby
        5. Quality standards and certifications
        6. Packaging requirements
        7. Logistics best practices
        
        Format as JSON with keys: major_mandis, transportation_options, storage_facilities, processing_units, quality_standards, packaging_requirements, logistics_best_practices
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "supply_chain_info"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get supply chain info: {str(e)}"}


class CropTool:
    """Tools for crop-related operations using Gemini for dynamic analysis"""
    
    @staticmethod
    async def get_crop_recommendations(soil_data: Dict[str, Any], location: str, season: str) -> Dict[str, Any]:
        """Get crop recommendations based on soil, location, and season"""
        prompt = f"""
        Based on the following conditions, recommend the best crops for cultivation in {location}, India during {season} season:
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Location: {location}
        Season: {season}
        
        Provide:
        1. Top 5 recommended crops with reasons
        2. Expected yield for each crop
        3. Market demand and profitability
        4. Input requirements and costs
        5. Risk factors and mitigation
        6. Cultivation timeline
        7. Success probability for each crop
        
        Format as JSON with keys: recommended_crops, expected_yields, market_analysis, input_requirements, risk_factors, cultivation_timeline, success_probability
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "crop_recommendations"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get crop recommendations: {str(e)}"}
    
    @staticmethod
    async def get_crop_cultivation_guide(crop: str, region: str) -> Dict[str, Any]:
        """Get comprehensive cultivation guide for a specific crop"""
        prompt = f"""
        Provide a comprehensive cultivation guide for {crop} in {region}, India.
        
        Include:
        1. Land preparation requirements
        2. Seed selection and treatment
        3. Sowing/planting methods and timing
        4. Irrigation schedule and water management
        5. Fertilizer application schedule
        6. Pest and disease management
        7. Weed control strategies
        8. Harvest timing and methods
        9. Post-harvest handling
        10. Common problems and solutions
        
        Format as JSON with keys: land_preparation, seed_selection, sowing_methods, irrigation_schedule, fertilizer_schedule, pest_management, weed_control, harvest_guide, post_harvest, problem_solutions
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "cultivation_guide"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get cultivation guide: {str(e)}"}
    
    @staticmethod
    async def analyze_crop_problems(symptoms: List[str], crop: str, growth_stage: str) -> Dict[str, Any]:
        """Analyze crop problems based on symptoms"""
        prompt = f"""
        Analyze these symptoms observed in {crop} during {growth_stage} stage:
        
        Symptoms: {', '.join(symptoms)}
        Crop: {crop}
        Growth Stage: {growth_stage}
        
        Provide:
        1. Likely causes (pests, diseases, nutrient deficiencies, environmental)
        2. Severity assessment
        3. Immediate treatment recommendations
        4. Preventive measures
        5. Long-term management strategies
        6. When to consult experts
        7. Economic impact assessment
        
        Format as JSON with keys: likely_causes, severity_assessment, immediate_treatment, preventive_measures, long_term_strategies, expert_consultation, economic_impact
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "crop_problem_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze crop problems: {str(e)}"}


class FertilizerTool:
    """Tools for fertilizer recommendations using Gemini for dynamic analysis"""
    
    @staticmethod
    async def get_fertilizer_recommendations(soil_data: Dict[str, Any], crop: str, area_acres: float, region: str) -> Dict[str, Any]:
        """Get comprehensive fertilizer recommendations"""
        prompt = f"""
        Provide detailed fertilizer recommendations for {crop} cultivation on {area_acres} acres in {region}, India.
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Crop: {crop}
        Area: {area_acres} acres
        Region: {region}
        
        Include:
        1. Nutrient deficiency analysis
        2. Specific fertilizer recommendations with quantities
        3. Application schedule and timing
        4. Organic fertilizer alternatives
        5. Cost analysis and budget planning
        6. Soil health improvement strategies
        7. Environmental considerations
        8. Regional fertilizer availability and prices
        
        Format as JSON with keys: nutrient_analysis, fertilizer_recommendations, application_schedule, organic_alternatives, cost_analysis, soil_health_strategies, environmental_considerations, regional_availability
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fertilizer_recommendations"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get fertilizer recommendations: {str(e)}"}
    
    @staticmethod
    async def get_organic_farming_guide(crop: str, region: str) -> Dict[str, Any]:
        """Get organic farming guide and alternatives"""
        prompt = f"""
        Provide a comprehensive organic farming guide for {crop} cultivation in {region}, India.
        
        Include:
        1. Organic fertilizer options and sources
        2. Composting techniques and recipes
        3. Bio-fertilizer recommendations
        4. Green manure crops
        5. Organic pest control methods
        6. Soil health improvement through organic practices
        7. Certification requirements
        8. Market opportunities for organic produce
        9. Cost comparison with conventional farming
        10. Transition strategies from conventional to organic
        
        Format as JSON with keys: organic_fertilizers, composting_guide, bio_fertilizers, green_manure, pest_control, soil_health, certification, market_opportunities, cost_comparison, transition_strategies
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "organic_farming_guide"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get organic farming guide: {str(e)}"}


class PestDiseaseTool:
    """Tools for pest and disease management using Gemini for dynamic analysis"""
    
    @staticmethod
    async def diagnose_pest_disease(symptoms: List[str], crop: str, region: str, growth_stage: str) -> Dict[str, Any]:
        """Diagnose pest or disease based on symptoms using AI analysis"""
        prompt = f"""
        Diagnose the pest or disease affecting {crop} in {region}, India based on these symptoms:
        
        Symptoms: {', '.join(symptoms)}
        Crop: {crop}
        Region: {region}
        Growth Stage: {growth_stage}
        
        Provide:
        1. Most likely pest/disease identification
        2. Severity assessment (low/medium/high)
        3. Contributing factors
        4. Immediate treatment recommendations
        5. Organic treatment options
        6. Chemical treatment options (if necessary)
        7. Prevention strategies
        8. Economic threshold for treatment
        9. When to seek expert help
        10. Long-term management plan
        
        Format as JSON with keys: diagnosis, severity, contributing_factors, immediate_treatment, organic_treatments, chemical_treatments, prevention_strategies, economic_threshold, expert_consultation, long_term_management
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "pest_disease_diagnosis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to diagnose pest/disease: {str(e)}"}
    
    @staticmethod
    async def get_integrated_pest_management(crop: str, region: str) -> Dict[str, Any]:
        """Get integrated pest management strategies"""
        prompt = f"""
        Provide comprehensive Integrated Pest Management (IPM) strategies for {crop} cultivation in {region}, India.
        
        Include:
        1. Common pests and diseases for this crop/region
        2. Cultural control methods
        3. Biological control options
        4. Mechanical control techniques
        5. Chemical control as last resort
        6. Monitoring and scouting techniques
        7. Economic injury levels
        8. Seasonal pest calendar
        9. Resistant variety recommendations
        10. Beneficial insect promotion
        
        Format as JSON with keys: common_pests_diseases, cultural_controls, biological_controls, mechanical_controls, chemical_controls, monitoring_techniques, economic_levels, seasonal_calendar, resistant_varieties, beneficial_insects
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "integrated_pest_management"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get IPM strategies: {str(e)}"}


class IrrigationTool:
    """Tools for irrigation planning using Gemini for dynamic analysis"""
    
    @staticmethod
    async def get_irrigation_planning(crop: str, soil_data: Dict[str, Any], weather_data: Dict[str, Any], region: str) -> Dict[str, Any]:
        """Get comprehensive irrigation planning"""
        prompt = f"""
        Provide detailed irrigation planning for {crop} cultivation in {region}, India.
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Weather Data: {json.dumps(weather_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Include:
        1. Water requirement analysis
        2. Irrigation schedule and timing
        3. Irrigation methods recommendations
        4. Water conservation strategies
        5. Drought management techniques
        6. Water quality considerations
        7. Cost analysis of irrigation systems
        8. Government schemes for irrigation
        9. Technology options (drip, sprinkler, etc.)
        10. Monitoring and maintenance
        
        Format as JSON with keys: water_requirements, irrigation_schedule, irrigation_methods, water_conservation, drought_management, water_quality, cost_analysis, government_schemes, technology_options, monitoring_maintenance
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "irrigation_planning"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get irrigation planning: {str(e)}"}
    
    @staticmethod
    async def get_water_management_strategies(region: str, season: str) -> Dict[str, Any]:
        """Get water management strategies for region and season"""
        prompt = f"""
        Provide water management strategies for farming in {region}, India during {season} season.
        
        Include:
        1. Water availability assessment
        2. Rainwater harvesting techniques
        3. Water storage solutions
        4. Efficient irrigation practices
        5. Water recycling methods
        6. Drought-resistant crop options
        7. Government water schemes
        8. Community water management
        9. Technology for water conservation
        10. Cost-effective water solutions
        
        Format as JSON with keys: water_availability, rainwater_harvesting, water_storage, efficient_irrigation, water_recycling, drought_resistant_crops, government_schemes, community_management, conservation_technology, cost_effective_solutions
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "water_management_strategies"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get water management strategies: {str(e)}"}


class WebScrapingTool:
    """Tools for web scraping market data and trends"""
    
    @staticmethod
    async def scrape_market_data(crop: str, region: str) -> Dict[str, Any]:
        """Scrape market data for specific crop and region"""
        prompt = f"""
        Based on current agricultural market trends and data, provide comprehensive market information for {crop} in {region}, India.
        
        Include:
        1. Current market prices per quintal/kg
        2. Price trends over the last 3 months
        3. Demand levels and market sentiment
        4. Major mandis and trading centers
        5. Quality specifications affecting prices
        6. Seasonal price patterns
        7. Export opportunities and prices
        8. Government procurement prices (MSP)
        9. Market volatility indicators
        10. Best selling locations and timing
        
        Format as JSON with keys: current_prices, price_trends, demand_levels, major_mandis, quality_specs, seasonal_patterns, export_opportunities, government_prices, volatility_indicators, best_locations
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "market_data_scraping"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to scrape market data: {str(e)}"}
    
    @staticmethod
    async def scrape_crop_trends(crop: str, region: str) -> Dict[str, Any]:
        """Scrape crop demand and trend data"""
        prompt = f"""
        Provide current crop demand and trend analysis for {crop} in {region}, India.
        
        Include:
        1. Current demand levels (high/medium/low)
        2. Demand growth trends
        3. Consumer preferences and market shifts
        4. Processing industry demand
        5. Export market trends
        6. Seasonal demand patterns
        7. Competitive crop analysis
        8. Market opportunities
        9. Risk factors affecting demand
        10. Future demand projections
        
        Format as JSON with keys: current_demand, demand_growth, consumer_preferences, processing_demand, export_trends, seasonal_patterns, competitive_analysis, market_opportunities, risk_factors, future_projections
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "crop_trends_scraping"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to scrape crop trends: {str(e)}"}


class ClimatePredictionTool:
    """Tools for climate prediction and weather analysis"""
    
    @staticmethod
    async def predict_climate_conditions(location: str, season: str, days: int = 30) -> Dict[str, Any]:
        """Predict climate conditions for crop planning"""
        prompt = f"""
        Provide detailed climate prediction for {location}, India during {season} season for the next {days} days.
        
        Include:
        1. Temperature predictions (min/max/average)
        2. Rainfall probability and amounts
        3. Humidity levels
        4. Wind patterns and speed
        5. Extreme weather risk assessment
        6. Climate impact on agriculture
        7. Best planting windows
        8. Risk mitigation strategies
        9. Historical climate comparison
        10. Long-term climate trends
        
        Format as JSON with keys: temperature_predictions, rainfall_forecast, humidity_levels, wind_patterns, extreme_weather_risks, agricultural_impact, planting_windows, risk_mitigation, historical_comparison, long_term_trends
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "climate_prediction"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to predict climate conditions: {str(e)}"}
    
    @staticmethod
    async def analyze_climate_impact_on_crops(crop: str, location: str, climate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze climate impact on specific crops"""
        prompt = f"""
        Analyze the impact of climate conditions on {crop} cultivation in {location}, India.
        
        Climate Data: {json.dumps(climate_data, indent=2)}
        Crop: {crop}
        Location: {location}
        
        Provide:
        1. Climate suitability assessment
        2. Growth stage impacts
        3. Yield potential under current conditions
        4. Risk factors and mitigation strategies
        5. Optimal planting timing
        6. Water requirement adjustments
        7. Pest and disease risk due to climate
        8. Harvest timing considerations
        9. Climate adaptation strategies
        10. Alternative crop recommendations if needed
        
        Format as JSON with keys: climate_suitability, growth_impacts, yield_potential, risk_factors, optimal_timing, water_adjustments, pest_disease_risks, harvest_considerations, adaptation_strategies, alternative_crops
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "climate_crop_impact"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze climate impact: {str(e)}"}


class MarketAnalysisTool:
    """Tools for comprehensive market analysis"""
    
    @staticmethod
    async def analyze_historical_prices(crop: str, region: str, period: str = "1_year") -> Dict[str, Any]:
        """Analyze historical crop prices and trends"""
        prompt = f"""
        Provide comprehensive historical price analysis for {crop} in {region}, India over the last {period}.
        
        Include:
        1. Price trends and patterns
        2. Seasonal price variations
        3. Price volatility analysis
        4. Peak and low price periods
        5. Factors affecting price changes
        6. Price correlation with other crops
        7. Market cycle analysis
        8. Price forecasting indicators
        9. Risk assessment for price fluctuations
        10. Optimal selling periods
        
        Format as JSON with keys: price_trends, seasonal_variations, volatility_analysis, peak_periods, price_factors, correlation_analysis, market_cycles, forecasting_indicators, risk_assessment, optimal_selling_periods
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "historical_price_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze historical prices: {str(e)}"}
    
    @staticmethod
    async def predict_future_demand(crop: str, region: str) -> Dict[str, Any]:
        """Predict future market demand for crops"""
        prompt = f"""
        Predict future market demand for {crop} in {region}, India.
        
        Include:
        1. Demand growth projections
        2. Market size estimates
        3. Consumer trend analysis
        4. Processing industry growth
        5. Export market potential
        6. Competitive landscape changes
        7. Technology impact on demand
        8. Government policy influences
        9. Economic factors affecting demand
        10. Risk factors and uncertainties
        
        Format as JSON with keys: demand_projections, market_size, consumer_trends, processing_growth, export_potential, competitive_changes, technology_impact, policy_influences, economic_factors, risk_factors
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "future_demand_prediction"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to predict future demand: {str(e)}"}


class GeneticDatabaseTool:
    """Tools for genetic database queries and seed variety analysis"""
    
    @staticmethod
    async def query_seed_varieties(crop: str, region: str) -> Dict[str, Any]:
        """Query seed varieties and their characteristics"""
        prompt = f"""
        Provide comprehensive information about seed varieties available for {crop} cultivation in {region}, India.
        
        Include:
        1. Popular varieties (GMO, hybrid, traditional)
        2. Yield potential for each variety
        3. Disease resistance traits
        4. Climate adaptability
        5. Soil type preferences
        6. Maturity period
        7. Water requirements
        8. Quality characteristics
        9. Market preferences
        10. Cost and availability
        
        Format as JSON with keys: popular_varieties, yield_potential, disease_resistance, climate_adaptability, soil_preferences, maturity_period, water_requirements, quality_characteristics, market_preferences, cost_availability
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "seed_variety_query"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to query seed varieties: {str(e)}"}
    
    @staticmethod
    async def analyze_seed_traits(crop: str, variety: str, region: str) -> Dict[str, Any]:
        """Analyze specific seed variety traits and characteristics"""
        prompt = f"""
        Provide detailed analysis of {variety} variety of {crop} for cultivation in {region}, India.
        
        Include:
        1. Genetic characteristics and traits
        2. Yield potential and performance
        3. Disease and pest resistance
        4. Environmental stress tolerance
        5. Nutritional quality
        6. Market acceptance
        7. Cultivation requirements
        8. Harvest and post-harvest characteristics
        9. Comparison with other varieties
        10. Recommendations for specific conditions
        
        Format as JSON with keys: genetic_traits, yield_performance, resistance_traits, stress_tolerance, nutritional_quality, market_acceptance, cultivation_requirements, harvest_characteristics, variety_comparison, specific_recommendations
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "seed_trait_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze seed traits: {str(e)}"}


class SoilSuitabilityTool:
    """Tools for soil suitability assessment for seed varieties"""
    
    @staticmethod
    async def assess_soil_suitability(soil_data: Dict[str, Any], crop: str, variety: str) -> Dict[str, Any]:
        """Assess soil suitability for specific crop variety"""
        prompt = f"""
        Assess soil suitability for {variety} variety of {crop} based on the provided soil data.
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Crop: {crop}
        Variety: {variety}
        
        Provide:
        1. Overall soil suitability score (0-100)
        2. Nutrient availability assessment
        3. pH compatibility
        4. Drainage requirements
        5. Soil amendment recommendations
        6. Root development potential
        7. Water retention capacity
        8. Microbial activity indicators
        9. Potential challenges
        10. Optimization strategies
        
        Format as JSON with keys: suitability_score, nutrient_availability, ph_compatibility, drainage_requirements, amendment_recommendations, root_development, water_retention, microbial_activity, potential_challenges, optimization_strategies
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "soil_suitability_assessment"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to assess soil suitability: {str(e)}"}
    
    @staticmethod
    async def recommend_soil_improvements(soil_data: Dict[str, Any], crop: str, target_yield: float) -> Dict[str, Any]:
        """Recommend soil improvements for target yield"""
        prompt = f"""
        Recommend soil improvements for {crop} cultivation to achieve target yield of {target_yield} quintals per acre.
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Crop: {crop}
        Target Yield: {target_yield} quintals/acre
        
        Include:
        1. Current soil limitations
        2. Required soil amendments
        3. Fertilizer recommendations
        4. Organic matter improvements
        5. pH adjustment needs
        6. Drainage improvements
        7. Soil structure enhancements
        8. Implementation timeline
        9. Cost estimates
        10. Expected yield improvement
        
        Format as JSON with keys: soil_limitations, required_amendments, fertilizer_recommendations, organic_improvements, ph_adjustments, drainage_improvements, structure_enhancements, implementation_timeline, cost_estimates, yield_improvement
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "soil_improvement_recommendations"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to recommend soil improvements: {str(e)}"}


class YieldPredictionTool:
    """Tools for yield prediction based on various factors"""
    
    @staticmethod
    async def predict_crop_yield(crop: str, variety: str, soil_data: Dict[str, Any], weather_data: Dict[str, Any], region: str) -> Dict[str, Any]:
        """Predict crop yield based on multiple factors"""
        prompt = f"""
        Predict the expected yield for {variety} variety of {crop} in {region}, India.
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Weather Data: {json.dumps(weather_data, indent=2)}
        Crop: {crop}
        Variety: {variety}
        Region: {region}
        
        Provide:
        1. Expected yield range (min-max)
        2. Most likely yield estimate
        3. Yield influencing factors
        4. Risk factors affecting yield
        5. Optimal growing conditions
        6. Yield optimization strategies
        7. Seasonal yield variations
        8. Comparison with regional averages
        9. Economic yield potential
        10. Yield monitoring recommendations
        
        Format as JSON with keys: yield_range, likely_yield, influencing_factors, risk_factors, optimal_conditions, optimization_strategies, seasonal_variations, regional_comparison, economic_potential, monitoring_recommendations
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "yield_prediction"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to predict crop yield: {str(e)}"}
    
    @staticmethod
    async def analyze_yield_factors(crop: str, variety: str, region: str) -> Dict[str, Any]:
        """Analyze factors that influence crop yield"""
        prompt = f"""
        Analyze the key factors that influence yield for {variety} variety of {crop} in {region}, India.
        
        Include:
        1. Genetic potential factors
        2. Environmental factors
        3. Management factors
        4. Soil-related factors
        5. Climate-related factors
        6. Pest and disease factors
        7. Water management factors
        8. Nutrient management factors
        9. Technology adoption factors
        10. Market and economic factors
        
        Format as JSON with keys: genetic_factors, environmental_factors, management_factors, soil_factors, climate_factors, pest_disease_factors, water_factors, nutrient_factors, technology_factors, market_factors
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "yield_factor_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze yield factors: {str(e)}"}


class SoilSensorTool:
    """Tools for soil sensor data integration and analysis"""
    
    @staticmethod
    async def integrate_sensor_data(sensor_data: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Integrate and analyze soil sensor data"""
        prompt = f"""
        Analyze and integrate soil sensor data for a farm in {location}, India.
        
        Sensor Data: {json.dumps(sensor_data, indent=2)}
        Location: {location}
        
        Provide:
        1. Real-time soil health assessment
        2. Nutrient levels analysis (NPK)
        3. pH level interpretation
        4. Moisture content analysis
        5. Temperature impact assessment
        6. Organic matter indicators
        7. Soil compaction analysis
        8. Microbial activity indicators
        9. Immediate action recommendations
        10. Long-term monitoring suggestions
        
        Format as JSON with keys: health_assessment, nutrient_analysis, ph_interpretation, moisture_analysis, temperature_impact, organic_matter, compaction_analysis, microbial_activity, immediate_actions, monitoring_suggestions
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "sensor_data_integration"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to integrate sensor data: {str(e)}"}
    
    @staticmethod
    async def get_sensor_recommendations(sensor_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Get recommendations based on sensor data"""
        prompt = f"""
        Provide specific recommendations for {crop} cultivation in {region}, India based on soil sensor data.
        
        Sensor Data: {json.dumps(sensor_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Include:
        1. Irrigation scheduling based on moisture
        2. Fertilizer application timing
        3. Soil amendment needs
        4. pH adjustment requirements
        5. Temperature management
        6. Aeration recommendations
        7. Organic matter additions
        8. Pest and disease prevention
        9. Yield optimization strategies
        10. Cost-effective improvements
        
        Format as JSON with keys: irrigation_scheduling, fertilizer_timing, soil_amendments, ph_adjustments, temperature_management, aeration_recommendations, organic_additions, pest_prevention, yield_optimization, cost_improvements
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "sensor_recommendations"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get sensor recommendations: {str(e)}"}


class AmendmentRecommendationTool:
    """Tools for soil amendment recommendations"""
    
    @staticmethod
    async def recommend_soil_amendments(soil_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Recommend soil amendments based on analysis"""
        prompt = f"""
        Recommend soil amendments for {crop} cultivation in {region}, India based on soil analysis.
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Lime application recommendations (if needed)
        2. Organic matter additions
        3. Compost requirements
        4. Bio-fertilizer suggestions
        5. Green manure crops
        6. Cover crop recommendations
        7. Mulching strategies
        8. Soil conditioner needs
        9. Application timing and methods
        10. Cost-benefit analysis
        
        Format as JSON with keys: lime_recommendations, organic_additions, compost_requirements, bio_fertilizers, green_manure, cover_crops, mulching_strategies, soil_conditioners, application_timing, cost_benefit_analysis
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "amendment_recommendations"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to recommend soil amendments: {str(e)}"}
    
    @staticmethod
    async def create_amendment_schedule(soil_data: Dict[str, Any], crop: str, season: str) -> Dict[str, Any]:
        """Create a detailed amendment application schedule"""
        prompt = f"""
        Create a detailed soil amendment application schedule for {crop} during {season} season.
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Crop: {crop}
        Season: {season}
        
        Include:
        1. Pre-planting amendments
        2. During-growing season applications
        3. Post-harvest soil improvements
        4. Seasonal timing for each amendment
        5. Application rates and methods
        6. Equipment requirements
        7. Weather considerations
        8. Cost estimates
        9. Expected improvements
        10. Monitoring and evaluation
        
        Format as JSON with keys: pre_planting, during_season, post_harvest, seasonal_timing, application_rates, equipment_needs, weather_considerations, cost_estimates, expected_improvements, monitoring_evaluation
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "amendment_schedule"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to create amendment schedule: {str(e)}"}


class LabTestAnalyzerTool:
    """Tools for laboratory test result analysis"""
    
    @staticmethod
    async def analyze_lab_results(lab_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Analyze laboratory test results"""
        prompt = f"""
        Analyze laboratory test results for soil samples from {region}, India for {crop} cultivation.
        
        Lab Data: {json.dumps(lab_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Comprehensive soil health score
        2. Nutrient deficiency analysis
        3. Nutrient excess identification
        4. pH level interpretation
        5. Organic matter assessment
        6. Micronutrient analysis
        7. Soil texture evaluation
        8. Cation exchange capacity
        9. Salinity and alkalinity assessment
        10. Overall soil quality rating
        
        Format as JSON with keys: health_score, deficiency_analysis, excess_identification, ph_interpretation, organic_assessment, micronutrient_analysis, texture_evaluation, cec_analysis, salinity_assessment, quality_rating
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "lab_result_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze lab results: {str(e)}"}
    
    @staticmethod
    async def generate_lab_report(lab_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Generate comprehensive lab report with recommendations"""
        prompt = f"""
        Generate a comprehensive laboratory report for soil analysis in {region}, India for {crop} cultivation.
        
        Lab Data: {json.dumps(lab_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Include:
        1. Executive summary
        2. Detailed test results interpretation
        3. Soil health recommendations
        4. Fertilizer recommendations with quantities
        5. Amendment requirements
        6. Crop suitability assessment
        7. Yield potential analysis
        8. Risk factors and mitigation
        9. Implementation timeline
        10. Expected outcomes and benefits
        
        Format as JSON with keys: executive_summary, test_interpretation, health_recommendations, fertilizer_recommendations, amendment_requirements, crop_suitability, yield_potential, risk_factors, implementation_timeline, expected_outcomes
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "lab_report_generation"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to generate lab report: {str(e)}"}


class FertilizerDatabaseTool:
    """Tools for fertilizer database queries and recommendations"""
    
    @staticmethod
    async def query_fertilizer_database(crop: str, growth_stage: str, soil_data: Dict[str, Any], region: str) -> Dict[str, Any]:
        """Query fertilizer database for specific crop and conditions"""
        prompt = f"""
        Query comprehensive fertilizer information for {crop} during {growth_stage} stage in {region}, India.
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Crop: {crop}
        Growth Stage: {growth_stage}
        Region: {region}
        
        Provide:
        1. Recommended fertilizer types and brands
        2. NPK ratios and formulations
        3. Application rates per acre
        4. Application timing and methods
        5. Cost analysis and budget planning
        6. Organic fertilizer alternatives
        7. Micronutrient requirements
        8. Fertilizer compatibility and mixing
        9. Storage and handling guidelines
        10. Quality specifications and certifications
        
        Format as JSON with keys: fertilizer_types, npk_formulations, application_rates, timing_methods, cost_analysis, organic_alternatives, micronutrient_needs, compatibility_guidelines, storage_handling, quality_specifications
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fertilizer_database_query"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to query fertilizer database: {str(e)}"}
    
    @staticmethod
    async def get_fertilizer_cost_analysis(crop: str, area_acres: float, region: str) -> Dict[str, Any]:
        """Get detailed cost analysis for fertilizer application"""
        prompt = f"""
        Provide detailed cost analysis for fertilizer application for {crop} on {area_acres} acres in {region}, India.
        
        Include:
        1. Fertilizer cost per acre
        2. Application cost (labor and equipment)
        3. Total cost breakdown
        4. Cost comparison between different fertilizer types
        5. Budget planning recommendations
        6. Government subsidy information
        7. Bulk purchase discounts
        8. Seasonal price variations
        9. Cost-benefit analysis
        10. Alternative cost-effective options
        
        Format as JSON with keys: fertilizer_cost_per_acre, application_cost, total_cost_breakdown, cost_comparison, budget_planning, government_subsidies, bulk_discounts, seasonal_prices, cost_benefit_analysis, cost_effective_alternatives
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fertilizer_cost_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get fertilizer cost analysis: {str(e)}"}


class WeatherForecastTool:
    """Tools for weather forecast integration with fertilizer planning"""
    
    @staticmethod
    async def get_fertilizer_weather_forecast(location: str, days: int = 14) -> Dict[str, Any]:
        """Get weather forecast specifically for fertilizer application planning"""
        prompt = f"""
        Provide detailed weather forecast for {location}, India for the next {days} days, specifically for fertilizer application planning.
        
        Include:
        1. Daily temperature (min/max)
        2. Rainfall probability and amounts
        3. Humidity levels
        4. Wind speed and direction
        5. Soil temperature predictions
        6. Evapotranspiration rates
        7. Best application windows
        8. Weather risks for fertilizer application
        9. Post-application weather conditions
        10. Irrigation needs based on weather
        
        Format as JSON with keys: daily_temperature, rainfall_forecast, humidity_levels, wind_conditions, soil_temperature, evapotranspiration, application_windows, weather_risks, post_application_weather, irrigation_needs
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fertilizer_weather_forecast"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get fertilizer weather forecast: {str(e)}"}
    
    @staticmethod
    async def adjust_fertilizer_schedule(fertilizer_plan: Dict[str, Any], weather_data: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Adjust fertilizer application schedule based on weather conditions"""
        prompt = f"""
        Adjust fertilizer application schedule based on weather conditions for {location}, India.
        
        Original Fertilizer Plan: {json.dumps(fertilizer_plan, indent=2)}
        Weather Data: {json.dumps(weather_data, indent=2)}
        Location: {location}
        
        Provide:
        1. Revised application schedule
        2. Weather-based timing adjustments
        3. Risk mitigation strategies
        4. Alternative application methods
        5. Emergency backup plans
        6. Weather monitoring recommendations
        7. Application window optimization
        8. Post-application care based on weather
        9. Cost implications of schedule changes
        10. Success probability assessment
        
        Format as JSON with keys: revised_schedule, timing_adjustments, risk_mitigation, alternative_methods, backup_plans, monitoring_recommendations, window_optimization, post_application_care, cost_implications, success_probability
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fertilizer_schedule_adjustment"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to adjust fertilizer schedule: {str(e)}"}


class PlantGrowthSimulationTool:
    """Tools for plant growth simulation based on fertilizer inputs"""
    
    @staticmethod
    async def simulate_plant_growth(crop: str, fertilizer_plan: Dict[str, Any], soil_data: Dict[str, Any], weather_data: Dict[str, Any], region: str) -> Dict[str, Any]:
        """Simulate plant growth based on fertilizer inputs and conditions"""
        prompt = f"""
        Simulate plant growth for {crop} in {region}, India based on fertilizer inputs and environmental conditions.
        
        Fertilizer Plan: {json.dumps(fertilizer_plan, indent=2)}
        Soil Data: {json.dumps(soil_data, indent=2)}
        Weather Data: {json.dumps(weather_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Growth stage progression timeline
        2. Biomass accumulation predictions
        3. Nutrient uptake patterns
        4. Yield potential estimates
        5. Growth rate variations
        6. Stress indicators and thresholds
        7. Optimal growth conditions
        8. Growth limiting factors
        9. Harvest timing predictions
        10. Quality parameter forecasts
        
        Format as JSON with keys: growth_timeline, biomass_predictions, nutrient_uptake, yield_estimates, growth_rates, stress_indicators, optimal_conditions, limiting_factors, harvest_timing, quality_forecasts
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "plant_growth_simulation"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to simulate plant growth: {str(e)}"}
    
    @staticmethod
    async def optimize_fertilizer_for_growth(crop: str, target_yield: float, soil_data: Dict[str, Any], region: str) -> Dict[str, Any]:
        """Optimize fertilizer application for target growth and yield"""
        prompt = f"""
        Optimize fertilizer application for {crop} to achieve target yield of {target_yield} quintals per acre in {region}, India.
        
        Soil Data: {json.dumps(soil_data, indent=2)}
        Crop: {crop}
        Target Yield: {target_yield} quintals/acre
        Region: {region}
        
        Provide:
        1. Optimized fertilizer schedule
        2. Nutrient application rates
        3. Growth stage-specific applications
        4. Yield optimization strategies
        5. Cost-effective fertilizer combinations
        6. Risk management approaches
        7. Monitoring and adjustment protocols
        8. Expected growth milestones
        9. Quality optimization measures
        10. Success probability and confidence levels
        
        Format as JSON with keys: optimized_schedule, nutrient_rates, stage_specific_applications, yield_strategies, cost_effective_combinations, risk_management, monitoring_protocols, growth_milestones, quality_measures, success_probability
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fertilizer_optimization"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to optimize fertilizer for growth: {str(e)}"}


class EvapotranspirationModelTool:
    """Tools for evapotranspiration calculations and water requirement analysis"""
    
    @staticmethod
    async def calculate_evapotranspiration(crop: str, growth_stage: str, weather_data: Dict[str, Any], soil_data: Dict[str, Any], region: str) -> Dict[str, Any]:
        """Calculate crop evapotranspiration using FAO Penman-Monteith equation"""
        prompt = f"""
        Calculate evapotranspiration (ET) for {crop} in {growth_stage} stage in {region}, India using FAO Penman-Monteith equation.
        
        Weather Data: {json.dumps(weather_data, indent=2)}
        Soil Data: {json.dumps(soil_data, indent=2)}
        Crop: {crop}
        Growth Stage: {growth_stage}
        Region: {region}
        
        Provide:
        1. Reference evapotranspiration (ET0)
        2. Crop coefficient (Kc) for current stage
        3. Crop evapotranspiration (ETc)
        4. Daily water requirement
        5. Weekly water requirement
        6. Monthly water requirement
        7. Peak water demand periods
        8. Water stress indicators
        9. Irrigation scheduling recommendations
        10. Water use efficiency metrics
        
        Format as JSON with keys: et0, crop_coefficient, crop_et, daily_water_requirement, weekly_water_requirement, monthly_water_requirement, peak_demand_periods, water_stress_indicators, irrigation_scheduling, water_use_efficiency
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "evapotranspiration_calculation"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to calculate evapotranspiration: {str(e)}"}
    
    @staticmethod
    async def optimize_irrigation_schedule(et_data: Dict[str, Any], soil_moisture_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Optimize irrigation schedule based on ET and soil moisture data"""
        prompt = f"""
        Optimize irrigation schedule for {crop} in {region}, India based on evapotranspiration and soil moisture data.
        
        ET Data: {json.dumps(et_data, indent=2)}
        Soil Moisture Data: {json.dumps(soil_moisture_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Optimal irrigation frequency
        2. Irrigation timing recommendations
        3. Water application rates
        4. Irrigation method recommendations
        5. Soil moisture thresholds
        6. Water conservation strategies
        7. Cost optimization for irrigation
        8. Weather-based adjustments
        9. Monitoring and control systems
        10. Expected water savings
        
        Format as JSON with keys: irrigation_frequency, timing_recommendations, application_rates, method_recommendations, moisture_thresholds, conservation_strategies, cost_optimization, weather_adjustments, monitoring_systems, water_savings
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "irrigation_optimization"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to optimize irrigation schedule: {str(e)}"}


class IoTSoilMoistureTool:
    """Tools for IoT soil moisture sensor integration and real-time monitoring"""
    
    @staticmethod
    async def integrate_sensor_data(sensor_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Integrate real-time soil moisture sensor data"""
        prompt = f"""
        Integrate and analyze real-time soil moisture sensor data for {crop} cultivation in {region}, India.
        
        Sensor Data: {json.dumps(sensor_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Current soil moisture levels
        2. Moisture trends and patterns
        3. Critical moisture thresholds
        4. Irrigation trigger points
        5. Sensor calibration status
        6. Data quality assessment
        7. Anomaly detection results
        8. Predictive moisture modeling
        9. Real-time alerts and notifications
        10. Historical data comparison
        
        Format as JSON with keys: current_moisture, moisture_trends, critical_thresholds, irrigation_triggers, calibration_status, data_quality, anomaly_detection, predictive_modeling, real_time_alerts, historical_comparison
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "sensor_data_integration"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to integrate sensor data: {str(e)}"}
    
    @staticmethod
    async def get_sensor_recommendations(sensor_data: Dict[str, Any], crop: str, growth_stage: str, region: str) -> Dict[str, Any]:
        """Get irrigation recommendations based on sensor data"""
        prompt = f"""
        Provide irrigation recommendations based on IoT soil moisture sensor data for {crop} in {growth_stage} stage in {region}, India.
        
        Sensor Data: {json.dumps(sensor_data, indent=2)}
        Crop: {crop}
        Growth Stage: {growth_stage}
        Region: {region}
        
        Provide:
        1. Immediate irrigation needs
        2. Recommended irrigation amount
        3. Optimal irrigation timing
        4. Irrigation method suggestions
        5. Water conservation opportunities
        6. Sensor maintenance recommendations
        7. Data interpretation guidelines
        8. Performance optimization tips
        9. Cost-benefit analysis
        10. Technology upgrade suggestions
        
        Format as JSON with keys: immediate_needs, irrigation_amount, optimal_timing, method_suggestions, conservation_opportunities, maintenance_recommendations, interpretation_guidelines, optimization_tips, cost_benefit_analysis, upgrade_suggestions
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "sensor_recommendations"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get sensor recommendations: {str(e)}"}


class WeatherAPITool:
    """Tools for weather API integration and irrigation planning"""
    
    @staticmethod
    async def get_irrigation_weather_forecast(location: str, days: int = 7) -> Dict[str, Any]:
        """Get weather forecast specifically for irrigation planning.

        Preferred: WeatherProvider bundle (cached).
        Fallback: Gemini-generated forecast.
        """
        try:
            provider_result = await _weather_provider.get_weather_bundle(location, days=days)
            if provider_result.get("success"):
                forecast = (provider_result.get("forecast") or {}).get("data") or {}
                daily = forecast.get("daily") or []
                return {
                    "daily_temperature": [
                        {"date": d.get("date"), "min_c": d.get("temp_min_c"), "max_c": d.get("temp_max_c")}
                        for d in daily
                    ],
                    "rainfall_forecast": [
                        {"date": d.get("date"), "rain_total_mm": d.get("rain_total_mm"), "pop_max": d.get("pop_max")}
                        for d in daily
                    ],
                    "humidity_levels": [{"date": d.get("date"), "avg_humidity_pct": d.get("avg_humidity_pct")} for d in daily],
                    "wind_conditions": None,
                    "solar_radiation": None,
                    "evapotranspiration": None,
                    "soil_temperature": None,
                    "irrigation_windows": [
                        {
                            "date": d.get("date"),
                            "recommendation": "Prefer morning/evening irrigation; avoid irrigation close to predicted rainfall." if (d.get("rain_total_mm") or 0) < 2 else "Rain likely; reduce/skip irrigation if soil moisture is adequate.",
                        }
                        for d in daily
                    ],
                    "weather_risks": forecast.get("alerts"),
                    "post_irrigation_weather": None,
                    "sources": provider_result.get("sources"),
                    "fetched_at": provider_result.get("fetched_at"),
                    "provider": "WeatherProvider",
                }
        except Exception:
            pass

        prompt = f"""
        Provide detailed weather forecast for {location}, India for the next {days} days, specifically for irrigation planning.
        
        Include:
        1. Daily temperature (min/max)
        2. Rainfall probability and amounts
        3. Humidity levels
        4. Wind speed and direction
        5. Solar radiation
        6. Evapotranspiration rates
        7. Soil temperature predictions
        8. Best irrigation windows
        9. Weather risks for irrigation
        10. Post-irrigation weather conditions
        
        Format as JSON with keys: daily_temperature, rainfall_forecast, humidity_levels, wind_conditions, solar_radiation, evapotranspiration, soil_temperature, irrigation_windows, weather_risks, post_irrigation_weather
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "irrigation_weather_forecast"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get irrigation weather forecast: {str(e)}"}
    
    @staticmethod
    async def adjust_irrigation_for_weather(irrigation_plan: Dict[str, Any], weather_data: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Adjust irrigation plan based on weather conditions"""
        prompt = f"""
        Adjust irrigation plan based on weather conditions for {location}, India.
        
        Original Irrigation Plan: {json.dumps(irrigation_plan, indent=2)}
        Weather Data: {json.dumps(weather_data, indent=2)}
        Location: {location}
        
        Provide:
        1. Revised irrigation schedule
        2. Weather-based timing adjustments
        3. Water application modifications
        4. Risk mitigation strategies
        5. Alternative irrigation methods
        6. Emergency backup plans
        7. Weather monitoring recommendations
        8. Irrigation window optimization
        9. Post-irrigation care based on weather
        10. Cost implications of adjustments
        
        Format as JSON with keys: revised_schedule, timing_adjustments, application_modifications, risk_mitigation, alternative_methods, backup_plans, monitoring_recommendations, window_optimization, post_irrigation_care, cost_implications
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "irrigation_weather_adjustment"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to adjust irrigation for weather: {str(e)}"}


class ImageRecognitionTool:
    """Tools for image recognition and plant disease identification"""
    
    @staticmethod
    async def identify_plant_disease(image_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Identify plant diseases from image data"""
        prompt = f"""
        Analyze plant disease from image data for {crop} in {region}, India.
        
        Image Data: {json.dumps(image_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Disease identification and classification
        2. Severity assessment (mild, moderate, severe)
        3. Affected plant parts analysis
        4. Disease symptoms description
        5. Potential causes and risk factors
        6. Treatment recommendations
        7. Prevention strategies
        8. Economic impact assessment
        9. Timeline for treatment
        10. Alternative diagnostic methods
        
        Format as JSON with keys: disease_identification, severity_assessment, affected_parts, symptoms_description, potential_causes, treatment_recommendations, prevention_strategies, economic_impact, treatment_timeline, alternative_diagnostics
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "plant_disease_identification"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to identify plant disease: {str(e)}"}
    
    @staticmethod
    async def analyze_pest_damage(image_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Analyze pest damage from image data"""
        prompt = f"""
        Analyze pest damage from image data for {crop} in {region}, India.
        
        Image Data: {json.dumps(image_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Pest identification and classification
        2. Damage severity assessment
        3. Affected plant areas analysis
        4. Pest lifecycle stage identification
        5. Damage pattern analysis
        6. Control recommendations
        7. Integrated pest management strategies
        8. Economic threshold assessment
        9. Monitoring and scouting guidelines
        10. Preventive measures
        
        Format as JSON with keys: pest_identification, damage_severity, affected_areas, lifecycle_stage, damage_patterns, control_recommendations, ipm_strategies, economic_threshold, monitoring_guidelines, preventive_measures
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "pest_damage_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze pest damage: {str(e)}"}


class VoiceToTextTool:
    """Tools for voice-to-text conversion and pest/disease description processing"""
    
    @staticmethod
    async def process_voice_description(voice_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Process voice descriptions of pest and disease issues"""
        prompt = f"""
        Process voice description of pest and disease issues for {crop} in {region}, India.
        
        Voice Data: {json.dumps(voice_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Transcribed text from voice input
        2. Key symptoms and observations extracted
        3. Pest/disease keywords identified
        4. Severity indicators mentioned
        5. Timeline and progression details
        6. Environmental conditions described
        7. Previous treatment attempts mentioned
        8. Farmer concerns and questions
        9. Follow-up questions for clarification
        10. Recommended next steps
        
        Format as JSON with keys: transcribed_text, symptoms_extracted, keywords_identified, severity_indicators, timeline_details, environmental_conditions, previous_treatments, farmer_concerns, follow_up_questions, recommended_steps
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "voice_description_processing"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to process voice description: {str(e)}"}
    
    @staticmethod
    async def convert_speech_to_actionable_data(speech_text: str, crop: str, region: str) -> Dict[str, Any]:
        """Convert speech text to actionable pest/disease data"""
        prompt = f"""
        Convert speech text to actionable pest and disease data for {crop} in {region}, India.
        
        Speech Text: "{speech_text}"
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Structured symptom data
        2. Pest/disease probability scores
        3. Recommended diagnostic tests
        4. Treatment priority ranking
        5. Cost-benefit analysis
        6. Implementation timeline
        7. Resource requirements
        8. Success probability assessment
        9. Risk factors and mitigation
        10. Monitoring and evaluation plan
        
        Format as JSON with keys: structured_symptoms, probability_scores, diagnostic_tests, treatment_priority, cost_benefit_analysis, implementation_timeline, resource_requirements, success_probability, risk_factors, monitoring_plan
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "speech_to_actionable_data"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to convert speech to actionable data: {str(e)}"}


class DiseasePredictionTool:
    """Tools for disease prediction and outbreak forecasting"""
    
    @staticmethod
    async def predict_disease_outbreak(environmental_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Predict potential disease outbreaks based on environmental conditions"""
        prompt = f"""
        Predict potential disease outbreaks for {crop} in {region}, India based on environmental conditions.
        
        Environmental Data: {json.dumps(environmental_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Disease outbreak probability scores
        2. High-risk disease identification
        3. Environmental risk factors
        4. Outbreak timeline predictions
        5. Severity level forecasts
        6. Affected area predictions
        7. Preventive measures recommendations
        8. Early warning indicators
        9. Monitoring and surveillance strategies
        10. Emergency response protocols
        
        Format as JSON with keys: outbreak_probability, high_risk_diseases, environmental_risks, timeline_predictions, severity_forecasts, affected_area_predictions, preventive_measures, early_warning_indicators, monitoring_strategies, emergency_protocols
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "disease_outbreak_prediction"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to predict disease outbreak: {str(e)}"}
    
    @staticmethod
    async def analyze_disease_risk_factors(historical_data: Dict[str, Any], current_conditions: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Analyze disease risk factors based on historical and current data"""
        prompt = f"""
        Analyze disease risk factors for {crop} in {region}, India based on historical and current conditions.
        
        Historical Data: {json.dumps(historical_data, indent=2)}
        Current Conditions: {json.dumps(current_conditions, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Risk factor analysis and scoring
        2. Historical pattern identification
        3. Current risk level assessment
        4. Seasonal risk variations
        5. Weather-related risk factors
        6. Soil and crop condition risks
        7. Management practice impacts
        8. Risk mitigation strategies
        9. Monitoring and early detection
        10. Long-term risk management
        
        Format as JSON with keys: risk_factor_analysis, historical_patterns, current_risk_level, seasonal_variations, weather_risks, soil_crop_risks, management_impacts, mitigation_strategies, monitoring_detection, long_term_management
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "disease_risk_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze disease risk factors: {str(e)}"}


class WeatherMonitoringTool:
    """Tools for weather API integration and real-time weather monitoring"""
    
    @staticmethod
    async def get_real_time_weather(location: str, days: int = 7) -> Dict[str, Any]:
        """Get real-time weather data and forecasts"""
        prompt = f"""
        Provide comprehensive real-time weather data and forecasts for {location}, India for the next {days} days.
        
        Include:
        1. Current weather conditions
        2. Hourly forecasts for next 24 hours
        3. Daily forecasts for next {days} days
        4. Temperature trends (min/max)
        5. Humidity and precipitation data
        6. Wind speed and direction
        7. UV index and solar radiation
        8. Weather alerts and warnings
        9. Agricultural weather indices
        10. Historical weather comparison
        
        Format as JSON with keys: current_conditions, hourly_forecast, daily_forecast, temperature_trends, humidity_precipitation, wind_conditions, uv_solar_radiation, weather_alerts, agricultural_indices, historical_comparison
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "real_time_weather"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get real-time weather: {str(e)}"}
    
    @staticmethod
    async def get_weather_alerts(location: str, alert_types: List[str] = None) -> Dict[str, Any]:
        """Get weather alerts and warnings for specific location"""
        if alert_types is None:
            alert_types = ["rain", "storm", "frost", "heat", "drought"]
        
        prompt = f"""
        Provide weather alerts and warnings for {location}, India.
        
        Alert Types: {', '.join(alert_types)}
        Location: {location}
        
        Include:
        1. Active weather alerts
        2. Alert severity levels
        3. Alert duration and timing
        4. Affected areas and coverage
        5. Recommended actions
        6. Agricultural impact assessment
        7. Crop protection recommendations
        8. Emergency contact information
        9. Alert escalation procedures
        10. Historical alert patterns
        
        Format as JSON with keys: active_alerts, severity_levels, duration_timing, affected_areas, recommended_actions, agricultural_impact, crop_protection, emergency_contacts, escalation_procedures, historical_patterns
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "weather_alerts"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get weather alerts: {str(e)}"}


class AlertSystemTool:
    """Tools for alert system and notification management"""
    
    @staticmethod
    async def send_weather_alert(alert_data: Dict[str, Any], farmer_contacts: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Send weather alerts to farmers via multiple channels"""
        prompt = f"""
        Send weather alert to farmers in {location}, India.
        
        Alert Data: {json.dumps(alert_data, indent=2)}
        Farmer Contacts: {json.dumps(farmer_contacts, indent=2)}
        Location: {location}
        
        Provide:
        1. Alert message content
        2. Delivery channel selection (SMS, email, push notification)
        3. Message personalization
        4. Delivery status tracking
        5. Confirmation receipts
        6. Failed delivery handling
        7. Alert escalation procedures
        8. Response tracking
        9. Delivery analytics
        10. Cost optimization
        
        Format as JSON with keys: alert_message, delivery_channels, message_personalization, delivery_status, confirmation_receipts, failed_delivery_handling, escalation_procedures, response_tracking, delivery_analytics, cost_optimization
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "send_weather_alert"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to send weather alert: {str(e)}"}
    
    @staticmethod
    async def manage_alert_subscriptions(farmer_preferences: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Manage farmer alert subscriptions and preferences"""
        prompt = f"""
        Manage alert subscriptions and preferences for farmers in {location}, India.
        
        Farmer Preferences: {json.dumps(farmer_preferences, indent=2)}
        Location: {location}
        
        Provide:
        1. Subscription management
        2. Alert frequency settings
        3. Channel preferences
        4. Alert type customization
        5. Geographic coverage settings
        6. Time zone handling
        7. Language preferences
        8. Opt-out procedures
        9. Subscription analytics
        10. Preference optimization
        
        Format as JSON with keys: subscription_management, frequency_settings, channel_preferences, alert_customization, geographic_coverage, timezone_handling, language_preferences, opt_out_procedures, subscription_analytics, preference_optimization
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "manage_alert_subscriptions"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to manage alert subscriptions: {str(e)}"}


class SatelliteImageProcessingTool:
    """Tools for satellite image processing and NDVI analysis"""
    
    @staticmethod
    async def analyze_ndvi(satellite_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Analyze NDVI (Normalized Difference Vegetation Index) from satellite images"""
        prompt = f"""
        Analyze NDVI data from satellite images for {crop} cultivation in {region}, India.
        
        Satellite Data: {json.dumps(satellite_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. NDVI value interpretation
        2. Vegetation health assessment
        3. Growth stage identification
        4. Stress indicators analysis
        5. Spatial variability mapping
        6. Historical NDVI comparison
        7. Crop condition recommendations
        8. Monitoring frequency suggestions
        9. Data quality assessment
        10. Integration with other data sources
        
        Format as JSON with keys: ndvi_interpretation, vegetation_health, growth_stage_identification, stress_indicators, spatial_variability, historical_comparison, crop_condition_recommendations, monitoring_frequency, data_quality, data_integration
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "ndvi_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze NDVI: {str(e)}"}
    
    @staticmethod
    async def track_crop_health(satellite_data: Dict[str, Any], crop: str, region: str, time_period: str = "monthly") -> Dict[str, Any]:
        """Track crop health over time using satellite data"""
        prompt = f"""
        Track crop health over {time_period} period for {crop} in {region}, India using satellite data.
        
        Satellite Data: {json.dumps(satellite_data, indent=2)}
        Crop: {crop}
        Region: {region}
        Time Period: {time_period}
        
        Provide:
        1. Health trend analysis
        2. Growth progression tracking
        3. Stress pattern identification
        4. Yield prediction indicators
        5. Intervention recommendations
        6. Seasonal pattern analysis
        7. Comparative performance metrics
        8. Risk assessment
        9. Monitoring schedule optimization
        10. Action plan development
        
        Format as JSON with keys: health_trends, growth_progression, stress_patterns, yield_indicators, intervention_recommendations, seasonal_patterns, performance_metrics, risk_assessment, monitoring_schedule, action_plan
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "crop_health_tracking"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to track crop health: {str(e)}"}


class DroneImageProcessingTool:
    """Tools for drone image processing and crop analysis"""
    
    @staticmethod
    async def analyze_drone_imagery(drone_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Analyze crop health and growth from drone images"""
        prompt = f"""
        Analyze drone imagery for {crop} cultivation in {region}, India.
        
        Drone Data: {json.dumps(drone_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. High-resolution crop analysis
        2. Disease and pest detection
        3. Growth stage assessment
        4. Stress identification
        5. Plant density analysis
        6. Weed detection and mapping
        7. Irrigation efficiency assessment
        8. Fertilizer application zones
        9. Harvest readiness indicators
        10. Precision agriculture recommendations
        
        Format as JSON with keys: crop_analysis, disease_pest_detection, growth_stage_assessment, stress_identification, plant_density, weed_detection, irrigation_efficiency, fertilizer_zones, harvest_readiness, precision_recommendations
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "drone_imagery_analysis"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze drone imagery: {str(e)}"}
    
    @staticmethod
    async def process_thermal_imagery(thermal_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Process thermal imagery for crop stress detection"""
        prompt = f"""
        Process thermal imagery for {crop} stress detection in {region}, India.
        
        Thermal Data: {json.dumps(thermal_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Temperature distribution analysis
        2. Water stress identification
        3. Disease hotspot detection
        4. Irrigation efficiency mapping
        5. Plant health indicators
        6. Stress severity assessment
        7. Intervention priority zones
        8. Thermal pattern interpretation
        9. Correlation with other data
        10. Action recommendations
        
        Format as JSON with keys: temperature_distribution, water_stress_identification, disease_hotspots, irrigation_efficiency, plant_health_indicators, stress_severity, intervention_zones, thermal_patterns, data_correlation, action_recommendations
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "thermal_imagery_processing"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to process thermal imagery: {str(e)}"}


class GrowthStagePredictionTool:
    """Tools for growth stage prediction and monitoring"""
    
    @staticmethod
    async def predict_growth_stages(environmental_data: Dict[str, Any], crop: str, region: str, planting_date: str) -> Dict[str, Any]:
        """Predict crop growth stages based on environmental and historical data"""
        prompt = f"""
        Predict growth stages for {crop} planted on {planting_date} in {region}, India.
        
        Environmental Data: {json.dumps(environmental_data, indent=2)}
        Crop: {crop}
        Region: {region}
        Planting Date: {planting_date}
        
        Provide:
        1. Current growth stage prediction
        2. Stage progression timeline
        3. Key developmental milestones
        4. Environmental factor impacts
        5. Growth rate variations
        6. Stage-specific care requirements
        7. Harvest timing prediction
        8. Risk factors and mitigation
        9. Monitoring recommendations
        10. Intervention timing
        
        Format as JSON with keys: current_stage, progression_timeline, developmental_milestones, environmental_impacts, growth_rate_variations, care_requirements, harvest_timing, risk_factors, monitoring_recommendations, intervention_timing
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "growth_stage_prediction"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to predict growth stages: {str(e)}"}
    
    @staticmethod
    async def monitor_growth_progression(historical_data: Dict[str, Any], current_data: Dict[str, Any], crop: str, region: str) -> Dict[str, Any]:
        """Monitor growth progression and detect anomalies"""
        prompt = f"""
        Monitor growth progression for {crop} in {region}, India and detect any anomalies.
        
        Historical Data: {json.dumps(historical_data, indent=2)}
        Current Data: {json.dumps(current_data, indent=2)}
        Crop: {crop}
        Region: {region}
        
        Provide:
        1. Growth progression analysis
        2. Anomaly detection results
        3. Performance comparison
        4. Deviation explanations
        5. Corrective action recommendations
        6. Timeline adjustments
        7. Risk assessment updates
        8. Monitoring frequency changes
        9. Data quality validation
        10. Future predictions update
        
        Format as JSON with keys: progression_analysis, anomaly_detection, performance_comparison, deviation_explanations, corrective_actions, timeline_adjustments, risk_updates, monitoring_changes, data_validation, future_predictions
        """
        
        try:
            response = await gemini_service.generate_response(prompt, {"task": "growth_progression_monitoring"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to monitor growth progression: {str(e)}"}



class TaskPrioritizationTool:
    """Tools for AI-driven farm task prioritization and optimization"""

    @staticmethod
    async def prioritize_tasks(tasks: List[Dict[str, Any]], resources: Dict[str, Any], constraints: Dict[str, Any], weather_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Prioritize and schedule tasks given constraints and resources"""
        prompt = f"""
        Prioritize and schedule farm tasks given available resources, constraints, and optional weather data.

        Tasks: {json.dumps(tasks, indent=2)}
        Resources: {json.dumps(resources, indent=2)}
        Constraints: {json.dumps(constraints, indent=2)}
        Weather Data: {json.dumps(weather_data or {}, indent=2)}

        Provide:
        1. Ordered task list with priorities (high/medium/low)
        2. Suggested schedule (date/time windows)
        3. Resource allocation per task (labor, machinery)
        4. Dependencies and blocking tasks
        5. Risk/impact assessment for delays
        6. Optimization notes (why ordering chosen)

        Format as JSON with keys: ordered_tasks, schedule, resource_allocation, dependencies, risk_assessment, optimization_notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "task_prioritization"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to prioritize tasks: {str(e)}"}

    @staticmethod
    async def optimize_sequence(ordered_tasks: List[Dict[str, Any]], objective: str = "minimize_lateness") -> Dict[str, Any]:
        """Optimize sequence according to an objective"""
        prompt = f"""
        Optimize the given ordered tasks according to objective: {objective}.

        Ordered Tasks: {json.dumps(ordered_tasks, indent=2)}
        Objective: {objective}

        Provide:
        1. Final task order
        2. Objective value estimate
        3. Bottlenecks and suggestions

        Format as JSON with keys: final_order, objective_value, bottlenecks, suggestions
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "task_sequence_optimization"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to optimize sequence: {str(e)}"}


class RealTimeTrackingTool:
    """Tools for task tracking integration (e.g., Trello-like)"""

    @staticmethod
    async def sync_tasks(board_info: Dict[str, Any], tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync tasks to tracking board and return link/ids"""
        prompt = f"""
        Sync tasks to a task tracking board.

        Board Info: {json.dumps(board_info, indent=2)}
        Tasks: {json.dumps(tasks, indent=2)}

        Provide:
        1. Board URL and identifiers
        2. Created/updated task mappings (local_id -> remote_id)
        3. Status of each operation
        4. Next actions for the farmer

        Format as JSON with keys: board_url, task_mappings, operation_status, next_actions
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "task_tracking_sync"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to sync tasks: {str(e)}"}

    @staticmethod
    async def progress_snapshot(board_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get a progress snapshot from tracking system"""
        prompt = f"""
        Provide a concise progress snapshot for the given task board.

        Board Info: {json.dumps(board_info, indent=2)}

        Provide JSON with: summary, tasks_by_status, blockers, upcoming_deadlines
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "task_progress_snapshot"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to get progress snapshot: {str(e)}"}


class MaintenanceTrackerTool:
    """Tools for machinery maintenance planning and tracking"""

    @staticmethod
    async def build_maintenance_plan(equipment: List[Dict[str, Any]], usage_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Build a preventive maintenance plan"""
        prompt = f"""
        Build a preventive maintenance plan for farm machinery.

        Equipment: {json.dumps(equipment, indent=2)}
        Usage Stats: {json.dumps(usage_stats, indent=2)}

        Provide JSON with: maintenance_schedule, parts_list, labor_hours, estimated_costs, priority_items, safety_checks
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "maintenance_plan"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to build maintenance plan: {str(e)}"}

    @staticmethod
    async def track_service_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Track service events and compute next service due"""
        prompt = f"""
        Track service events and compute next service due for each equipment.

        Events: {json.dumps(events, indent=2)}

        Provide JSON with: next_service_due, overdue_items, warranty_flags, cost_summary
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "maintenance_events_tracking"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to track service events: {str(e)}"}


class PredictiveMaintenanceTool:
    """Tools for predictive maintenance using usage and telemetry"""

    @staticmethod
    async def predict_failures(telemetry: Dict[str, Any], equipment_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict potential failures and risk windows"""
        prompt = f"""
        Predict potential machinery failures and risk windows based on telemetry and metadata.

        Telemetry: {json.dumps(telemetry, indent=2)}
        Equipment Meta: {json.dumps(equipment_meta, indent=2)}

        Provide JSON with: high_risk_components, failure_probabilities, risk_windows, recommended_actions
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "predictive_maintenance"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to predict failures: {str(e)}"}

    @staticmethod
    async def optimize_uptime(plan: Dict[str, Any], spare_inventory: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize uptime and parts strategy"""
        prompt = f"""
        Optimize machinery uptime and spare parts strategy.

        Maintenance Plan: {json.dumps(plan, indent=2)}
        Spare Inventory: {json.dumps(spare_inventory, indent=2)}

        Provide JSON with: optimized_plan, spare_stock_recommendations, downtime_reduction, roi_estimate
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "uptime_optimization"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to optimize uptime: {str(e)}"}


class FieldMappingTool:
    """Tools for farm layout mapping and geospatial analysis (OSM/Geo)"""

    @staticmethod
    async def generate_field_map(field_boundaries: List[Dict[str, Any]], overlays: Dict[str, Any], region: str) -> Dict[str, Any]:
        """Generate a field map with overlays (simulated via LLM prompt)"""
        prompt = f"""
        Generate a farm field map representation for {region}, India with overlays.

        Field Boundaries: {json.dumps(field_boundaries, indent=2)}
        Overlays: {json.dumps(overlays, indent=2)}
        Region: {region}

        Provide:
        1. Map layers (base, fields, irrigation, roads)
        2. Summary of field areas and centroids
        3. Suggested management zones
        4. Exportable artifacts (geojson/png descriptors)

        Format as JSON with keys: layers, field_summaries, management_zones, exports
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "generate_field_map"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to generate field map: {str(e)}"}

    @staticmethod
    async def analyze_field_shapes(field_boundaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze fields for area, perimeter, compactness, adjacency"""
        prompt = f"""
        Analyze field shapes for area, perimeter, compactness, and adjacency.

        Field Boundaries: {json.dumps(field_boundaries, indent=2)}

        Provide JSON with: areas, perimeters, compactness_scores, adjacency_graph, irrigation_zones
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "analyze_field_shapes"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to analyze field shapes: {str(e)}"}

    @staticmethod
    async def export_map(map_data: Dict[str, Any], formats: List[str]) -> Dict[str, Any]:
        """Export map in requested formats (meta only)"""
        prompt = f"""
        Prepare exportable artifacts for the provided map data.

        Map Data: {json.dumps(map_data, indent=2)}
        Formats: {formats}

        Provide JSON with: exports (format -> url_or_path), size_estimates, notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "export_map"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to export map: {str(e)}"}


class YieldModelTool:
    """Tools for yield modeling: training, prediction, and climate data loading"""

    @staticmethod
    async def load_climate_data(region: str, crop: str, years: int = 10) -> Dict[str, Any]:
        prompt = f"""
        Load historical climate data for yield modeling in {region}, India for crop {crop} for the past {years} years.

        Provide JSON with: temperature_series, rainfall_series, drought_days_series, anomalies, notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "load_climate_data"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to load climate data: {str(e)}"}

    @staticmethod
    async def train_yield_model(historical_yields: Dict[str, List[float]], climate_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Train a yield prediction model using provided historical yields, climate data, and additional features.

        Historical Yields: {json.dumps(historical_yields, indent=2)}
        Climate Data: {json.dumps(climate_data, indent=2)}
        Features: {json.dumps(features, indent=2)}

        Provide JSON with: model_id, feature_importance, cv_score, training_notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "train_yield_model"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to train yield model: {str(e)}"}

    @staticmethod
    async def predict_yield(model_id: str, crop: str, soil_data: Dict[str, Any], weather_forecast: Dict[str, Any], management: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Predict yield using model {model_id} for {crop} with provided soil data, weather forecast, and management.

        Soil Data: {json.dumps(soil_data, indent=2)}
        Weather Forecast: {json.dumps(weather_forecast, indent=2)}
        Management: {json.dumps(management, indent=2)}

        Provide JSON with: predicted_yield, confidence, risk_factors, drivers
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "predict_yield"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to predict yield: {str(e)}"}


class ProfitOptimizationTool:
    """Tools for profitability analysis and crop mix optimization"""

    @staticmethod
    async def calculate_profitability(crops: List[str], yields: Dict[str, float], prices: Dict[str, float], costs: Dict[str, float], area_acres: float) -> Dict[str, Any]:
        prompt = f"""
        Compute profitability per crop and overall farm profitability.

        Crops: {crops}
        Yields (t/acre): {json.dumps(yields, indent=2)}
        Prices (per t): {json.dumps(prices, indent=2)}
        Costs (per acre): {json.dumps(costs, indent=2)}
        Area Acres: {area_acres}

        Provide JSON with: crop_analysis, total_revenue, total_costs, total_profit, profit_margin, roi
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "calculate_profitability"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to calculate profitability: {str(e)}"}

    @staticmethod
    async def optimize_crop_mix(crops: List[str], yields: Dict[str, float], prices: Dict[str, float], costs: Dict[str, float], total_area: float, constraints: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Optimize crop mix allocation for maximum profit under constraints.

        Crops: {crops}
        Yields: {json.dumps(yields, indent=2)}
        Prices: {json.dumps(prices, indent=2)}
        Costs: {json.dumps(costs, indent=2)}
        Total Area: {total_area}
        Constraints: {json.dumps(constraints, indent=2)}

        Provide JSON with: optimal_allocation, projected_profitability, risk_level, feasibility_notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "optimize_crop_mix"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to optimize crop mix: {str(e)}"}

    @staticmethod
    async def export_profit_report(profit_data: Dict[str, Any], format: str = "csv") -> Dict[str, Any]:
        prompt = f"""
        Prepare a profitability report export in {format} format.

        Profit Data: {json.dumps(profit_data, indent=2)}

        Provide JSON with: export_url, size_bytes, notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "export_profit_report"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to export profit report: {str(e)}"}


class MarketIntelligenceTool:
    """Tools for market price intelligence and trend visualization"""

    @staticmethod
    async def fetch_mandi_prices(crops: List[str], location: str) -> Dict[str, Any]:
        try:
            provider_result = await _mandi_price_provider.get_mandi_prices(crops, location, limit_per_crop=10)
            if provider_result.get("success"):
                return {
                    "mandi_prices": provider_result.get("mandi_prices"),
                    "latest_snapshot": provider_result.get("latest_snapshot"),
                    "data_sources": provider_result.get("data_sources") or [provider_result.get("source")],
                    "fetched_at": provider_result.get("fetched_at"),
                    "provider": "MandiPriceProvider",
                    "errors": provider_result.get("errors"),
                }
        except Exception:
            pass

        prompt = f"""
        Fetch recent mandi prices for crops in {location}, India.

        Crops: {crops}

        Provide JSON with: mandi_prices (crop -> list of {{date, mandi, price}}), latest_snapshot (crop -> price), data_sources
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fetch_mandi_prices"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch mandi prices: {str(e)}"}

    @staticmethod
    async def fetch_global_prices(crops: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Fetch global commodity price indicators for given crops.

        Crops: {crops}

        Provide JSON with: global_prices (crop -> {index, last_close, change_pct}), sources
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fetch_global_prices"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch global prices: {str(e)}"}

    @staticmethod
    async def plot_price_trend(price_series: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        prompt = f"""
        Create a simple price trend visualization metadata for given time series per crop.

        Series: {json.dumps(price_series, indent=2)}

        Provide JSON with: chart_specs (per crop), insights (per crop), export_links (png/svg simulated)
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "plot_price_trend"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to plot price trend: {str(e)}"}


class LogisticsTool:
    """Tools for logistics, routing, storage options, and cost estimation"""

    @staticmethod
    async def calculate_transport_route(origin: str, destination: str, cargo_tons: float) -> Dict[str, Any]:
        prompt = f"""
        Plan an efficient transport route for agricultural cargo.

        Origin: {origin}
        Destination: {destination}
        Cargo (tons): {cargo_tons}

        Provide JSON with: route_summary, distance_km, duration_hours, suggested_vehicle, tolls_estimate, fuel_liters_estimate, notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "calculate_transport_route"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to calculate transport route: {str(e)}"}

    @staticmethod
    async def list_storage_options(location: str, crop: str, quantity_tons: float) -> Dict[str, Any]:
        prompt = f"""
        List nearby storage options for harvested crops.

        Location: {location}
        Crop: {crop}
        Quantity (tons): {quantity_tons}

        Provide JSON with: facilities (name, type, distance_km, capacity_tons, daily_rate), cold_storage_needed, recommendations
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "list_storage_options"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to list storage options: {str(e)}"}

    @staticmethod
    async def estimate_storage_cost(crop: str, quantity_tons: float, duration_days: int, cold_storage: bool = False) -> Dict[str, Any]:
        prompt = f"""
        Estimate storage costs for agricultural produce.

        Crop: {crop}
        Quantity (tons): {quantity_tons}
        Duration (days): {duration_days}
        Cold Storage: {cold_storage}

        Provide JSON with: base_rate_per_ton_day, cold_storage_premium, handling_fees, total_cost, spoilage_risk_notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "estimate_storage_cost"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to estimate storage cost: {str(e)}"}


class ProcurementTool:
    """Tools for input procurement: supplier search, offer comparison, bulk timing"""

    @staticmethod
    async def search_suppliers(item: str, location: str) -> Dict[str, Any]:
        prompt = f"""
        Find suppliers for farm inputs.

        Item: {item}
        Location: {location}

        Provide JSON with: suppliers (name, distance_km, price, min_order_qty, contact), notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "search_suppliers"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to search suppliers: {str(e)}"}

    @staticmethod
    async def compare_offers(offers: List[Dict[str, Any]], criteria: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Compare supplier offers for farm inputs.

        Offers: {json.dumps(offers, indent=2)}
        Criteria: {json.dumps(criteria, indent=2)}

        Provide JSON with: ranking, best_value_offer, delivery_considerations, negotiation_tips
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "compare_offers"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to compare offers: {str(e)}"}

    @staticmethod
    async def suggest_bulk_timing(item: str, region: str) -> Dict[str, Any]:
        prompt = f"""
        Suggest the best timing for bulk purchase based on seasonality and demand.

        Item: {item}
        Region: {region}

        Provide JSON with: best_months, expected_discounts_pct, risk_notes, storage_considerations
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "suggest_bulk_timing"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to suggest bulk timing: {str(e)}"}


class InsuranceRiskTool:
    """Tools for insurance plan fetching, risk scoring, and claim form generation"""

    @staticmethod
    async def fetch_insurance_plans(crops: List[str], location: str) -> Dict[str, Any]:
        prompt = f"""
        Fetch crop insurance plans for farmers.

        Crops: {crops}
        Location: {location}

        Provide JSON with: plans (id, name, type, coverage, premium_rate, notes), enrollment_links
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fetch_insurance_plans"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch insurance plans: {str(e)}"}

    @staticmethod
    async def calculate_risk_score(crops: List[str], location: str, factors: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Calculate crop risk scores to guide insurance choices.

        Crops: {crops}
        Location: {location}
        Factors: {factors}

        Provide JSON with: overall_risk (low/medium/high), crop_scores (per crop 0-1), drivers, mitigation
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "calculate_risk_score"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to calculate risk score: {str(e)}"}

    @staticmethod
    async def generate_claim_form(plan_id: str, farmer_details: Dict[str, Any], incident: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Generate a prefilled claim form metadata for crop insurance.

        Plan ID: {plan_id}
        Farmer: {json.dumps(farmer_details, indent=2)}
        Incident: {json.dumps(incident, indent=2)}

        Provide JSON with: form_fields_prefilled, required_documents, submission_instructions, timeline
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "generate_claim_form"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to generate claim form: {str(e)}"}


class FarmerCoachTool:
    """Tools for localized tips, FAQs, and translation"""

    @staticmethod
    async def fetch_local_tips(task: str, season: str, region: str) -> Dict[str, Any]:
        prompt = f"""
        Provide localized farming tips.

        Task: {task}
        Season: {season}
        Region: {region}

        Provide JSON with: tips, cautions, low_cost_hacks, sources
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fetch_local_tips"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch local tips: {str(e)}"}

    @staticmethod
    async def chat_faq(user_query: str, region: str) -> Dict[str, Any]:
        prompt = f"""
        Answer farmer FAQ conversationally.

        Query: {user_query}
        Region: {region}

        Provide JSON with: answer, related_questions, next_steps
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "chat_faq"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to answer FAQ: {str(e)}"}

    @staticmethod
    async def translate_text(text: str, target_language: str) -> Dict[str, Any]:
        prompt = f"""
        Translate farmer-facing text.

        Text: {text}
        Target Language: {target_language}

        Provide JSON with: translated_text, quality_estimate, glossary_notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "translate_text"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to translate text: {str(e)}"}

    @staticmethod
    async def fetch_government_schemes(user_query: str, region: str) -> Dict[str, Any]:
        """Fetch government schemes from authorized sources.

        Preferred: SchemesProvider (SerpAPI + curated fallback) with caching.
        Fallback: Gemini.
        """
        try:
            provider_result = await _schemes_provider.search_schemes(user_query, region=region, max_results=10)
            if provider_result.get("success"):
                return {
                    "schemes": provider_result.get("schemes"),
                    "source": provider_result.get("source"),
                    "fetched_at": provider_result.get("fetched_at"),
                    "provider": "SchemesProvider",
                }
        except Exception:
            pass

        prompt = f"""
        Fetch relevant Indian government schemes for farmers.

        Query: {user_query}
        Region: {region}

        Provide JSON with: schemes (name, benefit, eligibility, link), deadlines
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fetch_government_schemes"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch government schemes: {str(e)}"}


class ComplianceCertificationTool:
    """Tools for certification requirements, checklists, and document management"""

    @staticmethod
    async def fetch_cert_requirements(cert_type: str, region: str) -> Dict[str, Any]:
        prompt = f"""
        Fetch certification requirements for farmers.

        Certification Type: {cert_type}
        Region: {region}

        Provide JSON with: requirements, authorities, timelines, fees, assistance_programs
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fetch_cert_requirements"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch certification requirements: {str(e)}"}

    @staticmethod
    async def build_cert_checklist(cert_type: str, farm_profile: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Build a stepwise checklist for certification.

        Certification Type: {cert_type}
        Farm Profile: {json.dumps(farm_profile, indent=2)}

        Provide JSON with: steps, documents_needed, suggested_order, estimated_duration
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "build_cert_checklist"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to build certification checklist: {str(e)}"}

    @staticmethod
    async def manage_cert_docs(current_docs: Dict[str, Any], action: str) -> Dict[str, Any]:
        prompt = f"""
        Manage certification documents.

        Current Docs: {json.dumps(current_docs, indent=2)}
        Action: {action}

        Provide JSON with: updated_docs, missing_items, reminders
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "manage_cert_docs"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to manage certification documents: {str(e)}"}


class CommunityEngagementTool:
    """Tools for community discovery, schemes, and messaging"""

    @staticmethod
    async def list_nearby_peers(location: str, radius_km: int = 50) -> Dict[str, Any]:
        prompt = f"""
        List nearby farming peers and groups.

        Location: {location}
        Radius (km): {radius_km}

        Provide JSON with: peers (name, contact, specialty), groups, recommendations
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "list_nearby_peers"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to list nearby peers: {str(e)}"}

    @staticmethod
    async def fetch_coop_schemes(region: str) -> Dict[str, Any]:
        prompt = f"""
        Fetch cooperative and government schemes for farmers.

        Region: {region}

        Provide JSON with: schemes (name, benefit, eligibility, link), deadlines
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "fetch_coop_schemes"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch cooperative schemes: {str(e)}"}

    @staticmethod
    async def create_group_message(topic: str, audience: str) -> Dict[str, Any]:
        prompt = f"""
        Create an inviting, concise message for a farmer group.

        Topic: {topic}
        Audience: {audience}

        Provide JSON with: message_text, suggested_channels, timing_suggestion
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "create_group_message"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to create group message: {str(e)}"}


class CarbonSustainabilityTool:
    """Tools to compute carbon footprint, sequestration, and sustainable practices"""

    @staticmethod
    async def calculate_carbon_footprint(inputs: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Estimate farm-level greenhouse gas emissions (CO2e).

        Inputs: {json.dumps(inputs, indent=2)}

        Provide JSON with: total_emissions, by_source, emissions_per_acre, notes
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "calculate_carbon_footprint"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to calculate carbon footprint: {str(e)}"}

    @staticmethod
    async def estimate_sequestration(practices: List[Dict[str, Any]], farm_size: float) -> Dict[str, Any]:
        prompt = f"""
        Estimate carbon sequestration from sustainable practices.

        Practices: {json.dumps(practices, indent=2)}
        Farm Size (acres): {farm_size}

        Provide JSON with: annual_sequestration, per_practice, credit_potential
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "estimate_sequestration"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to estimate sequestration: {str(e)}"}

    @staticmethod
    async def suggest_sustainable_practices(context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Suggest high-impact sustainable practices for the farm.

        Context: {json.dumps(context, indent=2)}

        Provide JSON with: prioritized_practices, costs, expected_benefits, timeline
        """
        try:
            response = await gemini_service.generate_response(prompt, {"task": "suggest_sustainable_practices"})
            return gemini_service._parse_json_response(response)
        except Exception as e:
            return {"error": f"Failed to suggest sustainable practices: {str(e)}"}
