from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json

from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent

try:
    import numpy as np
    import pandas as pd
    from catboost import CatBoostRegressor
except Exception:  # pragma: no cover
    np = None
    pd = None
    CatBoostRegressor = None


_CACHED_MODEL: Optional["CatBoostRegressor"] = None
_CACHED_FEATURE_COLS: Optional[List[str]] = None
_CACHED_CFG: Optional[Dict[str, Any]] = None
_CACHED_DISTRICT_FREQ: Optional[Dict[str, float]] = None


def _external_artifacts_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    base = repo_root / "yield_predictor_agent" / "models"

    for d in ("artifacts", "artifacts_raw", "artifacts_freq"):
        cand = base / d
        if (cand / "catboost_yield_model.cbm").exists() and (cand / "model_metadata.json").exists():
            return cand
    return base / "artifacts"


def _load_model() -> None:
    global _CACHED_MODEL, _CACHED_FEATURE_COLS, _CACHED_CFG, _CACHED_DISTRICT_FREQ
    if _CACHED_MODEL is not None:
        return

    if CatBoostRegressor is None or pd is None or np is None:
        raise RuntimeError("Yield predictor dependencies missing (catboost/pandas/numpy)")

    artifacts_dir = _external_artifacts_dir()
    meta_path = artifacts_dir / "model_metadata.json"
    model_path = artifacts_dir / "catboost_yield_model.cbm"

    with meta_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    feature_cols = meta.get("feature_cols")
    if not isinstance(feature_cols, list) or not feature_cols:
        raise ValueError("model_metadata.json missing feature_cols")

    model = CatBoostRegressor()
    model.load_model(str(model_path))

    _CACHED_MODEL = model
    _CACHED_FEATURE_COLS = [str(x) for x in feature_cols]
    _CACHED_CFG = meta.get("config") if isinstance(meta.get("config"), dict) else {}
    _CACHED_DISTRICT_FREQ = meta.get("district_freq_map") if isinstance(meta.get("district_freq_map"), dict) else None


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ["State_Name", "District_Name", "Crop", "Season", "Crop_Year", "Area"]
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    out: Dict[str, Any] = {}
    out["State_Name"] = str(payload.get("State_Name") or "Unknown")
    out["District_Name"] = str(payload.get("District_Name") or "Unknown")
    out["Crop"] = str(payload.get("Crop") or "Unknown")
    out["Season"] = str(payload.get("Season") or "Unknown")
    out["Crop_Year"] = int(payload.get("Crop_Year"))
    out["Area"] = float(payload.get("Area"))
    if out["Area"] <= 0:
        raise ValueError("Area must be > 0")
    if "Production" in payload:
        raise ValueError("Production must not be provided as an input feature")
    return out


def _to_features_df(normalized: Dict[str, Any]) -> "pd.DataFrame":
    _load_model()
    assert _CACHED_FEATURE_COLS is not None

    row = dict(normalized)
    district_encoding = str((_CACHED_CFG or {}).get("district_encoding", "raw"))
    if district_encoding == "freq":
        freq_map = _CACHED_DISTRICT_FREQ or {}
        row["District_Freq"] = float(freq_map.get(str(row.get("District_Name")), 0.0))

    df = pd.DataFrame([row])
    for c in ("State_Name", "District_Name", "Crop", "Season"):
        if c in df.columns:
            df[c] = df[c].astype("string").fillna("Unknown")

    return df[_CACHED_FEATURE_COLS]


def predict_yield(payload: Dict[str, Any]) -> Dict[str, Any]:
    _load_model()
    assert _CACHED_MODEL is not None

    normalized = _normalize_payload(payload)
    X = _to_features_df(normalized)
    pred_fit = float(_CACHED_MODEL.predict(X)[0])

    log_target = bool((_CACHED_CFG or {}).get("log_target", False))
    pred = float(np.expm1(pred_fit)) if log_target else float(pred_fit)
    if not np.isfinite(pred) or pred < 0:
        pred = max(0.0, float(pred) if np.isfinite(pred) else 0.0)

    return {
        "predicted_yield": pred,
        "yield_unit_note": "Yield is typically tonnes/hectare; for Coconut, dataset production appears to be nuts, so yield may be nuts/hectare.",
        "inputs": normalized,
    }


