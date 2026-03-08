"""
Crop Selector Agent - AI decision-orchestrator for Indian small and marginal farmers
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Season(Enum):
    KHARIF = "Kharif"
    RABI = "Rabi"
    ZAID = "Zaid"


@dataclass
class FarmerContext:
    location: Dict[str, str]  # {"state": "", "district": ""}
    season: str
    land_size_acre: float
    risk_preference: str  # "Low" | "Medium" | "High"


@dataclass
class WeatherOutput:
    monsoon_onset: str  # "Early" | "Normal" | "Delayed"
    rainfall_outlook: str  # "Below" | "Normal" | "Above"
    dry_spell_risk: str  # "Low" | "Medium" | "High"
    heat_stress_risk: str  # "Low" | "Medium" | "High"


@dataclass
class SoilOutput:
    soil_type: str  # "Sandy" | "Loamy" | "Clay"
    fertility: str  # "Low" | "Medium" | "High"
    water_holding: str  # "Low" | "Medium" | "High"


@dataclass
class WaterOutput:
    water_availability: str  # "Low" | "Medium" | "High"
    irrigation_reliability: str  # "Poor" | "Moderate" | "Good"


@dataclass
class PestOutput:
    regional_pest_pressure: str  # "Low" | "Medium" | "High"
    high_risk_crops: List[str]
    alerts: List[str]


@dataclass
class MarketOutput:
    price_stability: Dict[str, str]  # crop -> "Low" | "Medium" | "High"
    msp_supported_crops: List[str]
    volatility_risk: str  # "Low" | "Medium" | "High"


@dataclass
class GovernmentOutput:
    insurance_supported_crops: List[str]
    subsidy_favored_crops: List[str]


@dataclass
class CropScore:
    crop_name: str
    overall_score: float
    weather_score: float
    water_score: float
    soil_score: float
    market_score: float
    pest_score: float
    category: str  # "Safest", "Balanced", "Higher Risk"


class CropSelectorAgent:
    """
    CropSelectorAgent - AI decision-orchestrator designed for Indian small and marginal farmers.
    Selects and recommends suitable crops by integrating outputs from specialized agents.
    """
    
    def __init__(self):
        # Import crop requirements from data
        from .crop_requirements import CROP_REQUIREMENTS, SEASONAL_CROPS, RISK_WEIGHTS, QUALITATIVE_SCORES
        self.crop_requirements = CROP_REQUIREMENTS
        self.crop_database = SEASONAL_CROPS
        self.weights = RISK_WEIGHTS
        self.qualitative_scores = QUALITATIVE_SCORES

    def _convert_to_score(self, qualitative: str) -> float:
        """Convert qualitative risk/suitability to numeric score"""
        return self.qualitative_scores.get(qualitative, 0.6)

    def _get_weather_suitability(self, crop: str, weather: WeatherOutput) -> float:
        """Calculate weather suitability score for a crop"""
        # Simplified logic - in production, this would be more sophisticated
        if crop in ["Paddy", "Cotton", "Sugarcane"] and weather.rainfall_outlook == "Below":
            return 0.3
        elif crop in ["Pearl Millet", "Sorghum", "Green Gram", "Black Gram", "Pigeon Pea", "Chickpea", "Lentil", "Groundnut", "Mustard", "Sesame"] and weather.rainfall_outlook == "Below":
            return 0.9
        elif weather.rainfall_outlook == "Normal":
            return 0.6
        elif weather.rainfall_outlook == "Above":
            return 0.9
        return 0.6

    def _get_water_suitability(self, crop: str, water: WaterOutput) -> float:
        """Calculate water availability suitability score"""
        crop_water_need = self.crop_requirements.get(crop, {}).get("water", "Medium")
        water_available = water.water_availability
        
        # High water need + Low availability = Poor match
        if crop_water_need == "High" and water_available == "Low":
            return 0.3
        # Low water need + Low availability = Good match
        elif crop_water_need == "Low" and water_available == "Low":
            return 0.9
        # High water need + High availability = Good match
        elif crop_water_need == "High" and water_available == "High":
            return 0.9
        # Medium water need + Medium availability = Good match
        elif crop_water_need == "Medium" and water_available == "Medium":
            return 0.6
        
        return 0.6

    def _get_soil_suitability(self, crop: str, soil: SoilOutput) -> float:
        """Calculate soil compatibility score"""
        crop_soil_pref = self.crop_requirements.get(crop, {}).get("soil", "Loamy")
        actual_soil = soil.soil_type
        
        if crop_soil_pref == actual_soil:
            return 0.9
        elif crop_soil_pref == "Loamy" and actual_soil in ["Sandy", "Clay"]:
            return 0.6
        elif actual_soil == "Loamy":
            return 0.6
        else:
            return 0.3

    def _get_market_suitability(self, crop: str, market: MarketOutput) -> float:
        """Calculate market stability score"""
        # Check if crop has MSP support
        if crop in market.msp_supported_crops:
            return 0.9
        
        # Check price stability
        price_stability = market.price_stability.get(crop, "Medium")
        return self._convert_to_score(price_stability)

    def _get_pest_suitability(self, crop: str, pest: PestOutput) -> float:
        """Calculate pest risk score (higher is better, so invert risk)"""
        if crop in pest.high_risk_crops:
            return 0.3
        
        pest_pressure = pest.regional_pest_pressure
        if pest_pressure == "Low":
            return 0.9
        elif pest_pressure == "Medium":
            return 0.6
        else:  # High
            return 0.3

    def _calculate_crop_score(self, crop: str, weather: WeatherOutput, 
                            soil: SoilOutput, water: WaterOutput, 
                            pest: PestOutput, market: MarketOutput) -> CropScore:
        """Calculate comprehensive score for a crop"""
        weather_score = self._get_weather_suitability(crop, weather)
        water_score = self._get_water_suitability(crop, water)
        soil_score = self._get_soil_suitability(crop, soil)
        market_score = self._get_market_suitability(crop, market)
        pest_score = self._get_pest_suitability(crop, pest)
        
        overall_score = (
            weather_score * self.weights["weather"] +
            water_score * self.weights["water"] +
            soil_score * self.weights["soil"] +
            market_score * self.weights["market"] +
            pest_score * self.weights["pest"]
        )
        
        # Categorize based on score
        if overall_score >= 0.70:
            category = "Safest"
        elif overall_score >= 0.55:
            category = "Balanced"
        else:
            category = "Higher Risk"
        
        return CropScore(
            crop_name=crop,
            overall_score=overall_score,
            weather_score=weather_score,
            water_score=water_score,
            soil_score=soil_score,
            market_score=market_score,
            pest_score=pest_score,
            category=category
        )

    def _apply_hard_constraints(self, crop: str, weather: WeatherOutput,
                               soil: SoilOutput, water: WaterOutput,
                               pest: PestOutput) -> bool:
        """Apply hard constraints to eliminate unsuitable crops"""
        # High water need crops under water scarcity
        crop_water_need = self.crop_requirements.get(crop, {}).get("water", "Medium")
        if crop_water_need == "High" and water.water_availability == "Low":
            return False
        
        # High pest risk crops
        if crop in pest.high_risk_crops and pest.regional_pest_pressure == "High":
            return False
        
        # Soil incompatibility
        crop_soil_pref = self.crop_requirements.get(crop, {}).get("soil", "Loamy")
        if crop_soil_pref == "Clay" and soil.soil_type == "Sandy":
            return False
        if crop_soil_pref == "Sandy" and soil.soil_type == "Clay":
            return False
        
        return True

    def select_crops(self, farmer_context: FarmerContext,
                    weather: WeatherOutput, soil: SoilOutput,
                    water: WaterOutput, pest: PestOutput,
                    market: MarketOutput, government: Optional[GovernmentOutput] = None) -> Dict:
        """
        Main method to select and recommend crops
        
        Args:
            farmer_context: Farmer's location, season, land size, risk preference
            weather: Weather agent output
            soil: Soil agent output
            water: Water/groundwater agent output
            pest: Pest & disease agent output
            market: Market agent output
            government: Government scheme agent output (optional)
        
        Returns:
            Dictionary with crop recommendations in the specified format
        """
        
        # Step 1: Generate candidate crops
        candidate_crops = self.crop_database.get(farmer_context.season, [])
        
        # Step 2: Apply hard constraints
        viable_crops = []
        for crop in candidate_crops:
            if self._apply_hard_constraints(crop, weather, soil, water, pest):
                viable_crops.append(crop)
        
        # Step 3: Risk-weighted scoring
        scored_crops = []
        for crop in viable_crops:
            score = self._calculate_crop_score(crop, weather, soil, water, pest, market)
            scored_crops.append(score)
        
        # Sort by overall score
        scored_crops.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Step 4: Categorize crops (already done in scoring)
        
        # Step 5: Select final recommendations
        recommendations = {
            "safest": [],
            "balanced": [],
            "higher_risk": [],
            "avoid": []
        }
        
        for score in scored_crops:
            if score.category == "Safest" and len(recommendations["safest"]) < 2:
                recommendations["safest"].append(score)
            elif score.category == "Balanced" and len(recommendations["balanced"]) < 2:
                recommendations["balanced"].append(score)
            elif score.category == "Higher Risk" and len(recommendations["higher_risk"]) < 1:
                recommendations["higher_risk"].append(score)
        
        # Crops to avoid (low scoring or eliminated by constraints)
        all_candidate_scores = {crop.crop_name: crop for crop in scored_crops}
        for crop in candidate_crops:
            if crop not in all_candidate_scores:
                recommendations["avoid"].append({
                    "crop": crop,
                    "reason": "Failed hard constraints (water/pest/soil incompatibility)"
                })
            elif all_candidate_scores[crop].overall_score < 0.4:
                recommendations["avoid"].append({
                    "crop": crop,
                    "reason": f"Low overall score ({all_candidate_scores[crop].overall_score:.2f})"
                })
        
        # Generate final response
        return self._format_response(farmer_context, weather, soil, water, pest, market, government, recommendations, scored_crops)

    def _format_response(self, farmer_context: FarmerContext, weather: WeatherOutput,
                        soil: SoilOutput, water: WaterOutput, pest: PestOutput,
                        market: MarketOutput, government: Optional[GovernmentOutput],
                        recommendations: Dict, scored_crops: List[CropScore]) -> Dict:
        """Format the response according to the specified structure"""
        
        # Calculate overall season risk
        risk_factors = [
            self._convert_to_score(weather.dry_spell_risk),
            self._convert_to_score(weather.heat_stress_risk),
            1 - self._convert_to_score(water.water_availability),  # Invert water availability
            self._convert_to_score(pest.regional_pest_pressure),
            self._convert_to_score(market.volatility_risk)
        ]
        overall_risk = sum(risk_factors) / len(risk_factors)
        
        if overall_risk <= 0.4:
            risk_level = "Low"
            risk_explanation = "Favorable conditions expected this season"
        elif overall_risk <= 0.7:
            risk_level = "Medium"
            risk_explanation = "Some challenges expected, careful planning needed"
        else:
            risk_level = "High"
            risk_explanation = "Challenging conditions, prioritize risk mitigation"
        
        # Build response
        response = {
            "situation": f"Farmer in {farmer_context.location['district']}, {farmer_context.location['state']} with {farmer_context.land_size_acre} acres for {farmer_context.season} season. Risk preference: {farmer_context.risk_preference}",
            "season_risk": {
                "level": risk_level,
                "explanation": risk_explanation
            },
            "recommendations": {
                "safest": [],
                "balanced": [],
                "higher_risk": []
            },
            "avoid": recommendations["avoid"],
            "reasoning": {
                "rainfall": weather.rainfall_outlook,
                "water": water.water_availability,
                "soil": soil.soil_type,
                "market": f"MSP support for {len(market.msp_supported_crops)} crops",
                "pest": pest.regional_pest_pressure
            },
            "next_steps": [
                "Select quality seeds from authorized dealers",
                f"Prepare land based on {soil.soil_type} soil requirements",
                "Arrange irrigation in advance if needed",
                "Stay updated on weather forecasts"
            ],
            "assumptions": "Standard farming practices assumed. Local variations may apply.",
            "confidence": "High" if len(scored_crops) > 5 else "Medium"
        }
        
        # Add crop recommendations
        for crop_score in recommendations["safest"]:
            response["recommendations"]["safest"].append({
                "crop": crop_score.crop_name,
                "score": round(crop_score.overall_score, 2),
                "why": f"Well-suited to current {weather.rainfall_outlook} rainfall and {soil.soil_type} soil"
            })
        
        for crop_score in recommendations["balanced"]:
            response["recommendations"]["balanced"].append({
                "crop": crop_score.crop_name,
                "score": round(crop_score.overall_score, 2),
                "trade_off": "Moderate risk with reasonable returns"
            })
        
        for crop_score in recommendations["higher_risk"]:
            response["recommendations"]["higher_risk"].append({
                "crop": crop_score.crop_name,
                "score": round(crop_score.overall_score, 2),
                "warning": "Higher risk but potentially better returns"
            })
        
        return response

    def get_advice_text(self, farmer_context: FarmerContext,
                       weather: WeatherOutput, soil: SoilOutput,
                       water: WaterOutput, pest: PestOutput,
                       market: MarketOutput, government: Optional[GovernmentOutput] = None) -> str:
        """Get formatted advice as text"""
        response = self.select_crops(farmer_context, weather, soil, water, pest, market, government)
        
        advice = f"""
