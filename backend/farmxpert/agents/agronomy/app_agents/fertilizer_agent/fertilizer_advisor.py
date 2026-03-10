import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
MASTER_DB_PATH = BASE_DIR / "crop_nutrient_master.json"
CROP_GROUPS_PATH = BASE_DIR / "crop_groups.json"
HISTORY_PATH = BASE_DIR / "fertilizer_history.json"

# Load databases
with open(MASTER_DB_PATH) as f:
    MASTER_DB = json.load(f)

with open(CROP_GROUPS_PATH) as f:
    CROP_GROUPS = json.load(f)

# Crop to group mapping
CROP_TO_GROUP = {
    "wheat": "cereal", "rice": "cereal", "maize": "cereal", "millets": "cereal", "barley": "cereal",
    "pulses": "pulse", "ground nuts": "pulse",
    "oil seeds": "oilseed",
    "cotton": "fiber",
    "potato": "tuber", "sugarcane": "tuber",
    "tobacco": "vegetable"
}

# Generic fallback RDF
GENERIC_RDF = {"N": 50, "P2O5": 40, "K2O": 30}

# Base confidence
BASE_CONFIDENCE = 0.85


def _blocked(reason: str) -> Dict[str, Any]:
    """Return blocked response with reason."""
    return {
        "agent": "fertilizer_advisor",
        "status": "blocked",
        "blockers": [reason],
        "recommendations": [],
        "alerts": [],
        "confidence": 0.0
    }


def _validate_input(payload: Dict[str, Any]) -> List[str]:
    """Validate input payload and return list of blocker reasons."""
    blockers = []
    
    # Check required top-level fields
    required_fields = ["crop", "growth_stage", "area_acres", "soil", "recent_weather"]
    for field in required_fields:
        if field not in payload:
            blockers.append(f"Missing input: {field}")
    
    if blockers:
        return blockers
    
    # Validate area_acres
    if not isinstance(payload["area_acres"], (int, float)) or payload["area_acres"] <= 0:
        blockers.append("area_acres must be > 0")
    
    # Validate soil
    soil = payload["soil"]
    if not isinstance(soil, dict):
        blockers.append("soil must be a dictionary")
    else:
        for nutrient in ["n", "p", "k"]:
            if nutrient not in soil:
                blockers.append(f"Missing soil nutrient: {nutrient}")
            elif not isinstance(soil[nutrient], (int, float)):
                blockers.append(f"Invalid soil.{nutrient} value")
    
    # Validate recent_weather
    weather = payload["recent_weather"]
    if not isinstance(weather, dict):
        blockers.append("recent_weather must be a dictionary")
    else:
        if "rain_last_3_days_mm" not in weather:
            blockers.append("Missing recent_weather.rain_last_3_days_mm")
        elif not isinstance(weather["rain_last_3_days_mm"], (int, float)):
            blockers.append("Invalid rain_last_3_days_mm value")
        
        if "forecast_next_5_days" not in weather:
            blockers.append("Missing recent_weather.forecast_next_5_days")
        elif not isinstance(weather["forecast_next_5_days"], list):
            blockers.append("forecast_next_5_days must be a list")
    
    return blockers


def _check_weather_blockers(weather: Dict[str, Any]) -> List[str]:
    """Check if weather conditions block fertilizer application."""
    blockers = []
    
    rain_last_3_days = weather.get("rain_last_3_days_mm", 0)
    if rain_last_3_days > 25:
        blockers.append("Rainfall in last 3 days exceeds 25mm - application unsafe")
    
    forecast = weather.get("forecast_next_5_days", [])
    rain_count = sum(1 for day in forecast if isinstance(day, str) and "rain" in day.lower())
    if rain_count >= 2:
        blockers.append("Forecast shows 2 or more rainy days - application unsafe")
    
    return blockers


def _get_crop_rdf(crop: str) -> tuple[Dict[str, float], str]:
    """Get crop RDF with source tracking.
    
    Returns:
        tuple: (rdf_dict, source_string)
        source_string is one of: "exact", "group", "generic"
    """
    crop_lower = crop.lower()
    
    # Try exact match first
    if crop_lower in MASTER_DB:
        return MASTER_DB[crop_lower]["seasonal_rdf_kg_per_acre"], "exact"
    
    # Try crop group fallback
    group = CROP_TO_GROUP.get(crop_lower)
    if group and group in CROP_GROUPS:
        return CROP_GROUPS[group]["default_rdf"], "group"
    
    # Generic fallback
    return GENERIC_RDF, "generic"