class YieldPredictorAgent(EnhancedBaseAgent):
    name = "yield_predictor_agent"
    description = "Estimates crop yields using farm-specific historical data, agronomic variables, and forecast conditions"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            from farmxpert.tools.analytics.yield_engine import YieldEngineTool
            self.yield_engine = YieldEngineTool()
        except ImportError:
            self.yield_engine = None
            self.logger.warning("Could not import YieldEngineTool")

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Predict yield using YieldEngineTool (simulated ML) and reason with LLM."""
        context = inputs.get("context", {})
        
        # Extract parameters
        crop = context.get("crop") or inputs.get("crop") or "Wheat"
        area = context.get("area") or inputs.get("area") or 1.0
        
        # Prepare inputs for engine
        engine_inputs = {
            "soil_data": context.get("soil_data") or context.get("soil", {}),
            "weather_data": context.get("weather_data") or context.get("weather", {})
        }
        
        tool_data = {}
        if self.yield_engine:
            try:
                # Use the new tool
                result = self.yield_engine.predict_yield(str(crop), float(area), engine_inputs)
                if result.get("success"):
                    tool_data = result
                    # Explicitly format for the LLM to see
                    tool_data["summary"] = f"YieldEngine Prediction: {result.get('predicted_yield_tons')} tons of {crop} ({area} acres). Confidence: {result.get('confidence_score')}"
                else:
                    tool_data = {"error": "Yield prediction failed", "details": result.get("error")}
            except Exception as e:
                self.logger.error(f"YieldEngine failed: {e}")
                tool_data = {"error": f"YieldEngine exception: {str(e)}"}
        
        # INJECT TOOL DATA INTO LLM CONTEXT
        # This is the critical step for "Context-Awareness"
        inputs["additional_data"] = inputs.get("additional_data", {})
        inputs["additional_data"]["yield_prediction_tool_result"] = tool_data
        
        # Force LLM usage to generate the final response using the Persona
        return await self._handle_with_llm(inputs)
    
    def _predict_crop_yield(self, crop: str, soil_data: Dict, weather: Dict, 
                           historical: List[float], field_conditions: Dict, 
                           management: Dict) -> Dict[str, Any]:
        """Predict yield for a specific crop"""
        
        # Base yield potential for different crops (tons per acre)
        base_yields = {
            "wheat": 2.5,
            "maize": 3.0,
            "rice": 2.8,
            "pulses": 1.2,
            "cotton": 0.8,
            "sugarcane": 35.0,
            "soybeans": 1.8,
            "sunflower": 1.5
        }
        
        base_yield = base_yields.get(crop.lower(), 2.0)
        
        # Calculate yield adjustments based on various factors
        soil_adjustment = self._calculate_soil_adjustment(soil_data, crop)
        weather_adjustment = self._calculate_weather_adjustment(weather, crop)
        historical_adjustment = self._calculate_historical_adjustment(historical)
        field_adjustment = self._calculate_field_adjustment(field_conditions, crop)
        management_adjustment = self._calculate_management_adjustment(management, crop)
        
        # Calculate final yield prediction
        predicted_yield = base_yield * soil_adjustment * weather_adjustment * \
                         historical_adjustment * field_adjustment * management_adjustment
        
        # Calculate confidence score
        confidence = self._calculate_confidence_score(
            soil_data, weather, historical, field_conditions, management
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            soil_data, weather, field_conditions, management
        )
        
        return {
            "yield": round(predicted_yield, 2),
            "confidence": confidence,
            "risk_factors": risk_factors,
            "adjustments": {
                "soil": soil_adjustment,
                "weather": weather_adjustment,
                "historical": historical_adjustment,
                "field": field_adjustment,
                "management": management_adjustment
            }
        }
    
    def _calculate_soil_adjustment(self, soil_data: Dict, crop: str) -> float:
        """Calculate yield adjustment based on soil conditions"""
        adjustment = 1.0
        
        # pH adjustment
        ph = soil_data.get("ph", 7.0)
        if crop in ["wheat", "maize"]:
            if 6.0 <= ph <= 7.5:
                adjustment *= 1.1
            elif ph < 5.5 or ph > 8.0:
                adjustment *= 0.8
        
        # NPK adjustment
        npk = soil_data.get("npk", {})
        nitrogen = npk.get("nitrogen", 0)
        phosphorus = npk.get("phosphorus", 0)
        potassium = npk.get("potassium", 0)
        
        # Nitrogen adjustment
        if crop in ["maize", "wheat"]:
            if nitrogen >= 150:
                adjustment *= 1.2
            elif nitrogen < 50:
                adjustment *= 0.7
        
        # Phosphorus adjustment
        if phosphorus >= 30:
            adjustment *= 1.1
        elif phosphorus < 10:
            adjustment *= 0.8
        
        # Organic matter adjustment
        organic_matter = soil_data.get("organic_matter", 2.0)
        if organic_matter >= 3.0:
            adjustment *= 1.15
        elif organic_matter < 1.0:
            adjustment *= 0.85
        
        return round(adjustment, 3)
    
    def _calculate_weather_adjustment(self, weather: Dict, crop: str) -> float:
        """Calculate yield adjustment based on weather forecast"""
        adjustment = 1.0
        
        # Temperature adjustment
        avg_temp = weather.get("average_temperature", 25)
        if crop in ["wheat", "maize"]:
            if 20 <= avg_temp <= 30:
                adjustment *= 1.1
            elif avg_temp < 15 or avg_temp > 35:
                adjustment *= 0.8
        
        # Rainfall adjustment
        rainfall = weather.get("total_rainfall", 100)
        if crop in ["rice"]:
            if rainfall >= 150:
                adjustment *= 1.2
            elif rainfall < 80:
                adjustment *= 0.6
        elif crop in ["wheat", "maize"]:
            if 80 <= rainfall <= 120:
                adjustment *= 1.1
            elif rainfall < 50 or rainfall > 200:
                adjustment *= 0.8
        
        # Drought stress
        drought_days = weather.get("drought_days", 0)
        if drought_days > 30:
            adjustment *= 0.7
        elif drought_days > 15:
            adjustment *= 0.9
        
        return round(adjustment, 3)
    
    def _calculate_historical_adjustment(self, historical_yields: List[float]) -> float:
        """Calculate adjustment based on historical yield data"""
        if not historical_yields:
            return 1.0
        
        # Calculate trend
        if len(historical_yields) >= 3:
            recent_avg = sum(historical_yields[-3:]) / 3
            older_avg = sum(historical_yields[:-3]) / len(historical_yields[:-3]) if len(historical_yields) > 3 else recent_avg
            
            if recent_avg > older_avg:
                return 1.05  # Improving trend
            elif recent_avg < older_avg:
                return 0.95  # Declining trend
        
        return 1.0
    
    def _calculate_field_adjustment(self, field_conditions: Dict, crop: str) -> float:
        """Calculate adjustment based on field conditions"""
        adjustment = 1.0
        
        # Field slope
        slope = field_conditions.get("slope", "flat")
        if slope == "steep":
            adjustment *= 0.8
        elif slope == "moderate":
            adjustment *= 0.9
        
        # Drainage
        drainage = field_conditions.get("drainage", "good")
        if drainage == "poor":
            adjustment *= 0.85
        elif drainage == "excellent":
            adjustment *= 1.1
        
        # Field size efficiency
        field_size = field_conditions.get("field_size_acres", 10)
        if 5 <= field_size <= 20:
            adjustment *= 1.05  # Optimal field size
        elif field_size < 2:
            adjustment *= 0.9  # Too small for efficient operations
        
        # Erosion
        erosion = field_conditions.get("erosion", "low")
        if erosion == "high":
            adjustment *= 0.8
        elif erosion == "moderate":
            adjustment *= 0.9
        
        return round(adjustment, 3)
    
    def _calculate_management_adjustment(self, management: Dict, crop: str) -> float:
        """Calculate adjustment based on management practices"""
        adjustment = 1.0
        
        # Irrigation
        irrigation = management.get("irrigation", "rainfed")
        if irrigation == "drip":
            adjustment *= 1.15
        elif irrigation == "sprinkler":
            adjustment *= 1.1
        elif irrigation == "flood":
            adjustment *= 1.05
        
        # Fertilizer application
        fertilizer_timing = management.get("fertilizer_timing", "standard")
        if fertilizer_timing == "optimal":
            adjustment *= 1.1
        elif fertilizer_timing == "poor":
            adjustment *= 0.9
        
        # Pest management
        pest_management = management.get("pest_management", "conventional")
        if pest_management == "integrated":
            adjustment *= 1.05
        elif pest_management == "none":
            adjustment *= 0.8
        
        # Weed management
        weed_management = management.get("weed_management", "herbicide")
        if weed_management == "integrated":
            adjustment *= 1.05
        elif weed_management == "manual":
            adjustment *= 0.95
        
        # Crop rotation
        rotation = management.get("crop_rotation", False)
        if rotation:
            adjustment *= 1.1
        
        return round(adjustment, 3)
    
    def _calculate_confidence_score(self, soil_data: Dict, weather: Dict, 
                                  historical: List[float], field_conditions: Dict, 
                                  management: Dict) -> float:
        """Calculate confidence score for yield prediction"""
        confidence = 0.5  # Base confidence
        
        # Data availability factors
        if soil_data:
            confidence += 0.1
        if weather:
            confidence += 0.1
        if len(historical) >= 3:
            confidence += 0.15
        if field_conditions:
            confidence += 0.1
        if management:
            confidence += 0.05
        
        # Data quality factors
        if soil_data.get("ph") and soil_data.get("npk"):
            confidence += 0.1
        if weather.get("average_temperature") and weather.get("total_rainfall"):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _identify_risk_factors(self, soil_data: Dict, weather: Dict, 
                              field_conditions: Dict, management: Dict) -> List[str]:
        """Identify potential risk factors affecting yield"""
        risks = []
        
        # Soil risks
        ph = soil_data.get("ph", 7.0)
        if ph < 5.5 or ph > 8.0:
            risks.append("Suboptimal soil pH")
        
        npk = soil_data.get("npk", {})
        if npk.get("nitrogen", 0) < 50:
            risks.append("Low nitrogen levels")
        if npk.get("phosphorus", 0) < 10:
            risks.append("Low phosphorus levels")
        
        # Weather risks
        if weather.get("drought_days", 0) > 15:
            risks.append("Extended drought conditions")
        if weather.get("average_temperature", 25) > 35:
            risks.append("High temperature stress")
        
        # Field risks
        if field_conditions.get("drainage") == "poor":
            risks.append("Poor field drainage")
        if field_conditions.get("erosion") == "high":
            risks.append("High soil erosion")
        
        # Management risks
        if management.get("pest_management") == "none":
            risks.append("No pest management")
        if not management.get("crop_rotation", False):
            risks.append("No crop rotation")
        
        return risks
    
    def _generate_optimization_recommendations(self, yield_predictions: Dict, 
                                             risk_factors: Dict, 
                                             management: Dict) -> List[str]:
        """Generate recommendations to optimize yields"""
        recommendations = []
        
        # Identify low-yield crops
        if not yield_predictions:
            return ["No yield predictions available for optimization recommendations"]
        avg_yield = sum(yield_predictions.values()) / len(yield_predictions)
        for crop, yield_val in yield_predictions.items():
            if yield_val < avg_yield * 0.8:
                recommendations.append(f"Focus on improving {crop} yields through better management")
        
        # Address common risk factors
        all_risks = []
        for risks in risk_factors.values():
            all_risks.extend(risks)
        
        if "Low nitrogen levels" in all_risks:
            recommendations.append("Consider increasing nitrogen fertilizer application")
        if "Extended drought conditions" in all_risks:
            recommendations.append("Implement drought-resistant crop varieties or irrigation")
        if "Poor field drainage" in all_risks:
            recommendations.append("Improve field drainage through land leveling or drainage systems")
        if "No crop rotation" in all_risks:
            recommendations.append("Implement crop rotation to improve soil health and reduce pest pressure")
        
        # General optimization tips
        recommendations.extend([
            "Monitor soil moisture regularly and adjust irrigation accordingly",
            "Apply fertilizers at optimal growth stages",
            "Implement integrated pest management practices",
            "Consider precision agriculture technologies for better resource management"
        ])
        
        return recommendations
    
    def _estimate_prediction_accuracy(self, historical_yields: Dict) -> float:
        """Estimate prediction accuracy based on historical data"""
        if not historical_yields:
            return 0.7  # Default accuracy
        
        # Calculate accuracy based on data availability and consistency
        total_accuracy = 0
        count = 0
        
        for crop, yields in historical_yields.items():
            if len(yields) >= 3:
                # Calculate coefficient of variation
                mean_yield = sum(yields) / len(yields)
                variance = sum((y - mean_yield) ** 2 for y in yields) / len(yields)
                cv = math.sqrt(variance) / mean_yield if mean_yield > 0 else 0
                
                # Higher CV means lower accuracy
                accuracy = max(0.5, 1.0 - cv)
                total_accuracy += accuracy
                count += 1
        
        return round(total_accuracy / count if count > 0 else 0.7, 2)
    
    def _calculate_seasonal_adjustments(self, weather: Dict) -> Dict[str, float]:
        """Calculate seasonal adjustments for yield predictions"""
        adjustments = {}
        
        # Get current season
        current_month = datetime.now().month
        
        # Seasonal adjustments for different crops
        if 3 <= current_month <= 5:  # Spring
            adjustments = {
                "wheat": 1.1,  # Good growing conditions
                "maize": 1.0,  # Planting season
                "rice": 1.05,  # Early growing
                "pulses": 1.0
            }
        elif 6 <= current_month <= 8:  # Summer
            adjustments = {
                "wheat": 0.9,  # Harvest stress
                "maize": 1.15,  # Peak growing
                "rice": 1.2,   # Peak growing
                "pulses": 1.1
            }
        elif 9 <= current_month <= 11:  # Fall
            adjustments = {
                "wheat": 1.0,  # Planting
                "maize": 0.9,  # Harvest
                "rice": 0.95,  # Late growing
                "pulses": 1.05
            }
        else:  # Winter
            adjustments = {
                "wheat": 0.8,  # Dormant
                "maize": 0.0,  # Not growing
                "rice": 0.0,   # Not growing
                "pulses": 0.9
            }
        
        return adjustments
