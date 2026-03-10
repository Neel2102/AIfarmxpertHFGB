from typing import Dict, Any, List, Optional
import random
import logging

logger = logging.getLogger(__name__)

class YieldEngineTool:
    """
    Tool to predict crop yields using a simulated Machine Learning model.
    In a real system, this would load a pickled Scikit-learn/TensorFlow model.
    """
    
    def predict_yield(self, crop: str, acreage: float, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict yield based on crop type, acreage, soil health, and weather inputs.
        """
        try:
            # Simulate ML model inference
            # Factors: Soil Health (0-1), Weather Favorability (0-1), Input Quality (0-1)
            
            soil_score = self._calculate_soil_score(inputs.get("soil_data", {}))
            weather_score = self._calculate_weather_score(inputs.get("weather_data", {}))
            input_efficiency = 0.9 # Assume high efficiency for standard inputs
            
            # Base yield averages (tons per acre) - approx Indian context
            base_yields = {
                "wheat": 1.8,
                "rice": 2.2,
                "maize": 2.5,
                "cotton": 0.8,
                "sugarcane": 30.0,
                "groundnut": 0.8
            }
            
            base = base_yields.get(crop.lower(), 1.5)
            
            # Predictive formula: Base * (Weights of factors) + Random Variance
            predicted_per_acre = base * (0.4 * soil_score + 0.4 * weather_score + 0.2 * input_efficiency)
            
            # Add small random variance for realism (+/- 10%)
            variance = random.uniform(0.9, 1.1)
            final_yield_per_acre = round(predicted_per_acre * variance, 2)
            
            total_yield = round(final_yield_per_acre * acreage, 2)
            
            confidence = round(0.75 + (0.1 * soil_score), 2)  # Higher soil score = better data = higher confidence
            
            return {
                "success": True,
                "crop": crop,
                "acreage": acreage,
                "predicted_yield_tons": total_yield,
                "yield_per_acre": final_yield_per_acre,
                "unit": "tons",
                "confidence_score": confidence,
                "factors": {
                    "soil_health_impact": "Positive" if soil_score > 0.7 else "Neutral",
                    "weather_impact": "Positive" if weather_score > 0.7 else "Negative"
                }
            }
            
        except Exception as e:
            logger.error(f"Error predicting yield: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_soil_score(self, soil: Dict[str, Any]) -> float:
        """Normalize soil data to 0-1 score"""
        if not soil: return 0.5
        
        score = 0.5
        # Ideal pH check (6.0 - 7.5)
        ph = soil.get("ph", 7.0)
        if 6.0 <= ph <= 7.5:
            score += 0.2
        elif ph < 5.5 or ph > 8.5:
            score -= 0.1
            
        # Organic matter check (>1.5 is good)
        om = soil.get("organic_matter", 1.0)
        if om > 1.5:
            score += 0.2
            
        return min(max(score, 0.1), 1.0)

    def _calculate_weather_score(self, weather: Dict[str, Any]) -> float:
        """Normalize weather data to 0-1 score"""
        if not weather: return 0.8 # Assume decent weather if unknown
        
        # Simple simulation: if "rain" key is high, might be good or bad depending on crop
        # For simplicity, returning a high default score modified by random 'seasonal' risk
        base = 0.8
        if random.random() > 0.8: # 20% chance of bad weather event reducing score
            base -= 0.3
            
        return base