### 🌾 Crop Selection Advice

#### 1️⃣ Your Situation
{response['situation']}

#### 2️⃣ Overall Season Risk
{response['season_risk']['level']}
{response['season_risk']['explanation']}

#### 3️⃣ Recommended Crop Options
"""
        
        if response['recommendations']['safest']:
            advice += "\n**🟢 Safest Option**\n"
            for crop in response['recommendations']['safest']:
                advice += f"* {crop['crop']} (Score: {crop['score']})\n"
                advice += f"  {crop['why']}\n"
        
        if response['recommendations']['balanced']:
            advice += "\n**🟡 Balanced Option**\n"
            for crop in response['recommendations']['balanced']:
                advice += f"* {crop['crop']} (Score: {crop['score']})\n"
                advice += f"  {crop['trade_off']}\n"
        
        if response['recommendations']['higher_risk']:
            advice += "\n**🔴 Higher-Return but Risky**\n"
            for crop in response['recommendations']['higher_risk']:
                advice += f"* {crop['crop']} (Score: {crop['score']})\n"
                advice += f"  {crop['warning']}\n"
        
        advice += f"\n#### 4️⃣ Crops to Avoid\n"
        for crop in response['avoid']:
            advice += f"* {crop['crop']}: {crop['reason']}\n"
        
        advice += f"\n#### 5️⃣ Why These Recommendations\n"
        reasoning = response['reasoning']
        advice += f"* Rainfall: {reasoning['rainfall']}\n"
        advice += f"* Water: {reasoning['water']}\n"
        advice += f"* Soil: {reasoning['soil']}\n"
        advice += f"* Market: {reasoning['market']}\n"
        advice += f"* Pest risk: {reasoning['pest']}\n"
        
        advice += f"\n#### 6️⃣ Next Steps\n"
        for step in response['next_steps']:
            advice += f"* {step}\n"
        
        advice += f"\n#### 7️⃣ Assumptions & Confidence\n"
        advice += f"* {response['assumptions']}\n"
        advice += f"* Confidence level: {response['confidence']}\n"
        
        return advice.strip()
