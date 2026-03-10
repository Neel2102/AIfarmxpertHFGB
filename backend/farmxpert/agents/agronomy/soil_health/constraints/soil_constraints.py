from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class SoilIssueType(str, Enum):
    ACIDIC_SOIL = "acidic_soil"
    ALKALINE_SOIL = "alkaline_soil"
    HIGH_SALINITY = "high_salinity"
    LOW_NITROGEN = "low_nitrogen"
    LOW_PHOSPHORUS = "low_phosphorus"
    LOW_POTASSIUM = "low_potassium"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Thresholds:
    ph_min: float = 6.0
    ph_max: float = 7.5
    ec_max: float = 2.0
    n_min: float = 40.0
    p_min: float = 15.0
    k_min: float = 80.0


HEALTH_SCORE_WEIGHTS: Dict[str, float] = {
    "pH": 0.35,
    "nutrients": 0.5,
    "salinity": 0.15,
}

# Minimal placeholder nutrient requirements; service logic may enrich later.
CROP_NUTRIENT_REQUIREMENTS: Dict[str, Dict[str, float]] = {
    "default": {"n": 40.0, "p": 15.0, "k": 80.0},
}


def get_thresholds_for_crop(crop_type: str) -> Dict[str, Any]:
    _ = (crop_type or "default").lower()
    t = Thresholds()
    return {
        "ph": {"min": t.ph_min, "max": t.ph_max},
        "electrical_conductivity": {"max": t.ec_max},
        "nitrogen": {"min": t.n_min},
        "phosphorus": {"min": t.p_min},
        "potassium": {"min": t.k_min},
    }


def get_issue_definition(issue_type: SoilIssueType) -> Dict[str, str]:
    definitions: Dict[SoilIssueType, Dict[str, str]] = {
        SoilIssueType.ACIDIC_SOIL: {
            "cause": "Soil pH is below optimal range.",
            "effect": "Nutrient availability may be reduced and roots can be stressed.",
        },
        SoilIssueType.ALKALINE_SOIL: {
            "cause": "Soil pH is above optimal range.",
            "effect": "Micronutrient deficiencies may appear and growth may slow.",
        },
        SoilIssueType.HIGH_SALINITY: {
            "cause": "Electrical conductivity indicates elevated salinity.",
            "effect": "Osmotic stress can reduce water uptake and yield.",
        },
        SoilIssueType.LOW_NITROGEN: {
            "cause": "Nitrogen is below the target level.",
            "effect": "Poor vegetative growth and pale leaves.",
        },
        SoilIssueType.LOW_PHOSPHORUS: {
            "cause": "Phosphorus is below the target level.",
            "effect": "Weak root development and delayed maturity.",
        },
        SoilIssueType.LOW_POTASSIUM: {
            "cause": "Potassium is below the target level.",
            "effect": "Poor stress tolerance and reduced quality.",
        },
    }
    return definitions.get(issue_type, {"cause": "Unknown", "effect": "Unknown"})