def _compute_stage_requirement(profile: Dict[str, Any], stage: str) -> Dict[str, float]:
    """Compute stage-specific nutrient requirements.
    
    Formula: seasonal_rdf × stage_distribution = stage requirement
    """
    stage_lower = stage.lower()
    stage_dist = profile.get("stage_distribution", {})
    
    if stage_lower not in stage_dist:
        raise ValueError(f"Stage '{stage}' not in crop profile")
    
    seasonal_rdf = profile["seasonal_rdf_kg_per_acre"]
    stage_split = stage_dist[stage_lower]
    
    # Calculate requirement for each nutrient
    requirements = {}
    for nutrient in ["N", "P2O5", "K2O"]:
        rdf_value = seasonal_rdf.get(nutrient, 0)
        split_value = stage_split.get(nutrient, 0)
        requirements[nutrient] = round(rdf_value * split_value, 2)
    
    return requirements


def _calculate_deficit(required: float, available: float) -> float:
    """Calculate nutrient deficit. Returns 0 if no deficit."""
    if required <= 0:
        return 0.0
    deficit = required - available
    return max(0.0, round(deficit, 2))


def _calculate_confidence(requirements: Dict[str, float], deficits: Dict[str, float], has_blockers: bool, rdf_source: str) -> float:
    """Calculate confidence score based on data quality, deficits, and RDF source."""
    if has_blockers:
        return 0.0
    
    if not deficits or all(d <= 0 for d in deficits.values()):
        return 0.85  # High confidence when no action needed
    
    # Start with base confidence adjusted by RDF source
    confidence = BASE_CONFIDENCE
    
    if rdf_source == "exact":
        confidence = BASE_CONFIDENCE
    elif rdf_source == "group":
        confidence = BASE_CONFIDENCE - 0.10
    else:  # generic
        confidence = BASE_CONFIDENCE - 0.20
    
    # Further adjust based on deficit magnitude
    max_deficit = max(deficits.values()) if deficits else 0
    if max_deficit > 10:
        confidence += 0.05
    elif max_deficit < 2:
        confidence -= 0.05
    
    return max(0.0, min(1.0, round(confidence, 2)))


def _load_history() -> List[Dict[str, Any]]:
    """Load fertilizer application history from file."""
    if not HISTORY_PATH.exists():
        return []
    try:
        with open(HISTORY_PATH) as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def _save_history(history: List[Dict[str, Any]]) -> None:
    """Save fertilizer application history to file."""
    try:
        with open(HISTORY_PATH, 'w') as f:
            json.dump(history, f, indent=2)
    except IOError:
        pass  # Silently fail if can't write


def _check_recent_applications(crop: str, days_threshold: int = 20) -> List[str]:
    """Check if any fertilizer was applied to this crop in the last N days.
    
    Returns list of blocker reasons if applications found within threshold.
    """
    history = _load_history()
    if not history:
        return []
    
    blockers = []
    today = datetime.now()
    threshold_date = today - timedelta(days=days_threshold)
    
    crop_lower = crop.lower()
    for record in history:
        if not isinstance(record, dict):
            continue
        
        record_crop = record.get("crop", "").lower()
        if record_crop != crop_lower:
            continue
        
        # Check application date
        app_date_str = record.get("application_date")
        if not app_date_str:
            continue
        
        try:
            app_date = datetime.fromisoformat(app_date_str)
            days_since = (today - app_date).days
            
            if days_since < days_threshold:
                fertilizer = record.get("fertilizer", "fertilizer")
                blockers.append(
                    f"Fertilizer ({fertilizer}) was applied {days_since} days ago. "
                    f"Wait {days_threshold - days_since} more days before next application."
                )
        except (ValueError, TypeError):
            continue
    
    return blockers


def _record_application(crop: str, recommendations: List[Dict[str, Any]]) -> None:
    """Record fertilizer applications to history."""
    if not recommendations:
        return
    
    history = _load_history()
    today = datetime.now().isoformat()
    
    for rec in recommendations:
        fertilizer = rec.get("fertilizer", "")
        if fertilizer:
            history.append({
                "crop": crop.lower(),
                "fertilizer": fertilizer,
                "application_date": today,
                "dose_per_acre_kg": rec.get("dose_per_acre_kg", 0),
                "total_quantity_kg": rec.get("total_quantity_kg", 0)
            })
    
    _save_history(history)


