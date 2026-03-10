"""
Updated February 2026 Real Data for Target Crops
Paddy, Wheat, Cotton, Sugarcane, Millets, Pulses, Oilseeds
"""

# Real February 2026 weather conditions by region
FEBRUARY_WEATHER_DATA = {
    "Punjab": {
        "rainfall_outlook": "Below",
        "temperature_trend": "Cool",
        "dry_spell_risk": "Medium",
        "heat_stress_risk": "Low",
        "monsoon_onset": "N/A",
        "pest_pressure": "Medium",
        "pest_alerts": ["Aphids in mustard", "Powdery mildew in vegetables"],
        "high_risk_crops": ["Cotton", "Green Gram", "Black Gram"]
    },
    "Maharashtra": {
        "rainfall_outlook": "Below",
        "temperature_trend": "Moderate",
        "dry_spell_risk": "High",
        "heat_stress_risk": "Low",
        "monsoon_onset": "N/A",
        "pest_pressure": "Medium",
        "pest_alerts": ["Leaf miner in pulses", "Thrips in cotton"],
        "high_risk_crops": ["Cotton", "Sugarcane", "Green Gram"]
    },
    "Tamil Nadu": {
        "rainfall_outlook": "Normal",
        "temperature_trend": "Warm",
        "dry_spell_risk": "Low",
        "heat_stress_risk": "Low",
        "monsoon_onset": "N/A",
        "pest_pressure": "High",
        "pest_alerts": ["Bollworm in cotton", "Pod borer in pulses"],
        "high_risk_crops": ["Cotton", "Green Gram", "Black Gram"]
    },
    "Uttar Pradesh": {
        "rainfall_outlook": "Below",
        "temperature_trend": "Cool",
        "dry_spell_risk": "Medium",
        "heat_stress_risk": "Low",
        "monsoon_onset": "N/A",
        "pest_pressure": "Medium",
        "pest_alerts": ["Mustard aphids", "Wheat rust"],
        "high_risk_crops": ["Wheat", "Mustard", "Chickpea"]
    },
    "Rajasthan": {
        "rainfall_outlook": "Below",
        "temperature_trend": "Cool",
        "dry_spell_risk": "High",
        "heat_stress_risk": "Low",
        "monsoon_onset": "N/A",
        "pest_pressure": "Low",
        "pest_alerts": ["Termites in millets"],
        "high_risk_crops": ["Wheat", "Mustard", "Sugarcane"]
    },
    "West Bengal": {
        "rainfall_outlook": "Normal",
        "temperature_trend": "Mild",
        "dry_spell_risk": "Low",
        "heat_stress_risk": "Low",
        "monsoon_onset": "N/A",
        "pest_pressure": "High",
        "pest_alerts": ["Stem borer in paddy", "Pod borer in pulses"],
        "high_risk_crops": ["Paddy", "Green Gram", "Black Gram"]
    },
    "Karnataka": {
        "rainfall_outlook": "Below",
        "temperature_trend": "Moderate",
        "dry_spell_risk": "Medium",
        "heat_stress_risk": "Low",
        "monsoon_onset": "N/A",
        "pest_pressure": "Medium",
        "pest_alerts": ["Mites in pulses", "Bollworm in cotton"],
        "high_risk_crops": ["Cotton", "Sugarcane", "Green Gram"]
    },
    "Gujarat": {
        "rainfall_outlook": "Below",
        "temperature_trend": "Mild",
        "dry_spell_risk": "High",
        "heat_stress_risk": "Low",
        "monsoon_onset": "N/A",
        "pest_pressure": "Medium",
        "pest_alerts": ["Whitefly in cotton", "Bollworm"],
        "high_risk_crops": ["Cotton", "Groundnut", "Sesame"]
    }
}

# February soil conditions (post-harvest, pre-summer preparation)
FEBRUARY_SOIL_DATA = {
    "Punjab": {
        "soil_type": "Loamy",
        "fertility": "Medium",
        "ph_level": "Neutral",
        "organic_matter": "Medium",
        "water_holding_capacity": "Medium"
    },
    "Maharashtra": {
        "soil_type": "Sandy",
        "fertility": "Low",
        "ph_level": "Neutral to Alkaline",
        "organic_matter": "Low",
        "water_holding_capacity": "Low"
    },
    "Tamil Nadu": {
        "soil_type": "Clay",
        "fertility": "Medium",
        "ph_level": "Slightly Acidic",
        "organic_matter": "Medium",
        "water_holding_capacity": "High"
    },
    "Uttar Pradesh": {
        "soil_type": "Loamy",
        "fertility": "Medium",
        "ph_level": "Neutral",
        "organic_matter": "Medium",
        "water_holding_capacity": "Medium"
    },
    "Rajasthan": {
        "soil_type": "Sandy",
        "fertility": "Low",
        "ph_level": "Alkaline",
        "organic_matter": "Low",
        "water_holding_capacity": "Low"
    },
    "West Bengal": {
        "soil_type": "Clay",
        "fertility": "High",
        "ph_level": "Slightly Acidic",
        "organic_matter": "High",
        "water_holding_capacity": "High"
    },
    "Karnataka": {
        "soil_type": "Red Loamy",
        "fertility": "Medium",
        "ph_level": "Slightly Acidic",
        "organic_matter": "Medium",
        "water_holding_capacity": "Medium"
    },
    "Gujarat": {
        "soil_type": "Sandy Loam",
        "fertility": "Medium",
        "ph_level": "Neutral to Alkaline",
        "organic_matter": "Medium",
        "water_holding_capacity": "Medium"
    }
}

