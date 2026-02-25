"""
Routing rules for the Orchestrator.
Rules are evaluated in order; the first match wins.
"""

from typing import Any, Dict, List, Optional


class RoutingRules:
    """Collection of routing rules for orchestrator agent selection."""

    @staticmethod
    def explicit_strategy(request: Dict[str, Any]) -> Optional[List[str]]:
        strategy = request.get("strategy") or (request.get("routing") or {}).get("strategy")
        if not strategy:
            return None

        normalized = str(strategy).strip().lower()
        if normalized in {"weather", "weather_only"}:
            return ["weather_watcher"]
        if normalized in {"growth", "growth_only"}:
            return ["growth_stage_monitor"]
        if normalized in {"irrigation", "irrigation_only"}:
            return ["irrigation_agent"]
        if normalized in {"fertilizer", "fertilizer_only"}:
            return ["fertilizer_agent"]
        if normalized in {"soil_health", "soil_health_only"}:
            return ["soil_health_agent"]
        if normalized in {"both", "comprehensive", "comprehensive_analysis"}:
            return ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "fertilizer_agent", "soil_health_agent"]
        return None

    @staticmethod
    def by_query_keywords(request: Dict[str, Any]) -> Optional[List[str]]:
        query = request.get("query") or request.get("message") or ""
        query = str(query).lower()
        if not query:
            return None

        weather_keywords = {
            "weather", "rain", "rainfall", "temperature", "forecast", "humidity",
            "cold", "wind", "storm", "drought"
        }
        growth_keywords = {
            "growth", "stage", "crop health", "plant", "seedling",
            "flowering", "harvest", "disease", "pest"
        }
        irrigation_keywords = {
            "irrigation", "irrigate", "watering", "sprinkler", "drip", 
            "flood", "canal", "pump"
        }
        fertilizer_keywords = {
            "fertilizer", "fertilize", "nutrient", "nitrogen", "phosphorus", "potassium",
            "npk", "urea", "dap", "mop", "compost", "manure", "feeding"
        }
        soil_health_keywords = {
            "soil health", "soil quality", "soil test", "soil analysis", 
            "soil nutrients", "soil ph", "soil composition",
            "soil fertility", "soil structure", "soil organic", "soil matter"
        }
        market_intelligence_keywords = {
            "market", "price", "sell", "revenue", "profit", "cost", "income",
            "mandi", "apmc", "commodity", "trading", "business", "economics",
            "investment", "return", "yield price", "crop price", "farm income"
        }
        task_scheduler_keywords = {
            "task", "schedule", "plan", "today", "tomorrow", "weekly", "daily",
            "reminder", "reminder", "activity", "work", "job"
        }

        # Use word boundaries for more precise matching
        import re
        query_lower = query.lower()
        
        wants_weather = any(re.search(r'\b' + re.escape(k) + r'\b', query_lower) for k in weather_keywords)
        wants_growth = any(re.search(r'\b' + re.escape(k) + r'\b', query_lower) for k in growth_keywords)
        wants_irrigation = any(re.search(r'\b' + re.escape(k) + r'\b', query_lower) for k in irrigation_keywords)
        wants_fertilizer = any(re.search(r'\b' + re.escape(k) + r'\b', query_lower) for k in fertilizer_keywords)
        wants_soil_health = any(re.search(r'\b' + re.escape(k) + r'\b', query_lower) for k in soil_health_keywords)
        wants_market_intelligence = any(re.search(r'\b' + re.escape(k) + r'\b', query_lower) for k in market_intelligence_keywords)
        wants_task_scheduler = any(re.search(r'\b' + re.escape(k) + r'\b', query_lower) for k in task_scheduler_keywords)

        # More specific routing logic - prioritize single-agent matches first
        if wants_task_scheduler and not wants_weather and not wants_growth and not wants_irrigation and not wants_fertilizer and not wants_soil_health and not wants_market_intelligence:
            return ["task_scheduler_agent"]
        if wants_market_intelligence and not wants_weather and not wants_growth and not wants_irrigation and not wants_fertilizer and not wants_soil_health and not wants_task_scheduler:
            return ["market_intelligence_agent"]
        if wants_soil_health and not wants_weather and not wants_growth and not wants_irrigation and not wants_fertilizer and not wants_market_intelligence and not wants_task_scheduler:
            return ["soil_health_agent"]
        if wants_fertilizer and not wants_weather and not wants_growth and not wants_irrigation and not wants_soil_health and not wants_market_intelligence and not wants_task_scheduler:
            return ["fertilizer_agent"]
        if wants_irrigation and not wants_weather and not wants_growth and not wants_fertilizer and not wants_soil_health and not wants_market_intelligence and not wants_task_scheduler:
            return ["irrigation_agent"]
        if wants_growth and not wants_weather and not wants_irrigation and not wants_fertilizer and not wants_soil_health and not wants_market_intelligence and not wants_task_scheduler:
            return ["growth_stage_monitor"]
        if wants_weather and not wants_growth and not wants_irrigation and not wants_fertilizer and not wants_soil_health and not wants_market_intelligence and not wants_task_scheduler:
            return ["weather_watcher"]
        
        # Then check combinations
        if wants_weather and wants_growth and wants_irrigation and wants_fertilizer and wants_soil_health and wants_market_intelligence:
            return ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "fertilizer_agent", "soil_health_agent", "market_intelligence_agent"]
        if wants_weather and wants_growth and wants_irrigation and wants_fertilizer and wants_soil_health:
            return ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "fertilizer_agent", "soil_health_agent"]
        if wants_weather and wants_growth and wants_irrigation and wants_fertilizer and wants_market_intelligence:
            return ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "fertilizer_agent", "market_intelligence_agent"]
        if wants_weather and wants_growth and wants_irrigation and wants_soil_health and wants_market_intelligence:
            return ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "soil_health_agent", "market_intelligence_agent"]
        if wants_weather and wants_growth and wants_fertilizer and wants_soil_health and wants_market_intelligence:
            return ["weather_watcher", "growth_stage_monitor", "fertilizer_agent", "soil_health_agent", "market_intelligence_agent"]
        if wants_weather and wants_irrigation and wants_fertilizer and wants_soil_health and wants_market_intelligence:
            return ["weather_watcher", "irrigation_agent", "fertilizer_agent", "soil_health_agent", "market_intelligence_agent"]
        if wants_growth and wants_irrigation and wants_fertilizer and wants_soil_health and wants_market_intelligence:
            return ["growth_stage_monitor", "irrigation_agent", "fertilizer_agent", "soil_health_agent", "market_intelligence_agent"]
        if wants_weather and wants_growth:
            return ["weather_watcher", "growth_stage_monitor"]
        if wants_weather and wants_irrigation:
            return ["weather_watcher", "irrigation_agent"]
        if wants_weather and wants_fertilizer:
            return ["weather_watcher", "fertilizer_agent"]
        if wants_weather and wants_soil_health:
            return ["weather_watcher", "soil_health_agent"]
        if wants_weather and wants_market_intelligence:
            return ["weather_watcher", "market_intelligence_agent"]
        if wants_growth and wants_irrigation:
            return ["growth_stage_monitor", "irrigation_agent"]
        if wants_growth and wants_fertilizer:
            return ["growth_stage_monitor", "fertilizer_agent"]
        if wants_growth and wants_soil_health:
            return ["growth_stage_monitor", "soil_health_agent"]
        if wants_growth and wants_market_intelligence:
            return ["growth_stage_monitor", "market_intelligence_agent"]
        if wants_irrigation and wants_fertilizer:
            return ["irrigation_agent", "fertilizer_agent"]
        if wants_irrigation and wants_soil_health:
            return ["irrigation_agent", "soil_health_agent"]
        if wants_irrigation and wants_market_intelligence:
            return ["irrigation_agent", "market_intelligence_agent"]
        if wants_fertilizer and wants_soil_health:
            return ["fertilizer_agent", "soil_health_agent"]
        if wants_fertilizer and wants_market_intelligence:
            return ["fertilizer_agent", "market_intelligence_agent"]
        if wants_soil_health and wants_market_intelligence:
            return ["soil_health_agent", "market_intelligence_agent"]
        
        # Fallback to single agents
        if wants_weather:
            return ["weather_watcher"]
        if wants_growth:
            return ["growth_stage_monitor"]
        if wants_irrigation:
            return ["irrigation_agent"]
        if wants_fertilizer:
            return ["fertilizer_agent"]
        if wants_soil_health:
            return ["soil_health_agent"]
        if wants_market_intelligence:
            return ["market_intelligence_agent"]
        if wants_task_scheduler:
            return ["task_scheduler_agent"]
        return None

    @staticmethod
    def by_payload_presence(request: Dict[str, Any]) -> Optional[List[str]]:
        location = request.get("location") or {}
        crop_data = request.get("crop_data") or request.get("crop") or {}
        irrigation_data = request.get("irrigation_data") or {}
        fertilizer_data = request.get("fertilizer_data") or {}

        has_location = bool(location.get("latitude")) and bool(location.get("longitude"))
        has_crop = bool(crop_data)
        has_irrigation = bool(irrigation_data)
        has_fertilizer = bool(fertilizer_data)

        if has_location and has_crop and has_irrigation and has_fertilizer:
            return ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "fertilizer_agent"]
        if has_location and has_crop and has_irrigation:
            return ["weather_watcher", "growth_stage_monitor", "irrigation_agent"]
        if has_location and has_crop and has_fertilizer:
            return ["weather_watcher", "growth_stage_monitor", "fertilizer_agent"]
        if has_location and has_irrigation and has_fertilizer:
            return ["weather_watcher", "irrigation_agent", "fertilizer_agent"]
        if has_crop and has_irrigation and has_fertilizer:
            return ["growth_stage_monitor", "irrigation_agent", "fertilizer_agent"]
        if has_location and has_crop:
            return ["weather_watcher", "growth_stage_monitor"]
        if has_location and has_irrigation:
            return ["weather_watcher", "irrigation_agent"]
        if has_location and has_fertilizer:
            return ["weather_watcher", "fertilizer_agent"]
        if has_crop and has_irrigation:
            return ["growth_stage_monitor", "irrigation_agent"]
        if has_crop and has_fertilizer:
            return ["growth_stage_monitor", "fertilizer_agent"]
        if has_irrigation and has_fertilizer:
            return ["irrigation_agent", "fertilizer_agent"]
        if has_location:
            return ["weather_watcher"]
        if has_crop:
            return ["growth_stage_monitor"]
        if has_irrigation:
            return ["irrigation_agent"]
        if has_fertilizer:
            return ["fertilizer_agent"]
        return None

    @staticmethod
    def fallback_both(_: Dict[str, Any]) -> List[str]:
        return ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "fertilizer_agent", "soil_health_agent", "market_intelligence_agent"]
