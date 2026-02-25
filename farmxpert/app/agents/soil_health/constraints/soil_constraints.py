"""
Soil Health Constraints
Configuration and rules for soil health analysis
"""

from typing import Dict, Any, List
from enum import Enum


class SoilIssueType(str, Enum):
    """Types of soil issues"""
    ACIDIC_SOIL = "acidic_soil"
    ALKALINE_SOIL = "alkaline_soil"
    HIGH_SALINITY = "high_salinity"
    LOW_NITROGEN = "low_nitrogen"
    LOW_PHOSPHORUS = "low_phosphorus"
    LOW_POTASSIUM = "low_potassium"


class UrgencyLevel(str, Enum):
    """Urgency levels for addressing issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Soil parameter thresholds for different crops and regions
SOIL_THRESHOLDS = {
    "default": {
        "pH": {
            "optimal_min": 6.0,
            "optimal_max": 7.5,
            "warning_low": 5.5,
            "warning_high": 8.0,
            "critical_low": 5.0,
            "critical_high": 9.0
        },
        "nitrogen_ppm": {
            "optimal_min": 50,
            "optimal_max": 200,
            "warning_low": 30,
            "critical_low": 20
        },
        "phosphorus_ppm": {
            "optimal_min": 20,
            "optimal_max": 60,
            "warning_low": 12,
            "critical_low": 8
        },
        "potassium_ppm": {
            "optimal_min": 80,
            "optimal_max": 300,
            "warning_low": 60,
            "critical_low": 40
        },
        "electrical_conductivity": {
            "optimal_max": 2.0,
            "warning_high": 3.0,
            "critical_high": 4.0
        },
        "organic_matter_percent": {
            "optimal_min": 2.0,
            "optimal_max": 5.0,
            "warning_low": 1.5,
            "critical_low": 1.0
        }
    },
    "cotton": {
        "pH": {
            "optimal_min": 6.0,
            "optimal_max": 7.0,
            "warning_low": 5.5,
            "warning_high": 7.5,
            "critical_low": 5.0,
            "critical_high": 8.0
        },
        "nitrogen_ppm": {
            "optimal_min": 60,
            "optimal_max": 150,
            "warning_low": 40,
            "critical_low": 25
        },
        "phosphorus_ppm": {
            "optimal_min": 25,
            "optimal_max": 50,
            "warning_low": 15,
            "critical_low": 10
        },
        "potassium_ppm": {
            "optimal_min": 100,
            "optimal_max": 250,
            "warning_low": 70,
            "critical_low": 50
        }
    },
    "wheat": {
        "pH": {
            "optimal_min": 6.2,
            "optimal_max": 7.5,
            "warning_low": 5.8,
            "warning_high": 8.0,
            "critical_low": 5.2,
            "critical_high": 8.5
        },
        "nitrogen_ppm": {
            "optimal_min": 80,
            "optimal_max": 180,
            "warning_low": 50,
            "critical_low": 30
        },
        "phosphorus_ppm": {
            "optimal_min": 30,
            "optimal_max": 70,
            "warning_low": 18,
            "critical_low": 12
        },
        "potassium_ppm": {
            "optimal_min": 120,
            "optimal_max": 280,
            "warning_low": 80,
            "critical_low": 60
        }
    },
    "rice": {
        "pH": {
            "optimal_min": 5.5,
            "optimal_max": 7.0,
            "warning_low": 5.0,
            "warning_high": 7.5,
            "critical_low": 4.5,
            "critical_high": 8.0
        },
        "nitrogen_ppm": {
            "optimal_min": 70,
            "optimal_max": 160,
            "warning_low": 45,
            "critical_low": 25
        },
        "phosphorus_ppm": {
            "optimal_min": 20,
            "optimal_max": 50,
            "warning_low": 12,
            "critical_low": 8
        },
        "potassium_ppm": {
            "optimal_min": 100,
            "optimal_max": 200,
            "warning_low": 70,
            "critical_low": 45
        }
    }
}


# Issue definitions with causes, effects, and recommendations
SOIL_ISSUES_DEFINITION = {
    SoilIssueType.ACIDIC_SOIL: {
        "cause": "High rainfall, leaching of basic cations, excessive use of acid-forming fertilizers",
        "effect": "Reduced nutrient availability, aluminum toxicity, poor microbial activity",
        "urgency": UrgencyLevel.MEDIUM,
        "chemical_recommendations": [
            {
                "name": "Agricultural lime",
                "description": "Calcium carbonate to raise pH",
                "application_rate": "2-4 tons/ha depending on soil pH",
                "timing": "Before planting season"
            },
            {
                "name": "Dolomitic lime",
                "description": "Calcium magnesium carbonate for pH adjustment and magnesium supply",
                "application_rate": "1-3 tons/ha",
                "timing": "Before planting"
            }
        ],
        "organic_recommendations": [
            {
                "name": "Compost",
                "description": "Well-decomposed organic matter to buffer pH",
                "application_rate": "5-10 tons/ha",
                "timing": "Before planting or as top dressing"
            },
            {
                "name": "Green manure",
                "description": "Leguminous crops to improve soil pH and organic matter",
                "application_rate": "Incorporate 6-8 weeks before main crop",
                "timing": "Between cropping seasons"
            }
        ]
    },
    
    SoilIssueType.ALKALINE_SOIL: {
        "cause": "Low rainfall, high calcium carbonate content, excessive lime application",
        "effect": "Micronutrient deficiencies (iron, zinc, manganese), poor nutrient uptake",
        "urgency": UrgencyLevel.MEDIUM,
        "chemical_recommendations": [
            {
                "name": "Elemental sulfur",
                "description": "Sulfur to lower pH through microbial oxidation",
                "application_rate": "500-1000 kg/ha",
                "timing": "3-4 months before planting"
            },
            {
                "name": "Gypsum",
                "description": "Calcium sulfate to improve soil structure and provide sulfur",
                "application_rate": "1-2 tons/ha",
                "timing": "Before planting"
            }
        ],
        "organic_recommendations": [
            {
                "name": "Acidic organic matter",
                "description": "Pine needles, coffee grounds, or other acidic materials",
                "application_rate": "2-5 tons/ha",
                "timing": "Before planting"
            }
        ]
    },
    
    SoilIssueType.HIGH_SALINITY: {
        "cause": "Poor drainage, high water table, excessive fertilizer use, irrigation with saline water",
        "effect": "Osmotic stress, reduced water uptake, ion toxicity, poor seed germination",
        "urgency": UrgencyLevel.HIGH,
        "chemical_recommendations": [
            {
                "name": "Gypsum",
                "description": "Calcium sulfate to replace sodium ions and improve structure",
                "application_rate": "2-5 tons/ha depending on EC level",
                "timing": "Before leaching irrigation"
            }
        ],
        "organic_recommendations": [
            {
                "name": "Organic matter",
                "description": "Farmyard manure or compost to improve structure and water retention",
                "application_rate": "10-15 tons/ha",
                "timing": "Before planting season"
            },
            {
                "name": "Green manure",
                "description": "Salt-tolerant crops like barley or mustard",
                "application_rate": "Incorporate at flowering stage",
                "timing": "Between main crops"
            }
        ],
        "cultural_recommendations": [
            {
                "name": "Leaching irrigation",
                "description": "Apply excess irrigation water to leach salts below root zone",
                "application_rate": "20-30 cm water per leaching event",
                "timing": "Before planting season"
            },
            {
                "name": "Raised beds",
                "description": "Create raised beds to improve drainage",
                "application_rate": "15-20 cm height",
                "timing": "Before land preparation"
            }
        ]
    },
    
    SoilIssueType.LOW_NITROGEN: {
        "cause": "High crop removal, leaching, low organic matter, insufficient fertilization",
        "effect": "Stunted growth, yellowing of leaves, reduced protein content, low yield",
        "urgency": UrgencyLevel.HIGH,
        "chemical_recommendations": [
            {
                "name": "Urea",
                "description": "Concentrated nitrogen source (46% N)",
                "application_rate": "50-100 kg/ha depending on crop",
                "timing": "Split application: basal + top dressing"
            },
            {
                "name": "Ammonium sulfate",
                "description": "Nitrogen with sulfur (21% N, 24% S)",
                "application_rate": "100-150 kg/ha",
                "timing": "Basal application"
            }
        ],
        "organic_recommendations": [
            {
                "name": "Farmyard manure",
                "description": "Well-decomposed cattle manure",
                "application_rate": "5-10 tons/ha",
                "timing": "Before planting"
            },
            {
                "name": "Legume green manure",
                "description": "Fix atmospheric nitrogen",
                "application_rate": "Incorporate 6-8 weeks before main crop",
                "timing": "Between cropping seasons"
            }
        ]
    },
    
    SoilIssueType.LOW_PHOSPHORUS: {
        "cause": "Phosphorus fixation in acidic/alkaline soils, erosion, low organic matter",
        "effect": "Poor root development, delayed maturity, reduced flowering, weak seed formation",
        "urgency": UrgencyLevel.MEDIUM,
        "chemical_recommendations": [
            {
                "name": "Single superphosphate (SSP)",
                "description": "16% P2O5 with calcium and sulfur",
                "application_rate": "100-150 kg/ha",
                "timing": "Basal application at planting"
            },
            {
                "name": "DAP",
                "description": "Diammonium phosphate (18% N, 46% P2O5)",
                "application_rate": "50-100 kg/ha",
                "timing": "Basal application"
            }
        ],
        "organic_recommendations": [
            {
                "name": "Bone meal",
                "description": "Slow-release phosphorus source",
                "application_rate": "200-400 kg/ha",
                "timing": "Before planting"
            },
            {
                "name": "Phosphate-rich compost",
                "description": "Compost enriched with phosphorus",
                "application_rate": "5-8 tons/ha",
                "timing": "Before planting"
            }
        ]
    },
    
    SoilIssueType.LOW_POTASSIUM: {
        "cause": "High crop removal, leaching in sandy soils, insufficient fertilization",
        "effect": "Weak stems, poor disease resistance, reduced yield quality, water stress sensitivity",
        "urgency": UrgencyLevel.MEDIUM,
        "chemical_recommendations": [
            {
                "name": "Muriate of potash (MOP)",
                "description": "Potassium chloride (60% K2O)",
                "application_rate": "50-80 kg/ha",
                "timing": "Basal or top dressing"
            },
            {
                "name": "Sulfate of potash (SOP)",
                "description": "Potassium sulfate (50% K2O, 18% S)",
                "application_rate": "60-100 kg/ha",
                "timing": "Basal application"
            }
        ],
        "organic_recommendations": [
            {
                "name": "Wood ash",
                "description": "Rich in potassium and other minerals",
                "application_rate": "200-500 kg/ha",
                "timing": "Before planting"
            },
            {
                "name": "Banana peel compost",
                "description": "Potassium-rich organic material",
                "application_rate": "2-4 tons/ha",
                "timing": "Before planting"
            }
        ]
    }
}


# Health score calculation weights
HEALTH_SCORE_WEIGHTS = {
    "pH": 0.25,
    "nitrogen": 0.25,
    "phosphorus": 0.20,
    "potassium": 0.20,
    "salinity": 0.10
}


# Crop-specific nutrient requirements
CROP_NUTRIENT_REQUIREMENTS = {
    "cotton": {
        "nitrogen_ppm": {"optimal": 100, "high": 150, "low": 60},
        "phosphorus_ppm": {"optimal": 35, "high": 50, "low": 25},
        "potassium_ppm": {"optimal": 150, "high": 250, "low": 100}
    },
    "wheat": {
        "nitrogen_ppm": {"optimal": 120, "high": 180, "low": 80},
        "phosphorus_ppm": {"optimal": 40, "high": 70, "low": 30},
        "potassium_ppm": {"optimal": 180, "high": 280, "low": 120}
    },
    "rice": {
        "nitrogen_ppm": {"optimal": 100, "high": 160, "low": 70},
        "phosphorus_ppm": {"optimal": 30, "high": 50, "low": 20},
        "potassium_ppm": {"optimal": 150, "high": 200, "low": 100}
    },
    "maize": {
        "nitrogen_ppm": {"optimal": 140, "high": 200, "low": 100},
        "phosphorus_ppm": {"optimal": 45, "high": 70, "low": 35},
        "potassium_ppm": {"optimal": 200, "high": 300, "low": 150}
    }
}


def get_thresholds_for_crop(crop_type: str) -> Dict[str, Any]:
    """Get soil thresholds for a specific crop type"""
    return SOIL_THRESHOLDS.get(crop_type, SOIL_THRESHOLDS["default"])


def get_issue_definition(issue_type: SoilIssueType) -> Dict[str, Any]:
    """Get definition for a specific soil issue"""
    return SOIL_ISSUES_DEFINITION.get(issue_type, {})