def fertilizer_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure orchestrator-grade fertilizer advisor agent.
    
    Args:
        payload: Dictionary containing:
            - crop: str (e.g., "wheat")
            - growth_stage: str (e.g., "tillering")
            - area_acres: float (> 0)
            - soil: dict with keys "n", "p", "k" (values in kg/acre)
            - recent_weather: dict with:
                - rain_last_3_days_mm: float
                - forecast_next_5_days: list of strings
    
    Returns:
        Dictionary with strict JSON structure:
        {
            "agent": "fertilizer_advisor",
            "status": "ok" | "blocked",
            "blockers": [],
            "recommendations": [...],
            "alerts": [],
            "confidence": float
        }
    """
    # Validate input structure
    validation_blockers = _validate_input(payload)
    if validation_blockers:
        return {
            "agent": "fertilizer_advisor",
            "status": "blocked",
            "blockers": validation_blockers,
            "recommendations": [],
            "alerts": [],
            "confidence": 0.0
        }
    
    blockers = []
    
    # Get crop RDF with source tracking
    crop_rdf, rdf_source = _get_crop_rdf(payload["crop"])
    
    # For now, use equal stage distribution (can be enhanced later)
    stage_requirements = {
        "N": crop_rdf["N"] * 0.25,  # Assume 25% at current stage
        "P2O5": crop_rdf["P2O5"] * 0.25,
        "K2O": crop_rdf["K2O"] * 0.25
    }
    
    # Check weather blockers
    weather_blockers = _check_weather_blockers(payload["recent_weather"])
    blockers.extend(weather_blockers)
    
    # Check recent application history (20-day cooldown)
    history_blockers = _check_recent_applications(payload["crop"], days_threshold=20)
    blockers.extend(history_blockers)
    
    if blockers:
        return {
            "agent": "fertilizer_advisor",
            "status": "blocked",
            "blockers": blockers,
            "recommendations": [],
            "alerts": [],
            "confidence": 0.0
        }
    
    # Calculate nutrient deficits
    soil = payload["soil"]
    area = payload["area_acres"]
    stage = payload["growth_stage"]
    
    # Map soil nutrients to requirements
    # Soil has: n, p, k (in kg/acre)
    # Requirements are: N, P2O5, K2O (in kg/acre)
    # We compare directly (assuming soil values are in same units)
    deficits = {
        "N": _calculate_deficit(stage_requirements["N"], soil["n"]),
        "P2O5": _calculate_deficit(stage_requirements["P2O5"], soil["p"]),
        "K2O": _calculate_deficit(stage_requirements["K2O"], soil["k"])
    }
    
    # Generate recommendations only for nutrients with deficits
    recommendations = []
    
    if deficits["N"] > 0:
        recommendations.append({
            "fertilizer": "nitrogen_source",
            "dose_per_acre_kg": deficits["N"],
            "total_quantity_kg": round(deficits["N"] * area, 2),
            "application_method": "After irrigation",
            "reason": f"Nitrogen deficit at {stage} stage",
            "rdf_source": rdf_source,
            "confidence": 0.0,  # Will be set at overall level
            "alerts": []
        })
    
    if deficits["P2O5"] > 0:
        recommendations.append({
            "fertilizer": "phosphorus_source",
            "dose_per_acre_kg": deficits["P2O5"],
            "total_quantity_kg": round(deficits["P2O5"] * area, 2),
            "application_method": "After irrigation",
            "reason": f"Phosphorus deficit at {stage} stage",
            "rdf_source": rdf_source,
            "confidence": 0.0,  # Will be set at overall level
            "alerts": []
        })
    
    if deficits["K2O"] > 0:
        recommendations.append({
            "fertilizer": "potassium_source",
            "dose_per_acre_kg": deficits["K2O"],
            "total_quantity_kg": round(deficits["K2O"] * area, 2),
            "application_method": "After irrigation",
            "reason": f"Potassium deficit at {stage} stage",
            "rdf_source": rdf_source,
            "confidence": 0.0,  # Will be set at overall level
            "alerts": []
        })
    
    # Calculate confidence with RDF source awareness
    confidence = _calculate_confidence(stage_requirements, deficits, False, rdf_source)
    
    # Update confidence for all recommendations
    for rec in recommendations:
        rec["confidence"] = confidence
    
    # Record applications to history if recommendations are made
    if recommendations:
        _record_application(payload["crop"], recommendations)
    
    return {
        "agent": "fertilizer_advisor",
        "status": "ok",
        "blockers": [],
        "recommendations": recommendations,
        "alerts": [],
        "confidence": confidence
    }
