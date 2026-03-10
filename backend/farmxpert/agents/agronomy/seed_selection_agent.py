from __future__ import annotations
from typing import Dict, Any, List, Optional
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import GeneticDatabaseTool, SoilSuitabilityTool, YieldPredictionTool, MarketTool
from farmxpert.services.gemini_service import gemini_service


class SeedSelectionAgent(EnhancedBaseAgent):
    name = "seed_selection"
    description = "Suggests optimal seed varieties (hybrid, GMO, traditional) tailored to crop choice and farmer goals"

    def _get_system_prompt(self) -> str:
        return """You are a Seed Selection Agent specializing in recommending the best seed varieties for farmers.

Your expertise includes:
- Genetic characteristics of different seed varieties
- Soil suitability for specific varieties
- Yield potential analysis
- Disease and pest resistance
- Market preferences and pricing
- Climate adaptability

Always provide practical, data-driven recommendations with clear reasoning."""

    def _get_examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "What are the best wheat varieties for high yield in ahmedabad?",
                "output": "For high yield wheat in ahmedabad, I recommend HD-3086 (Hybrid, 65-70 q/ha) and PBW-723 (Hybrid, 60-65 q/ha). These varieties are well-suited for ahmedabad's climate and soil conditions."
            },
            {
                "input": "Which rice varieties are disease resistant for Tamil Nadu?",
                "output": "For disease-resistant rice in Tamil Nadu, consider ADT-43 (Traditional, resistant to blast) and CO-51 (Hybrid, resistant to bacterial blight). Both perform well in Tamil Nadu's conditions."
            }
        ]

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle seed selection using dynamic tools and comprehensive analysis"""
        try:
            # Get tools from inputs
            tools = inputs.get("tools", {})
            context = inputs.get("context", {})
            query = inputs.get("query", "")
            
            # Extract parameters
            crop = self._extract_crop_from_query(query) or context.get("crop", "wheat")
            location = context.get("farm_location", inputs.get("location", "unknown"))
            goals = context.get("preferences", {}).get("goal", "high_yield")
            budget = context.get("preferences", {}).get("budget", "medium")
            soil_data = context.get("soil_data", {})
            
            # Initialize data containers
            genetic_data = {}
            soil_suitability_data = {}
            yield_prediction_data = {}
            market_data = {}
            
            # Get genetic database information
            if "genetic_database" in tools:
                try:
                    genetic_data = await tools["genetic_database"].query_seed_varieties(crop, location)
                except Exception as e:
                    self.logger.warning(f"Failed to get genetic data: {e}")
            
            # Get soil suitability analysis
            if "soil_suitability" in tools and soil_data:
                try:
                    # Get top varieties from genetic data for soil analysis
                    top_varieties = genetic_data.get("popular_varieties", [])[:3]
                    for variety in top_varieties:
                        if isinstance(variety, dict) and "name" in variety:
                            variety_name = variety["name"]
                            soil_analysis = await tools["soil_suitability"].assess_soil_suitability(
                                soil_data, crop, variety_name
                            )
                            soil_suitability_data[variety_name] = soil_analysis
                except Exception as e:
                    self.logger.warning(f"Failed to get soil suitability data: {e}")
            
            # Get yield predictions
            if "yield_prediction" in tools:
                try:
                    weather_data = context.get("weather_data", {})
                    top_varieties = genetic_data.get("popular_varieties", [])[:2]
                    for variety in top_varieties:
                        if isinstance(variety, dict) and "name" in variety:
                            variety_name = variety["name"]
                            yield_data = await tools["yield_prediction"].predict_crop_yield(
                                crop, variety_name, soil_data, weather_data, location
                            )
                            yield_prediction_data[variety_name] = yield_data
                except Exception as e:
                    self.logger.warning(f"Failed to get yield prediction data: {e}")
            
            # Get market information
            if "market" in tools:
                try:
                    market_data = await tools["market"].get_current_prices(crop, location)
                except Exception as e:
                    self.logger.warning(f"Failed to get market data: {e}")
            
            # Build comprehensive prompt for Gemini
            prompt = f"""
You are an expert seed selection specialist. Based on the following comprehensive analysis, recommend the best seed varieties for the farmer.

Farmer's Query: "{query}"

Analysis Results:
- Crop: {crop}
- Location: {location}
- Goals: {goals}
- Budget: {budget}
- Genetic Data: {genetic_data.get('popular_varieties', [])}
- Soil Suitability: {list(soil_suitability_data.keys())}
- Yield Predictions: {list(yield_prediction_data.keys())}
- Market Data: {market_data.get('current_prices', {})}

Provide 3 seed variety recommendations with detailed reasoning, including:
1. Variety name and type (GMO/Hybrid/Traditional)
2. Expected yield potential
3. Soil suitability score
4. Disease resistance traits
5. Cost and availability
6. Market demand
7. Specific advantages for the farmer's conditions

