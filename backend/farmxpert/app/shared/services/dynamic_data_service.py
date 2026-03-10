"""
Dynamic Data Service
Provides real-time data integration for all FarmXpert agents
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import sys

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from farmxpert.app.config import settings
from farmxpert.app.shared.utils import logger


class DynamicDataService:
    """Service for fetching and managing dynamic agricultural data"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False
        
        cached_time = self.cache[key].get('timestamp')
        if not cached_time:
            return False
            
        return (datetime.now() - cached_time).seconds < self.cache_ttl
    
    def _get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if valid"""
        if self._is_cache_valid(key):
            return self.cache[key]['data']
        return None
    
    def _set_cache_data(self, key: str, data: Dict[str, Any]) -> None:
        """Set data in cache with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def get_dynamic_soil_data(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get dynamic soil data for a location
        Combines soil moisture, temperature, and nutrient data
        """
        cache_key = f"soil_{location.get('latitude')}_{location.get('longitude')}"
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Simulate soil sensor data (in real implementation, this would connect to soil sensors)
            import random
            
            # Base soil data with realistic variations
            soil_data = {
                "moisture_percent": random.uniform(25, 75),  # Dynamic moisture
                "temperature_celsius": random.uniform(15, 35),  # Dynamic soil temp
                "ph_level": random.uniform(6.0, 8.0),  # Dynamic pH
                "nitrogen_ppm": random.uniform(20, 80),  # Dynamic N
                "phosphorus_ppm": random.uniform(10, 50),  # Dynamic P
                "potassium_ppm": random.uniform(100, 300),  # Dynamic K
                "organic_matter_percent": random.uniform(1.5, 5.0),  # Dynamic organic matter
                "electrical_conductivity": random.uniform(0.5, 2.0),  # Dynamic EC
                "timestamp": datetime.now().isoformat(),
                "location": location,
                "data_source": "simulated_sensors"
            }
            
            # Cache the data
            self._set_cache_data(cache_key, soil_data)
            
            logger.info(f"Dynamic soil data retrieved for location: {location}")
            return soil_data
            
        except Exception as e:
            logger.error(f"Error fetching dynamic soil data: {e}")
            # Return fallback data
            return self._get_fallback_soil_data(location)
    
    def get_dynamic_crop_data(self, crop_type: str, location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get dynamic crop data including growth stage, health indicators
        """
        cache_key = f"crop_{crop_type}_{location.get('latitude')}_{location.get('longitude')}"
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            import random
            
            # Calculate days since planting (simulate)
            days_since_planting = random.randint(30, 120)
            
            # Determine growth stage based on days
            if days_since_planting < 30:
                growth_stage = "seedling"
                health_score = random.uniform(0.7, 0.9)
            elif days_since_planting < 60:
                growth_stage = "vegetative"
                health_score = random.uniform(0.6, 0.85)
            elif days_since_planting < 90:
                growth_stage = "flowering"
                health_score = random.uniform(0.5, 0.8)
            else:
                growth_stage = "maturity"
                health_score = random.uniform(0.4, 0.75)
            
            crop_data = {
                "crop_type": crop_type,
                "growth_stage": growth_stage,
                "days_since_planting": days_since_planting,
                "health_score": health_score,
                "height_cm": random.uniform(20, 150),
                "leaf_area_index": random.uniform(1.0, 5.0),
                "chlorophyll_content": random.uniform(30, 60),
                "stress_indicators": {
                    "water_stress": random.uniform(0, 0.3),
                    "nutrient_stress": random.uniform(0, 0.2),
                    "pest_pressure": random.uniform(0, 0.1),
                    "disease_risk": random.uniform(0, 0.15)
                },
                "yield_estimate_kg_per_hectare": random.uniform(2000, 6000),
                "timestamp": datetime.now().isoformat(),
                "location": location,
                "data_source": "simulated_crop_monitoring"
            }
            
            # Cache the data
            self._set_cache_data(cache_key, crop_data)
            
            logger.info(f"Dynamic crop data retrieved for {crop_type}")
            return crop_data
            
        except Exception as e:
            logger.error(f"Error fetching dynamic crop data: {e}")
            return self._get_fallback_crop_data(crop_type, location)
    
    def get_dynamic_irrigation_data(self, location: Dict[str, Any], crop_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get dynamic irrigation data including water requirements and availability
        """
        cache_key = f"irrigation_{location.get('latitude')}_{location.get('longitude')}"
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            import random
            
            # Get soil moisture data
            soil_data = self.get_dynamic_soil_data(location)
            current_moisture = soil_data.get('moisture_percent', 50)
            
            # Calculate irrigation requirements based on crop and soil
            crop_type = crop_data.get('crop_type', 'wheat')
            growth_stage = crop_data.get('growth_stage', 'vegetative')
            
            # Water requirements by growth stage (mm/day)
            water_requirements = {
                'seedling': 3.0,
                'vegetative': 5.0,
                'flowering': 7.0,
                'maturity': 4.0
            }
            
            daily_requirement = water_requirements.get(growth_stage, 5.0)
            
            irrigation_data = {
                "current_soil_moisture": current_moisture,
                "optimal_moisture_range": {
                    "min": 60,
                    "max": 80
                },
                "daily_water_requirement_mm": daily_requirement,
                "irrigation_needed": current_moisture < 65,
                "recommended_amount_mm": max(0, 65 - current_moisture),
                "water_source_status": {
                    "groundwater_level": random.uniform(10, 50),  # meters
                    "canal_water_available": random.choice([True, False]),
                    "rainwater_harvested": random.uniform(1000, 5000)  # liters
                },
                "efficiency_metrics": {
                    "irrigation_efficiency": random.uniform(0.6, 0.85),
                    "water_use_efficiency": random.uniform(1.5, 3.0)  # kg yield per mm water
                },
                "timestamp": datetime.now().isoformat(),
                "location": location,
                "data_source": "simulated_irrigation_sensors"
            }
            
            # Cache the data
            self._set_cache_data(cache_key, irrigation_data)
            
            logger.info(f"Dynamic irrigation data retrieved")
            return irrigation_data
            
        except Exception as e:
            logger.error(f"Error fetching dynamic irrigation data: {e}")
            return self._get_fallback_irrigation_data(location, crop_data)
    
    def get_dynamic_fertilizer_data(self, location: Dict[str, Any], crop_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get dynamic fertilizer recommendations based on soil and crop data
        """
        cache_key = f"fertilizer_{crop_data.get('crop_type', 'wheat')}_{location.get('latitude')}_{location.get('longitude')}"
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            import random
            
            # Get soil and crop data
            soil_data = self.get_dynamic_soil_data(location)
            crop_type = crop_data.get('crop_type', 'wheat')
            growth_stage = crop_data.get('growth_stage', 'vegetative')
            
            # Calculate nutrient requirements based on crop and growth stage
            base_requirements = {
                'wheat': {'N': 120, 'P': 60, 'K': 50},  # kg/ha
                'rice': {'N': 100, 'P': 50, 'K': 80},
                'maize': {'N': 150, 'P': 70, 'K': 60},
                'cotton': {'N': 100, 'P': 50, 'K': 90}
            }
            
            crop_reqs = base_requirements.get(crop_type, base_requirements['wheat'])
            
            # Adjust for growth stage
            stage_multiplier = {
                'seedling': 0.3,
                'vegetative': 0.6,
                'flowering': 0.8,
                'maturity': 0.2
            }
            
            multiplier = stage_multiplier.get(growth_stage, 0.5)
            
            # Current soil levels
            current_n = soil_data.get('nitrogen_ppm', 40) * 2.24  # Convert ppm to kg/ha
            current_p = soil_data.get('phosphorus_ppm', 20) * 2.24
            current_k = soil_data.get('potassium_ppm', 150) * 1.2
            
            fertilizer_data = {
                "current_soil_levels": {
                    "nitrogen_kg_per_hectare": current_n,
                    "phosphorus_kg_per_hectare": current_p,
                    "potassium_kg_per_hectare": current_k
                },
                "recommended_application": {
                    "nitrogen_kg_per_hectare": max(0, (crop_reqs['N'] * multiplier) - current_n),
                    "phosphorus_kg_per_hectare": max(0, (crop_reqs['P'] * multiplier) - current_p),
                    "potassium_kg_per_hectare": max(0, (crop_reqs['K'] * multiplier) - current_k)
                },
                "fertilizer_types": {
                    "urea_kg_per_hectare": max(0, ((crop_reqs['N'] * multiplier) - current_n) / 0.46),  # 46% N
                    "dap_kg_per_hectare": max(0, ((crop_reqs['P'] * multiplier) - current_p) / 0.18),  # 18% P
                    "mop_kg_per_hectare": max(0, ((crop_reqs['K'] * multiplier) - current_k) / 0.60)  # 60% K
                },
                "application_timing": {
                    "optimal_days_after_planting": random.randint(20, 40),
                    "weather_suitable": random.choice([True, False]),
                    "soil_moisture_adequate": soil_data.get('moisture_percent', 50) > 60
                },
                "efficiency_metrics": {
                    "nutrient_use_efficiency": random.uniform(0.4, 0.7),
                    "expected_yield_increase": random.uniform(5, 15)  # percentage
                },
                "timestamp": datetime.now().isoformat(),
                "location": location,
                "data_source": "simulated_soil_analysis"
            }
            
            # Cache the data
            self._set_cache_data(cache_key, fertilizer_data)
            
            logger.info(f"Dynamic fertilizer data retrieved for {crop_type}")
            return fertilizer_data
            
        except Exception as e:
            logger.error(f"Error fetching dynamic fertilizer data: {e}")
            return self._get_fallback_fertilizer_data(location, crop_data)
    
    def _get_fallback_soil_data(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback soil data when dynamic data fails"""
        return {
            "moisture_percent": 50,
            "temperature_celsius": 25,
            "ph_level": 7.0,
            "nitrogen_ppm": 40,
            "phosphorus_ppm": 20,
            "potassium_ppm": 150,
            "organic_matter_percent": 3.0,
            "electrical_conductivity": 1.0,
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "data_source": "fallback"
        }
    
    def _get_fallback_crop_data(self, crop_type: str, location: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback crop data when dynamic data fails"""
        return {
            "crop_type": crop_type,
            "growth_stage": "vegetative",
            "days_since_planting": 60,
            "health_score": 0.75,
            "height_cm": 75,
            "leaf_area_index": 3.0,
            "chlorophyll_content": 45,
            "stress_indicators": {"water_stress": 0.1, "nutrient_stress": 0.1, "pest_pressure": 0.05, "disease_risk": 0.05},
            "yield_estimate_kg_per_hectare": 4000,
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "data_source": "fallback"
        }
    
    def _get_fallback_irrigation_data(self, location: Dict[str, Any], crop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback irrigation data when dynamic data fails"""
        return {
            "current_soil_moisture": 50,
            "optimal_moisture_range": {"min": 60, "max": 80},
            "daily_water_requirement_mm": 5.0,
            "irrigation_needed": True,
            "recommended_amount_mm": 15,
            "water_source_status": {"groundwater_level": 25, "canal_water_available": True, "rainwater_harvested": 2500},
            "efficiency_metrics": {"irrigation_efficiency": 0.75, "water_use_efficiency": 2.0},
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "data_source": "fallback"
        }
    
    def _get_fallback_fertilizer_data(self, location: Dict[str, Any], crop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback fertilizer data when dynamic data fails"""
        return {
            "current_soil_levels": {"nitrogen_kg_per_hectare": 80, "phosphorus_kg_per_hectare": 40, "potassium_kg_per_hectare": 180},
            "recommended_application": {"nitrogen_kg_per_hectare": 40, "phosphorus_kg_per_hectare": 20, "potassium_kg_per_hectare": 20},
            "fertilizer_types": {"urea_kg_per_hectare": 87, "dap_kg_per_hectare": 111, "mop_kg_per_hectare": 33},
            "application_timing": {"optimal_days_after_planting": 30, "weather_suitable": True, "soil_moisture_adequate": True},
            "efficiency_metrics": {"nutrient_use_efficiency": 0.55, "expected_yield_increase": 10},
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "data_source": "fallback"
        }


# Global instance
dynamic_data_service = DynamicDataService()
