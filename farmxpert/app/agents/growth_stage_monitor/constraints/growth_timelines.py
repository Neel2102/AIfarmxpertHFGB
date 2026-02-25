"""
Crop Growth Timelines
Defines growth stages and timelines for different crops
"""

from typing import Dict, List, Tuple

# Convert dictionary timelines to list of tuples for easier processing
def _convert_dict_to_tuples(timeline_dict: Dict[str, int]) -> List[Tuple[str, int, int]]:
    """Convert timeline dictionary to list of (stage, start_day, end_day) tuples"""
    stages = list(timeline_dict.keys())
    tuples = []
    
    for i, stage in enumerate(stages):
        start_day = timeline_dict[stage]
        if i < len(stages) - 1:
            end_day = timeline_dict[stages[i + 1]] - 1
        else:
            end_day = start_day + 20  # Give last stage some range
        
        tuples.append((stage, start_day, end_day))
    
    return tuples

# Original dictionary data (kept for reference)
_CROP_GROWTH_DAY_MAPS: Dict[str, Dict[str, int]] = {
    "wheat": {
        "germination": 7,      # days
        "seedling": 21,        # days
        "tillering": 35,       # days
        "stem_extension": 55,  # days
        "booting": 70,         # days
        "heading": 85,         # days
        "flowering": 95,       # days
        "milk": 105,           # days
        "dough": 115,          # days
        "ripening": 130,       # days
        "maturity": 140        # days
    },
    "rice": {
        "germination": 5,
        "seedling": 25,
        "tillering": 45,
        "stem_extension": 65,
        "booting": 80,
        "heading": 90,
        "flowering": 100,
        "milk": 110,
        "dough": 120,
        "ripening": 135,
        "maturity": 150
    },
    "corn": {
        "germination": 7,
        "seedling": 20,
        "vegetative": 40,
        "tasseling": 60,
        "silking": 65,
        "blister": 75,
        "milk": 85,
        "dough": 95,
        "dent": 110,
        "maturity": 120
    },
    "soybean": {
        "germination": 7,
        "emergence": 14,
        "vegetative": 35,
        "flowering": 50,
        "pod": 65,
        "seed": 80,
        "maturity": 100
    },
    "cotton": {
        "germination": 7,
        "seedling": 21,
        "vegetative": 45,
        "square": 60,
        "flower": 70,
        "boll": 85,
        "maturity": 120
    }
}

# Converted timelines in the expected format
CROP_GROWTH_TIMELINES: Dict[str, List[Tuple[str, int, int]]] = {
    crop: _convert_dict_to_tuples(timeline) 
    for crop, timeline in _CROP_GROWTH_DAY_MAPS.items()
}

# Growth stage descriptions
GROWTH_STAGE_DESCRIPTIONS: Dict[str, str] = {
    "germination": "Seed germination and sprouting",
    "seedling": "Young seedling establishment",
    "tillering": "Tiller formation and early growth",
    "stem_extension": "Stem elongation and leaf development",
    "booting": "Boot stage - spike formation",
    "heading": "Heading - spike emergence",
    "flowering": "Flowering and pollination",
    "milk": "Milk stage - grain filling begins",
    "dough": "Dough stage - grain development",
    "ripening": "Ripening - maturation process",
    "maturity": "Full maturity - harvest ready",
    "vegetative": "Vegetative growth phase",
    "tasseling": "Tassel formation in corn",
    "silking": "Silk emergence in corn",
    "blister": "Blister stage in corn",
    "dent": "Dent stage in corn",
    "emergence": "Seed emergence from soil",
    "pod": "Pod development in legumes",
    "seed": "Seed development in legumes",
    "square": "Square formation in cotton",
    "boll": "Boll development in cotton"
}

# Default growth stages for unknown crops
DEFAULT_GROWTH_STAGES = [
    "germination",
    "seedling", 
    "vegetative",
    "flowering",
    "maturity"
]