Format your response as a natural conversation with the farmer.
"""

            response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "seed_selection"})

            # If LLM quota/rate limit is hit, fall back to deterministic output
            resp_lower = (response or "").lower()
            if "429" in resp_lower or "quota" in resp_lower or "rate limit" in resp_lower:
                return await self._handle_traditional(inputs)
            
            return {
                "agent": self.name,
                "success": True,
                "response": response,
                "data": {
                    "crop": crop,
                    "location": location,
                    "goals": goals,
                    "budget": budget,
                    "genetic_data": genetic_data,
                    "soil_suitability_data": soil_suitability_data,
                    "yield_prediction_data": yield_prediction_data,
                    "market_data": market_data
                },
                "recommendations": self._extract_recommendations_from_data(genetic_data, soil_suitability_data, yield_prediction_data),
                "warnings": self._extract_warnings_from_data(soil_suitability_data, yield_prediction_data),
                "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
            }
            
        except Exception as e:
            self.logger.error(f"Error in seed selection agent: {e}")
            # Fallback to traditional method
            return await self._handle_traditional(inputs)
    
    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback traditional seed selection method"""
        context = inputs.get("context", {})
        crop = inputs.get("entities", {}).get("crop") or inputs.get("crop", "wheat")
        goals = context.get("preferences", {}).get("goal", "high_yield")
        budget = context.get("preferences", {}).get("budget", "medium")
        location = context.get("farm_location", inputs.get("location", "unknown"))
        
        # Basic seed variety recommendations
        seed_recommendations = {
            "wheat": {
                "high_yield": [
                    {"variety": "HD-3086", "type": "Hybrid", "yield_potential": "65-70 q/ha", "price": "₹2800/bag"},
                    {"variety": "PBW-723", "type": "Hybrid", "yield_potential": "60-65 q/ha", "price": "₹2600/bag"}
                ],
                "disease_resistant": [
                    {"variety": "HD-2967", "type": "Traditional", "yield_potential": "55-60 q/ha", "price": "₹1800/bag"},
                    {"variety": "PBW-550", "type": "Traditional", "yield_potential": "50-55 q/ha", "price": "₹1600/bag"}
                ]
            },
            "rice": {
                "high_yield": [
                    {"variety": "Pusa-1121", "type": "Hybrid", "yield_potential": "45-50 q/ha", "price": "₹3200/bag"},
                    {"variety": "PR-126", "type": "Hybrid", "yield_potential": "40-45 q/ha", "price": "₹3000/bag"}
                ]
            },
            "maize": {
                "high_yield": [
                    {"variety": "Pioneer-3396", "type": "GMO", "yield_potential": "80-85 q/ha", "price": "₹4500/bag"},
                    {"variety": "DKC-9141", "type": "Hybrid", "yield_potential": "75-80 q/ha", "price": "₹4200/bag"}
                ]
            }
        }
        
        recommendations = seed_recommendations.get(crop, {}).get(goals, [])
        
        # Filter by budget
        if budget == "low":
            recommendations = [r for r in recommendations if r["price"] < "₹2500"]
        elif budget == "high":
            recommendations = [r for r in recommendations if r["price"] > "₹3000"]
        
        response = f"Seed recommendations for {crop} in {location}: {', '.join([r['variety'] for r in recommendations[:3]])}"
        
        return {
            "agent": self.name,
            "success": True,
            "response": response,
            "recommendations": recommendations,
            "data": {"crop": crop, "location": location, "goal": goals, "budget": budget},
            "metadata": {"model": "traditional"}
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
    
    def _extract_recommendations_from_data(self, genetic_data: Dict[str, Any], soil_data: Dict[str, Any], yield_data: Dict[str, Any]) -> List[str]:
        """Extract recommendations from analysis data"""
        recommendations = []
        
        if isinstance(genetic_data, dict) and "popular_varieties" in genetic_data:
            varieties = genetic_data["popular_varieties"]
            if isinstance(varieties, list) and varieties:
                recommendations.append(f"Consider these varieties: {', '.join([v.get('name', str(v)) for v in varieties[:3]])}")
        
        if isinstance(soil_data, dict):
            for variety, data in soil_data.items():
                if isinstance(data, dict) and "suitability_score" in data:
                    score = data["suitability_score"]
                    if isinstance(score, (int, float)) and score > 80:
                        recommendations.append(f"{variety} has excellent soil suitability (score: {score})")
        
        return recommendations
    
    def _extract_warnings_from_data(self, soil_data: Dict[str, Any], yield_data: Dict[str, Any]) -> List[str]:
        """Extract warnings from analysis data"""
        warnings = []
        
        if isinstance(soil_data, dict):
            for variety, data in soil_data.items():
                if isinstance(data, dict) and "suitability_score" in data:
                    score = data["suitability_score"]
                    if isinstance(score, (int, float)) and score < 60:
                        warnings.append(f"{variety} has low soil suitability (score: {score})")
        
        if isinstance(yield_data, dict):
            for variety, data in yield_data.items():
                if isinstance(data, dict) and "risk_factors" in data:
                    risks = data["risk_factors"]
                    if isinstance(risks, list) and risks:
                        warnings.append(f"{variety} has yield risks: {', '.join(risks[:2])}")
        
        return warnings
