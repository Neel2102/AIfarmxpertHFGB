from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import SoilTool, WeatherTool, MarketTool, CropTool, WebScrapingTool, ClimatePredictionTool, MarketAnalysisTool
from farmxpert.services.gemini_service import gemini_service


class CropSelectorAgent(EnhancedBaseAgent):
    name = "crop_selector"
    description = "Suggests crops based on soil, weather and market signals"

    def _get_system_prompt(self) -> str:
        return """You are a Crop Selection Agent specializing in recommending the best crops for farmers based on their specific conditions.

Your expertise includes:
- Soil analysis and crop compatibility
- Seasonal planting recommendations
- Regional climate considerations
- Market demand and profitability
- Crop rotation strategies

Always provide practical, actionable recommendations with clear reasoning."""

    def _get_examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "What crops should I plant in clay soil during monsoon season?",
                "output": "For clay soil during monsoon, I recommend rice, maize, or sugarcane. These crops thrive in water-retentive clay soil and benefit from monsoon rainfall."
            },
            {
                "input": "Best crops for sandy soil in dry climate?",
                "output": "For sandy soil in dry climates, consider drought-resistant crops like millets (bajra, jowar), groundnuts, or cotton. These crops have deep root systems and low water requirements."
            }
        ]

    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle crop selection using traditional logic"""
        query = inputs.get("query", "")
        context = inputs.get("context", {})
        soil = SoilTool.load_static({**context, "session_id": inputs.get("session_id"), "user_id": context.get("user_id")}) or inputs.get("soil", {})
        season = context.get("entities", {}).get("time_period") or inputs.get("season", "unknown")
        location = context.get("farm_location", inputs.get("location", "unknown"))
        entities = inputs.get("entities", {})

        # Extract crop from entities if mentioned
        mentioned_crop = entities.get("crop")
        
        # Basic crop recommendations based on season and soil
        suggested_crops = self._get_crop_recommendations(season, soil, location, mentioned_crop)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(season, soil, location, suggested_crops)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(suggested_crops, soil, season)
        
        return {
            "agent": self.name,
            "success": True,
            "response": f"Based on your {season} season and soil conditions, I recommend: {', '.join(suggested_crops[:3])}",
            "recommendations": recommendations,
            "insights": [reasoning],
            "data": {
                "location": location,
                "season": season,
                "soil_summary": {k: soil.get(k) for k in ("ph", "npk", "organic") if k in soil},
                "suggested_crops": suggested_crops,
                "reasoning": reasoning
            },
            "confidence": 0.8
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize real tools
        try:
            from farmxpert.tools.crop_planning.market_scraper import MarketScraperTool
            from farmxpert.tools.crop_planning.weather_client import WeatherClientTool
            self.market_tool = MarketScraperTool()
            self.weather_tool = WeatherClientTool()
        except ImportError:
            self.market_tool = None
            self.weather_tool = None
            self.logger.warning("Could not import real tools for CropSelectorAgent")

    async def _handle_internal_logic(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle crop selection using internal deterministic crop selector with REAL TOOLS via tools.py."""
        from farmxpert.agents.crop_planning.crop_selector_pkg.agents.json_crop_selector import JSONCropSelector

        context = inputs.get("context") or {}
        location = context.get("farm_location") or context.get("location") or inputs.get("location") or {}
        if isinstance(location, str):
            location_text = location
            location = {"state": context.get("state") or "", "district": context.get("district") or ""}
        else:
            location_text = f"{location.get('district', '')}, {location.get('state', '')}".strip(', ')
        
        if not isinstance(location, dict):
            location = {}

        # --- REAL TOOL INTEGRATION START ---
        # enrich context with real weather and market data if tools are available
        real_weather = {}
        real_market = {}
        
        if self.weather_tool and location_text:
            try:
                # Fetch 5-day forecast
                forecast = self.weather_tool.get_forecast(location_text)
                if forecast and "list" in forecast:
                    real_weather = {
                        "forecast": forecast["list"][:3], # first 3 intervals
                        "source": forecast.get("source", "simulated")
                    }
                    self.logger.info(f"Enriched CropSelector with weather data for {location_text}")
            except Exception as e:
                self.logger.warning(f"Failed to fetch real weather: {e}")

        if self.market_tool and location.get("state"):
             # We don't know the crop yet, but if the user *mentioned* a crop, we can look it up
             # OR we can pass this tool to the JSON selector (if it supported it)
             # For now, let's just scrape for a common crop like 'Wheat' or 'Rice' as a baseline check
             # or better, check if query has a crop.
             mentioned_crop = self._extract_crop_from_query(inputs.get("query", ""))
             if mentioned_crop:
                 try:
                     market_data = self.market_tool.fetch_market_prices(mentioned_crop, location.get("state"))
                     if market_data:
                         real_market = {"prices": market_data, "trend": "analyzed"}
                         self.logger.info(f"Enriched CropSelector with market data for {mentioned_crop}")
                 except Exception as e:
                     self.logger.warning(f"Failed to fetch market data: {e}")
        # --- REAL TOOL INTEGRATION END ---

        season = (
            context.get("entities", {}).get("time_period")
            or context.get("season")
            or inputs.get("season")
            or "Kharif"
        )
        land_size_acre = context.get("land_size_acre") or context.get("land") or inputs.get("land_size_acre") or 1.0
        risk_preference = context.get("risk_preference") or inputs.get("risk_preference") or "Medium"

        agent_inputs = {
            "farmer_context": {
                "location": {
                    "state": location.get("state") or location.get("State") or "",
                    "district": location.get("district") or location.get("District") or "",
                },
                "season": season,
                "land_size_acre": float(land_size_acre) if land_size_acre is not None else 1.0,
                "risk_preference": risk_preference,
            },
            # Inject real tool data into context for reasoning
            "weather_watcher": {**real_weather, **(context.get("weather_watcher") or {})},
            "market_intelligence": {**real_market, **(context.get("market_intelligence") or {})},
            
            "soil_health": context.get("soil_health") or context.get("soil") or context.get("soil_data") or {},
            "irrigation_planner": context.get("irrigation_planner") or context.get("irrigation") or {},
            "fertilizer_agent": context.get("fertilizer_agent") or context.get("fertilizer") or {},
        }

        selector = JSONCropSelector()
        reco = selector.select_crop_from_json(agent_inputs)
        data = reco.get("recommendation") if isinstance(reco, dict) else None

        recommendations: List[str] = []
        if isinstance(data, dict) and data.get("crop"):
            recommendations.append(f"Recommended crop: {data['crop']}")
            # Add market insight if we scraped it
            if real_market.get("prices"):
                 best_price = max(p["modal_price"] for p in real_market["prices"])
                 recommendations.append(f"Current market price trend for {data['crop']}: approx ₹{best_price}/quintal")

        next_steps = []
        if isinstance(reco, dict) and isinstance(reco.get("next_steps"), list):
            next_steps = [str(x) for x in reco.get("next_steps")[:5]]

        return {
            "agent": self.name,
            "success": True,
            "response": f"Recommended crop: {data.get('crop') if isinstance(data, dict) else ''}".strip(),
            "recommendations": recommendations,
            "warnings": [],
            "next_steps": next_steps,
            "data": reco,
            "metadata": {
                "mode": "internal_crop_selector_with_real_tools", 
                "tools_used": ["WeatherClient", "MarketScraper"] if (real_weather or real_market) else []
            },
        }
    
    def _extract_crop_from_query(self, query: str) -> Optional[str]:
        """Extract mentioned crop from user query"""
        query_lower = query.lower()
        crops = ["wheat", "rice", "maize", "cotton", "sugarcane", "groundnut", "soybean", 
                "barley", "mustard", "chickpea", "lentil", "potato", "onion", "tomato"]
        
        for crop in crops:
            if crop in query_lower:
                return crop
        return None
    
    def _extract_recommendations_from_data(self, crop_data: Dict[str, Any]) -> List[str]:
        """Extract recommendations from crop data"""
        recommendations = []
        
        if isinstance(crop_data, dict):
            if "recommended_crops" in crop_data:
                crops = crop_data["recommended_crops"]
                if isinstance(crops, list):
                    recommendations.append(f"Consider these crops: {', '.join(crops[:3])}")
            
            if "market_analysis" in crop_data:
                market = crop_data["market_analysis"]
                if isinstance(market, dict) and "profitability" in market:
                    recommendations.append(f"Market analysis: {market['profitability']}")
        
        return recommendations
    
    def _extract_warnings_from_data(self, weather_data: Dict[str, Any], market_data: Dict[str, Any]) -> List[str]:
        """Extract warnings from weather and market data"""
        warnings = []
        
        if isinstance(weather_data, dict):
            if "agricultural_impact" in weather_data:
                impact = weather_data["agricultural_impact"]
                if isinstance(impact, dict) and "risks" in impact:
                    warnings.append(f"Weather risks: {impact['risks']}")
        
        if isinstance(market_data, dict):
            if "market_risks" in market_data:
                risks = market_data["market_risks"]
                if isinstance(risks, list):
                    warnings.extend([f"Market risk: {risk}" for risk in risks[:2]])
        
        return warnings

    def _get_crop_recommendations(self, season: str, soil: Dict[str, Any], location: str, mentioned_crop: str = None) -> List[str]:
        """Get crop recommendations based on conditions"""
        if mentioned_crop:
            return [mentioned_crop]
        
        # Season-based recommendations
        season_crops = {
            "kharif": ["rice", "maize", "cotton", "sugarcane", "groundnut", "soybean"],
            "rabi": ["wheat", "barley", "mustard", "chickpea", "lentil", "potato"],
            "zaid": ["cucumber", "watermelon", "muskmelon", "bitter gourd"],
            "monsoon": ["rice", "maize", "sugarcane", "cotton"],
            "winter": ["wheat", "barley", "mustard", "potato", "onion"],
            "summer": ["rice", "maize", "cotton", "groundnut"]
        }
        
        # Get crops for season
        season_lower = season.lower()
        crops = []
        
        for key, crop_list in season_crops.items():
            if key in season_lower:
                crops.extend(crop_list)
        
        # If no season match, use general recommendations
        if not crops:
            crops = ["wheat", "maize", "pulses", "rice", "cotton"]
        
        # Filter based on soil pH if available
        ph = soil.get("ph", 7.0)
        if ph < 6.0:
            # Acidic soil - prefer rice, maize
            crops = [c for c in crops if c in ["rice", "maize", "potato", "tomato"]]
        elif ph > 7.5:
            # Alkaline soil - prefer wheat, barley
            crops = [c for c in crops if c in ["wheat", "barley", "mustard", "cotton"]]
        
        return crops[:5]  # Return top 5 recommendations

    def _generate_reasoning(self, season: str, soil: Dict[str, Any], location: str, crops: List[str]) -> str:
        """Generate reasoning for crop recommendations"""
        reasoning_parts = []
        
        # Season reasoning
        if season and season != "unknown":
            reasoning_parts.append(f"Selected crops are suitable for {season} season")
        
        # Soil reasoning
        ph = soil.get("ph")
        if ph:
            if ph < 6.0:
                reasoning_parts.append("Crops selected for acidic soil conditions")
            elif ph > 7.5:
                reasoning_parts.append("Crops selected for alkaline soil conditions")
            else:
                reasoning_parts.append("Crops selected for neutral soil pH")
        
        # Location reasoning
        if location and location != "unknown":
            reasoning_parts.append(f"Recommendations consider {location} climate")
        
        return ". ".join(reasoning_parts) if reasoning_parts else "Crops selected based on general agricultural best practices"

    def _generate_recommendations(self, crops: List[str], soil: Dict[str, Any], season: str) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if crops:
            recommendations.append(f"Consider planting {crops[0]} as your primary crop")
            if len(crops) > 1:
                recommendations.append(f"Use {crops[1]} as a secondary crop for diversification")
        
        # Soil-specific recommendations
        ph = soil.get("ph")
        if ph and ph < 6.0:
            recommendations.append("Consider lime application to improve soil pH")
        elif ph and ph > 7.5:
            recommendations.append("Consider sulfur application to lower soil pH")
        
        # Season-specific recommendations
        if "monsoon" in season.lower() or "kharif" in season.lower():
            recommendations.append("Ensure proper drainage to prevent waterlogging")
        elif "winter" in season.lower() or "rabi" in season.lower():
            recommendations.append("Plan irrigation schedule for dry winter months")
        
        return recommendations[:3]  # Limit to 3 recommendations


