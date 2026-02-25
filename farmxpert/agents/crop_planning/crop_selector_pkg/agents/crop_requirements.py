"""
Crop Requirements Data - Water, soil, and pest requirements for target crops
"""

# Target crops: Paddy, Wheat, Cotton, Sugarcane, Millets, Pulses, Oilseeds
CROP_REQUIREMENTS = {
    # CEREALS
    "Paddy": {
        "water": "High",
        "soil": "Clay",
        "pest_sensitivity": "High",
        "season": "Kharif",
        "seed_rate": "25-30 kg/acre",
        "irrigation_schedule": "Continuous flooding or alternate wetting-drying",
        "fertilizer_needs": "NPK 20-20-20",
        "growth_duration": "120-150 days",
        "water_needs": "High - 1500-2000 mm"
    },
    "Wheat": {
        "water": "Medium",
        "soil": "Loamy",
        "pest_sensitivity": "Medium",
        "season": "Rabi",
        "seed_rate": "40-50 kg/acre",
        "irrigation_schedule": "4-5 irrigations at critical stages",
        "fertilizer_needs": "NPK 15-15-15",
        "growth_duration": "100-120 days",
        "water_needs": "Medium - 450-600 mm"
    },
    "Pearl Millet": {
        "water": "Low",
        "soil": "Sandy",
        "pest_sensitivity": "Low",
        "season": "Kharif",
        "seed_rate": "3-5 kg/acre",
        "irrigation_schedule": "2-3 irrigations if needed",
        "fertilizer_needs": "NPK 20-20-20",
        "growth_duration": "80-90 days",
        "water_needs": "Low - 300-400 mm"
    },
    "Sorghum": {
        "water": "Low",
        "soil": "Loamy",
        "pest_sensitivity": "Low",
        "season": "Kharif",
        "seed_rate": "8-10 kg/acre",
        "irrigation_schedule": "2-3 irrigations if needed",
        "fertilizer_needs": "NPK 20-20-20",
        "growth_duration": "90-110 days",
        "water_needs": "Low - 400-500 mm"
    },
    
    # COMMERCIAL CROPS
    "Cotton": {
        "water": "Medium",
        "soil": "Loamy",
        "pest_sensitivity": "High",
        "season": "Kharif",
        "seed_rate": "1.5-2 kg/acre",
        "irrigation_schedule": "Irrigation at flowering and boll development",
        "fertilizer_needs": "NPK 20-20-20",
        "growth_duration": "150-180 days",
        "water_needs": "Medium - 700-900 mm"
    },
    "Sugarcane": {
        "water": "High",
        "soil": "Loamy",
        "pest_sensitivity": "Medium",
        "season": "All",
        "seed_rate": "30-40 thousand sets/acre",
        "irrigation_schedule": "Regular irrigation throughout growth",
        "fertilizer_needs": "NPK 20-20-20",
        "growth_duration": "300-360 days",
        "water_needs": "High - 1500-2500 mm"
    },
    
    # PULSES
    "Green Gram": {
        "water": "Low",
        "soil": "Loamy",
        "pest_sensitivity": "Low",
        "season": "Kharif",
        "seed_rate": "12-15 kg/acre",
        "irrigation_schedule": "1-2 irrigations at flowering",
        "fertilizer_needs": "NPK 10-26-26",
        "growth_duration": "60-70 days",
        "water_needs": "Low - 250-350 mm"
    },
    "Black Gram": {
        "water": "Low",
        "soil": "Loamy",
        "pest_sensitivity": "Low",
        "season": "Kharif",
        "seed_rate": "12-15 kg/acre",
        "irrigation_schedule": "1-2 irrigations at flowering",
        "fertilizer_needs": "NPK 10-26-26",
        "growth_duration": "60-75 days",
        "water_needs": "Low - 250-350 mm"
    },
    "Pigeon Pea": {
        "water": "Low",
        "soil": "Loamy",
        "pest_sensitivity": "Low",
        "season": "Kharif",
        "seed_rate": "12-15 kg/acre",
        "irrigation_schedule": "2-3 irrigations at critical stages",
        "fertilizer_needs": "NPK 10-26-26",
        "growth_duration": "150-180 days",
        "water_needs": "Low - 400-500 mm"
    },
    "Chickpea": {
        "water": "Low",
        "soil": "Loamy",
        "pest_sensitivity": "Low",
        "season": "Rabi",
        "seed_rate": "60-80 kg/acre",
        "irrigation_schedule": "2-3 irrigations at flowering and pod development",
        "fertilizer_needs": "NPK 10-26-26",
        "growth_duration": "90-110 days",
        "water_needs": "Low - 300-400 mm"
    },
    "Lentil": {
        "water": "Low",
        "soil": "Loamy",
        "pest_sensitivity": "Low",
        "season": "Rabi",
        "seed_rate": "25-30 kg/acre",
        "irrigation_schedule": "2-3 irrigations at critical stages",
        "fertilizer_needs": "NPK 10-26-26",
        "growth_duration": "100-110 days",
        "water_needs": "Low - 300-350 mm"
    },
    
    # OILSEEDS
    "Groundnut": {
        "water": "Low",
        "soil": "Sandy",
        "pest_sensitivity": "Medium",
        "season": "Kharif",
        "seed_rate": "80-100 kg/acre",
        "irrigation_schedule": "Irrigation at flowering and pod development",
        "fertilizer_needs": "NPK 17-17-17",
        "growth_duration": "90-110 days",
        "water_needs": "Low - 400-500 mm"
    },
    "Mustard": {
        "water": "Low",
        "soil": "Loamy",
        "pest_sensitivity": "Medium",
        "season": "Rabi",
        "seed_rate": "2-3 kg/acre",
        "irrigation_schedule": "2-3 irrigations at flowering and pod filling",
        "fertilizer_needs": "NPK 17-17-17",
        "growth_duration": "90-110 days",
        "water_needs": "Low - 300-400 mm"
    },
    "Sesame": {
        "water": "Low",
        "soil": "Sandy",
        "pest_sensitivity": "Low",
        "season": "Kharif",
        "seed_rate": "4-5 kg/acre",
        "irrigation_schedule": "1-2 irrigations if needed",
        "fertilizer_needs": "NPK 17-17-17",
        "growth_duration": "80-90 days",
        "water_needs": "Low - 300-400 mm"
    }
}

# Seasonal crop database
SEASONAL_CROPS = {
    "Kharif": [
        "Paddy", "Cotton", "Pearl Millet", "Sorghum", 
        "Green Gram", "Black Gram", "Pigeon Pea", "Groundnut", "Sesame"
    ],
    "Rabi": [
        "Wheat", "Sorghum", "Pearl Millet", "Chickpea", 
        "Lentil", "Mustard", "Groundnut", "Sesame"
    ],
    "Zaid": [
        "Sugarcane", "Green Gram", "Black Gram"
    ]
}

# Risk weights for scoring
RISK_WEIGHTS = {
    "weather": 0.30,
    "water": 0.25,
    "soil": 0.20,
    "market": 0.15,
    "pest": 0.10
}

# Qualitative scoring mapping
QUALITATIVE_SCORES = {"Low": 0.3, "Medium": 0.6, "High": 0.9}

def get_crop_requirements(crop: str) -> dict:
    """Get requirements for a specific crop"""
    return CROP_REQUIREMENTS.get(crop, {})

def get_seasonal_crops(season: str) -> list:
    """Get crops suitable for a specific season"""
    return SEASONAL_CROPS.get(season, [])

def get_all_crops() -> list:
    """Get all supported crops"""
    return list(CROP_REQUIREMENTS.keys())
