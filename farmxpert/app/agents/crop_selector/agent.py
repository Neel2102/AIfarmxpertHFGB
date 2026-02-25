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

Always provide practical, actionable recommendations with clear reasoning.

CRITICAL: If the user asks about anything unrelated to Crop Selection, politely refuse and state that your expertise is limited to Crop Selection."""

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

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle crop selection using internal deterministic crop selector with fallback."""
        try:
            # Kept the import path to original location as we are not moving the pkg yet
            from farmxpert.agents.crop_planning.crop_selector_pkg.agents.json_crop_selector import JSONCropSelector

            context = inputs.get("context") or {}
            location = context.get("farm_location") or context.get("location") or inputs.get("location") or {}
            if isinstance(location, str):
                location = {"state": context.get("state") or "", "district": context.get("district") or ""}
            if not isinstance(location, dict):
                location = {}

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
                "weather_watcher": context.get("weather_watcher") or context.get("weather") or {},
                "soil_health": context.get("soil_health") or context.get("soil") or context.get("soil_data") or {},
                "irrigation_planner": context.get("irrigation_planner") or context.get("irrigation") or {},
                "market_intelligence": context.get("market_intelligence") or context.get("market") or {},
                "fertilizer_agent": context.get("fertilizer_agent") or context.get("fertilizer") or {},
            }

            selector = JSONCropSelector()
            reco = selector.select_crop_from_json(agent_inputs)
            data = reco.get("recommendation") if isinstance(reco, dict) else None

            recommendations: List[str] = []
            if isinstance(data, dict) and data.get("crop"):
                recommendations.append(f"Recommended crop: {data['crop']}")
            next_steps = []
            if isinstance(reco, dict) and isinstance(reco.get("next_steps"), list):
                next_steps = [str(x) for x in reco.get("next_steps")[:5]]

            crop_name = data.get("crop") if isinstance(data, dict) else None
            detailed = reco.get("detailed_reasoning") if isinstance(reco, dict) else None
            reasons: List[str] = []
            if isinstance(detailed, dict):
                for k in ("weather_impact", "soil_impact", "water_impact", "market_impact", "fertilizer_impact"):
                    v = detailed.get(k)
                    if isinstance(v, str) and v.strip():
                        reasons.append(v.strip())

            response_parts: List[str] = []
            if crop_name:
                response_parts.append(f"I recommend {crop_name} for this season.")
            else:
                response_parts.append("I can suggest crops for this season, but I need a bit more detail.")

            if reasons:
                response_parts.append("Reasons:")
                for r in reasons[:3]:
                    response_parts.append(f"- {r}")

            if next_steps:
                response_parts.append("Next steps:")
                for s in next_steps[:3]:
                    response_parts.append(f"- {s}")

            response_text = "\n".join(response_parts).strip()

            return {
                "agent": self.name,
                "success": True,
                "response": response_text,
                "recommendations": recommendations,
                "warnings": [],
                "next_steps": next_steps,
                "data": reco,
                "metadata": {"mode": "internal_crop_selector"},
            }
        except Exception as e:
            self.logger.error(f"Internal CropSelector failed: {e}")
            # Fallback to traditional logic
            return await self._handle_traditional(inputs)
    
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