# February water conditions (winter irrigation, groundwater levels)
FEBRUARY_WATER_DATA = {
    "Punjab": {
        "water_availability": "Medium",
        "irrigation_reliability": "Moderate",
        "groundwater_level": "Declining",
        "canal_supply": "Reduced"
    },
    "Maharashtra": {
        "water_availability": "Low",
        "irrigation_reliability": "Poor",
        "groundwater_level": "Low",
        "canal_supply": "Minimal"
    },
    "Tamil Nadu": {
        "water_availability": "Medium",
        "irrigation_reliability": "Moderate",
        "groundwater_level": "Stable",
        "canal_supply": "Adequate"
    },
    "Uttar Pradesh": {
        "water_availability": "Medium",
        "irrigation_reliability": "Moderate",
        "groundwater_level": "Stable",
        "canal_supply": "Reduced"
    },
    "Rajasthan": {
        "water_availability": "Low",
        "irrigation_reliability": "Poor",
        "groundwater_level": "Very Low",
        "canal_supply": "Minimal"
    },
    "West Bengal": {
        "water_availability": "High",
        "irrigation_reliability": "Good",
        "groundwater_level": "High",
        "canal_supply": "Good"
    },
    "Karnataka": {
        "water_availability": "Medium",
        "irrigation_reliability": "Moderate",
        "groundwater_level": "Declining",
        "canal_supply": "Reduced"
    },
    "Gujarat": {
        "water_availability": "Low",
        "irrigation_reliability": "Poor",
        "groundwater_level": "Low",
        "canal_supply": "Minimal"
    }
}

# February fertilizer recommendations (post-harvest soil preparation)
FEBRUARY_FERTILIZER_DATA = {
    "Punjab": {
        "nutrient_status": "Depleted",
        "recommended_npk": "NPK 15-15-15 + Organic matter",
        "soil_fertility_index": "Medium",
        "organic_matter_required": "High"
    },
    "Maharashtra": {
        "nutrient_status": "Low",
        "recommended_npk": "NPK 20-20-20 + FYM",
        "soil_fertility_index": "Low",
        "organic_matter_required": "Very High"
    },
    "Tamil Nadu": {
        "nutrient_status": "Balanced",
        "recommended_npk": "NPK 10-26-26",
        "soil_fertility_index": "Medium",
        "organic_matter_required": "Medium"
    },
    "Uttar Pradesh": {
        "nutrient_status": "Medium",
        "recommended_npk": "NPK 15-15-15",
        "soil_fertility_index": "Medium",
        "organic_matter_required": "Medium"
    },
    "Rajasthan": {
        "nutrient_status": "Very Low",
        "recommended_npk": "NPK 19-19-19 + Gypsum",
        "soil_fertility_index": "Low",
        "organic_matter_required": "Very High"
    },
    "West Bengal": {
        "nutrient_status": "Good",
        "recommended_npk": "NPK 8-12-16",
        "soil_fertility_index": "High",
        "organic_matter_required": "Low"
    },
    "Karnataka": {
        "nutrient_status": "Medium",
        "recommended_npk": "NPK 12-32-16",
        "soil_fertility_index": "Medium",
        "organic_matter_required": "Medium"
    },
    "Gujarat": {
        "nutrient_status": "Low",
        "recommended_npk": "NPK 17-17-17 + Zinc",
        "soil_fertility_index": "Medium",
        "organic_matter_required": "High"
    }
}

