from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent, AgentStatus
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

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for handling crop selection requests.
        Routes to internal logic (real tools) or traditional fallback.
        """
        self.status = AgentStatus.RUNNING if hasattr(self, 'status') else None
        try:
            # Use internal logic with real tools by default if available
            return await self._handle_internal_logic(inputs)
        except Exception as e:
            self.logger.warning(f"Internal logic failed, falling back to traditional: {e}")
            return await self._handle_traditional(inputs)
        finally:
            self.status = AgentStatus.COMPLETED if hasattr(self, 'status') else None

    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle crop selection using traditional logic"""
        query = inputs.get("query", "")
        context = inputs.get("context", {})
        # Simplified soil loading: use provided soil data or fallback to empty dict
        soil = inputs.get("soil") or context.get("soil") or {}
        season = context.get("entities", {}).get("time_period") or inputs.get("season") or context.get("season") or "unknown"
        location = context.get("farm_location") or inputs.get("location") or "Punjab"
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
        # Real tools are now statics in services/tools.py and will be called dynamically

    async def _handle_internal_logic(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle crop selection using REAL TOOLS via services/tools.py."""
        context = inputs.get("context", {})
        location = context.get("farm_location") or inputs.get("location") or "Unknown Region"
        soil_data = context.get("soil_health") or context.get("soil") or inputs.get("soil") or {}
        season = context.get("entities", {}).get("time_period") or context.get("season") or inputs.get("season") or "Kharif"
        
        self.logger.info(f"CropSelectorAgent executing real tools for location: {location}, season: {season}")
        
        # 1. Get Climate Prediction
        climate_data = {}
        try:
            climate_data = await ClimatePredictionTool.predict_climate_conditions(location, season, 30)
        except Exception as e:
            self.logger.warning(f"ClimatePredictionTool failed: {e}")

        # 2. Get Initial Recommendations via LLM Tool based on soil, location, season
        base_recs = {}
        try:
            base_recs = await CropTool.get_crop_recommendations(soil_data, location, season)
        except Exception as e:
            self.logger.warning(f"CropTool failed: {e}")
            
        # 3. If crops recommended, scrape market for the top crop
        top_crop = ""
        market_data = {}
        if base_recs and "recommended_crops" in base_recs:
            recs = base_recs["recommended_crops"]
            if recs and isinstance(recs, list) and len(recs) > 0:
                top_crop_info = recs[0]
                if isinstance(top_crop_info, dict):
                    top_crop = top_crop_info.get("name", str(top_crop_info))
                else:
                    top_crop = str(top_crop_info)
                    
                self.logger.info(f"Top crop recommended: {top_crop}. Scraping market data.")
                try:
                    market_data = await WebScrapingTool.scrape_market_data(top_crop, location)
                except Exception as e:
                    self.logger.warning(f"WebScrapingTool failed: {e}")
                    
        # Synthesize final output
        final_prompt = f"""
        You are the Crop Selector Agent. Synthesize the final comprehensive response to the user based on the real-time data gathered from our tools.
        
        User Query: {inputs.get("query", "What crops should I plant?")}
        
        Tool 1: Crop Recommendations Tool Output:
        {json.dumps(base_recs, indent=2)}
        
        Tool 2: Climate Prediction Tool Output:
        {json.dumps(climate_data, indent=2)}
        
        Tool 3: Real-Time Market Scraping Output for top crop ({top_crop}):
        {json.dumps(market_data, indent=2)}
        
        Synthesize a final json response with:
        1. "recommended_crops": List of top 3 crops.
        2. "response": A natural paragraph explaining the main recommendation integrating climate and market conditions.
        3. "recommendations": Concrete next steps.
        4. "warnings": Any risks from market or climate.
        """
        
        try:
            from farmxpert.services.gemini_service import gemini_service
            synthesized = await gemini_service.generate_response(final_prompt, {"task": "crop_selector_synthesis"})
            parsed = gemini_service._parse_json_response(synthesized)
            
            return {
                "agent": self.name,
                "success": True,
                "response": parsed.get("response", f"Based on conditions, we recommend {top_crop}."),
                "recommendations": parsed.get("recommendations", []),
                "warnings": parsed.get("warnings", []),
                "next_steps": parsed.get("recommendations", []),
                "data": parsed,
                "metadata": {
                    "mode": "real_tools_orchestration",
                    "tools_used": ["CropTool", "ClimatePredictionTool", "WebScrapingTool"]
                }
            }
        except Exception as e:
            self.logger.error(f"Synthesis failed: {e}")
            raise
    
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