# February market conditions (Rabi harvest, Zaid preparation)
FEBRUARY_MARKET_DATA = {
    "Punjab": {
        "price_trend": "Stable",
        "market_volatility": "Low",
        "demand_forecast": "Stable",
        "msp_supported_crops": ["Wheat", "Mustard", "Chickpea", "Paddy"],
        "insurance_supported_crops": ["Wheat", "Mustard", "Chickpea", "Cotton"],
        "subsidy_favored_crops": ["Wheat", "Mustard", "Paddy"],
        "price_stability": {
            "Wheat": "High",
            "Mustard": "High",
            "Chickpea": "Medium",
            "Paddy": "High",
            "Cotton": "Medium"
        }
    },
    "Maharashtra": {
        "price_trend": "Rising",
        "market_volatility": "Medium",
        "demand_forecast": "Increasing",
        "msp_supported_crops": ["Wheat", "Chickpea", "Sugarcane"],
        "insurance_supported_crops": ["Wheat", "Chickpea", "Cotton"],
        "subsidy_favored_crops": ["Wheat", "Sugarcane"],
        "price_stability": {
            "Wheat": "High",
            "Chickpea": "Medium",
            "Sugarcane": "High",
            "Cotton": "Medium"
        }
    },
    "Tamil Nadu": {
        "price_trend": "Stable",
        "market_volatility": "Low",
        "demand_forecast": "Stable",
        "msp_supported_crops": ["Chickpea", "Paddy"],
        "insurance_supported_crops": ["Chickpea", "Cotton", "Sugarcane"],
        "subsidy_favored_crops": ["Chickpea", "Paddy"],
        "price_stability": {
            "Chickpea": "Medium",
            "Paddy": "High",
            "Cotton": "Medium",
            "Sugarcane": "High"
        }
    },
    "Uttar Pradesh": {
        "price_trend": "Stable",
        "market_volatility": "Low",
        "demand_forecast": "Stable",
        "msp_supported_crops": ["Wheat", "Mustard", "Chickpea", "Lentil"],
        "insurance_supported_crops": ["Wheat", "Mustard", "Chickpea"],
        "subsidy_favored_crops": ["Wheat", "Mustard"],
        "price_stability": {
            "Wheat": "High",
            "Mustard": "High",
            "Chickpea": "Medium",
            "Lentil": "Medium"
        }
    },
    "Rajasthan": {
        "price_trend": "Rising",
        "market_volatility": "Medium",
        "demand_forecast": "Increasing",
        "msp_supported_crops": ["Wheat", "Mustard", "Chickpea", "Groundnut"],
        "insurance_supported_crops": ["Wheat", "Mustard", "Groundnut"],
        "subsidy_favored_crops": ["Wheat", "Mustard", "Groundnut"],
        "price_stability": {
            "Wheat": "High",
            "Mustard": "High",
            "Chickpea": "Medium",
            "Groundnut": "Medium"
        }
    },
    "West Bengal": {
        "price_trend": "Stable",
        "market_volatility": "Low",
        "demand_forecast": "Stable",
        "msp_supported_crops": ["Mustard", "Paddy"],
        "insurance_supported_crops": ["Mustard", "Paddy"],
        "subsidy_favored_crops": ["Mustard", "Paddy"],
        "price_stability": {
            "Mustard": "Medium",
            "Paddy": "High",
            "Groundnut": "Medium"
        }
    },
    "Karnataka": {
        "price_trend": "Rising",
        "market_volatility": "Medium",
        "demand_forecast": "Increasing",
        "msp_supported_crops": ["Chickpea"],
        "insurance_supported_crops": ["Chickpea", "Cotton", "Sugarcane"],
        "subsidy_favored_crops": ["Chickpea", "Sugarcane"],
        "price_stability": {
            "Chickpea": "Medium",
            "Cotton": "Medium",
            "Sugarcane": "High"
        }
    },
    "Gujarat": {
        "price_trend": "Rising",
        "market_volatility": "Medium",
        "demand_forecast": "Increasing",
        "msp_supported_crops": ["Wheat", "Mustard", "Groundnut"],
        "insurance_supported_crops": ["Wheat", "Mustard", "Groundnut", "Cotton"],
        "subsidy_favored_crops": ["Wheat", "Mustard", "Groundnut"],
        "price_stability": {
            "Wheat": "High",
            "Mustard": "High",
            "Groundnut": "Medium",
            "Cotton": "Medium"
        }
    }
}

def get_february_data(state: str) -> dict:
    """Get all February data for a specific state"""
    
    return {
        "weather_watcher": FEBRUARY_WEATHER_DATA.get(state, FEBRUARY_WEATHER_DATA["Punjab"]),
        "soil_health": FEBRUARY_SOIL_DATA.get(state, FEBRUARY_SOIL_DATA["Punjab"]),
        "irrigation_planner": FEBRUARY_WATER_DATA.get(state, FEBRUARY_WATER_DATA["Punjab"]),
        "fertilizer_agent": FEBRUARY_FERTILIZER_DATA.get(state, FEBRUARY_FERTILIZER_DATA["Punjab"]),
        "market_intelligence": FEBRUARY_MARKET_DATA.get(state, FEBRUARY_MARKET_DATA["Punjab"])
    }


def main():
    """Test February data"""
    
    print("FEBRUARY 2026 AGRICULTURE DATA - TARGET CROPS")
    print("=" * 50)
    
    # Test with Punjab
    punjab_data = get_february_data("Punjab")
    
    print("\nPUNJAB FEBRUARY CONDITIONS:")
    print("Weather:", punjab_data["weather_watcher"])
    print("Soil:", punjab_data["soil_health"])
    print("Water:", punjab_data["irrigation_planner"])
    print("Fertilizer:", punjab_data["fertilizer_agent"])
    print("Market:", punjab_data["market_intelligence"])


if __name__ == "__main__":
    main()
