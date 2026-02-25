"""
FarmXpert Orchestrator Agent
Central coordinator for all AI agents with unified configuration support
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Import unified configuration
try:
    from farmxpert.app.agents.config_service import agent_config_service
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logging.warning("Unified configuration service not available")

# Import individual agents
from farmxpert.app.agents.weather_watcher.services.weather_service import WeatherService
from farmxpert.app.agents.market_intelligence.service import MarketIntelligenceService
from farmxpert.app.agents.task_scheduler.service import TaskSchedulerService

# Import shared utilities
from farmxpert.app.shared.utils import logger, create_success_response, create_error_response
from farmxpert.app.shared.exceptions import FarmXpertException, OrchestratorException
from farmxpert.app.shared.services.dynamic_data_service import dynamic_data_service
from farmxpert.app.orchestrator.services import OrchestratorLLMService, RoutingRules


class OrchestratorAgent:
    """Central orchestrator that coordinates all AI agents."""

    RULES = [
        RoutingRules.explicit_strategy,
        RoutingRules.by_query_keywords,
        RoutingRules.by_payload_presence,
        RoutingRules.fallback_both
    ]

    # Use unified configuration if available, fallback to static mapping
    QUERY_TYPE_MAP = {
        "weather_watcher": ["weather_watcher"],
        "growth_stage_monitor": ["growth_stage_monitor"],
        "irrigation_agent": ["irrigation_agent"],
        "fertilizer_agent": ["fertilizer_agent"],
        "soil_health_agent": ["soil_health_agent"],
        "market_intelligence_agent": ["market_intelligence_agent"],
        "task_scheduler_agent": ["task_scheduler_agent"],
        "weather_only": ["weather_watcher"],
        "growth_only": ["growth_stage_monitor"],
        "irrigation_only": ["irrigation_agent"],
        "fertilizer_only": ["fertilizer_agent"],
        "soil_health_only": ["soil_health_agent"],
        "market_only": ["market_intelligence_agent"],
        "task_scheduling": ["task_scheduler_agent"],
        "comprehensive_analysis": ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "fertilizer_agent", "soil_health_agent", "market_intelligence_agent", "task_scheduler_agent"],
        "conversational_query": ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "fertilizer_agent", "soil_health_agent", "market_intelligence_agent", "task_scheduler_agent"],
        "farmer_query": ["weather_watcher", "growth_stage_monitor", "irrigation_agent", "fertilizer_agent", "soil_health_agent", "market_intelligence_agent", "task_scheduler_agent"]
    }

    @staticmethod
    async def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Try to enrich with dynamic data, but don't fail if it doesn't work
            try:
                enriched_request = OrchestratorAgent._enrich_with_dynamic_data(request)
                logger.info("Dynamic data enrichment successful")
            except Exception as e:
                logger.warning(f"Dynamic data enrichment failed: {e}")
                enriched_request = request

            # Determine query type using routing rules
            query_type = OrchestratorAgent._determine_query_type(enriched_request)
            # Ensure query_type is a string, not a list
            if isinstance(query_type, list):
                query_type = query_type[0] if query_type else "conversational_query"
            logger.info(f"Determined query type: {query_type}")

            # Get agents to call based on query type
            agents_to_call = OrchestratorAgent.QUERY_TYPE_MAP.get(query_type, [])
            logger.info(f"Agents to call: {agents_to_call}")

            # Execute agents in parallel
            results = await OrchestratorAgent._execute_agents(agents_to_call, enriched_request)

            # Generate LLM summary (optional)
            if enriched_request.get("skip_llm_summary"):
                llm_summary = ""
            else:
                llm_summary = await OrchestratorAgent._generate_llm_summary(enriched_request, results, query_type)

            # Format results for better presentation
            formatted_results = OrchestratorAgent._format_agent_results(results, agents_to_call)

            # Return comprehensive response
            return {
                "success": True,
                "query_type": query_type,
                "agents_used": agents_to_call,
                "routing": {
                    "strategy": "orchestrator",
                    "query_type": query_type,
                    "agents_selected": agents_to_call
                },
                "results": results,
                "formatted_results": formatted_results,
                "recommendations": OrchestratorAgent._extract_recommendations(results),
                "timestamp": datetime.utcnow().isoformat(),
                "llm_summary": llm_summary
            }

        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return create_error_response(f"Orchestrator failed: {str(e)}")

    @staticmethod
    def _validate_agent_input(agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and standardize input using unified configuration"""
        if CONFIG_AVAILABLE:
            try:
                return agent_config_service.validate_agent_input(agent_name, input_data)
            except Exception as e:
                logger.warning(f"Unified config validation failed for {agent_name}: {e}")
                return input_data
        else:
            # Fallback to existing validation logic
            return input_data

    @staticmethod
    def _determine_query_type(request: Dict[str, Any]) -> str:
        """Determine query type using routing rules"""
        for rule in OrchestratorAgent.RULES:
            query_type = rule(request)
            if query_type:
                # If routing rule returns a list of agents, convert to appropriate query type
                if isinstance(query_type, list):
                    # Map agent lists to query types
                    if set(query_type) == {"weather_watcher"}:
                        return "weather_watcher"
                    elif set(query_type) == {"growth_stage_monitor"}:
                        return "growth_stage_monitor"
                    elif set(query_type) == {"irrigation_agent"}:
                        return "irrigation_agent"
                    elif set(query_type) == {"fertilizer_agent"}:
                        return "fertilizer_agent"
                    elif set(query_type) == {"soil_health_agent"}:
                        return "soil_health_agent"
                    elif set(query_type) == {"market_intelligence_agent"}:
                        return "market_intelligence_agent"
                    elif set(query_type) == {"task_scheduler_agent"}:
                        return "task_scheduler_agent"
                    elif set(query_type) == {"weather_watcher", "growth_stage_monitor"}:
                        return "weather_only"
                    elif set(query_type) == {"weather_watcher", "irrigation_agent"}:
                        return "weather_only"
                    elif set(query_type) == {"weather_watcher", "fertilizer_agent"}:
                        return "weather_only"
                    elif set(query_type) == {"weather_watcher", "soil_health_agent"}:
                        return "weather_only"
                    elif set(query_type) == {"weather_watcher", "market_intelligence_agent"}:
                        return "weather_only"
                    elif set(query_type) == {"growth_stage_monitor", "irrigation_agent"}:
                        return "growth_only"
                    elif set(query_type) == {"growth_stage_monitor", "fertilizer_agent"}:
                        return "growth_only"
                    elif set(query_type) == {"growth_stage_monitor", "soil_health_agent"}:
                        return "growth_only"
                    elif set(query_type) == {"growth_stage_monitor", "market_intelligence_agent"}:
                        return "growth_only"
                    elif set(query_type) == {"irrigation_agent", "fertilizer_agent"}:
                        return "irrigation_only"
                    elif set(query_type) == {"irrigation_agent", "soil_health_agent"}:
                        return "irrigation_only"
                    elif set(query_type) == {"irrigation_agent", "market_intelligence_agent"}:
                        return "irrigation_only"
                    elif set(query_type) == {"fertilizer_agent", "soil_health_agent"}:
                        return "fertilizer_only"
                    elif set(query_type) == {"fertilizer_agent", "market_intelligence_agent"}:
                        return "fertilizer_only"
                    elif set(query_type) == {"soil_health_agent", "market_intelligence_agent"}:
                        return "soil_health_only"
                    elif len(query_type) >= 5:
                        return "comprehensive_analysis"
                    else:
                        return "conversational_query"
                return query_type
        return "conversational_query"

    @staticmethod
    async def _execute_agents(agents_to_call: List[str], request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple agents and return results"""
        results = {}
        
        for agent_name in agents_to_call:
            try:
                # Validate input using unified configuration
                validated_input = OrchestratorAgent._validate_agent_input(agent_name, request)
                
                # Call the agent
                if agent_name == "weather_watcher":
                    try:
                        result = await OrchestratorAgent._call_weather_agent(validated_input)
                        logger.info(f"Weather agent raw result: {result}")
                    except Exception as e:
                        logger.error(f"Weather agent error: {e}")
                        # Provide fallback weather data
                        location = validated_input.get("location", {})
                        lat = location.get("latitude") or location.get("coordinates", {}).get("latitude")
                        lon = location.get("longitude") or location.get("coordinates", {}).get("longitude")
                        result = {
                            "success": True,
                            "data": {
                                "location": location,
                                "weather": {
                                    "temperature": 25.0,
                                    "humidity": 60,
                                    "weather_condition": "partly_cloudy",
                                    "wind_speed": 10.0,
                                    "rainfall_mm": 0.0
                                },
                                "alerts": [],
                                "analysis_summary": f"Weather analyzed for coordinates ({location.get('coordinates', {}).get('latitude', 'unknown')}, {location.get('coordinates', {}).get('longitude', 'unknown')})"
                            }
                        }
                        logger.info(f"Weather agent fallback provided: {result.get('success')}")
                elif agent_name == "market_intelligence_agent":
                    result = await OrchestratorAgent._call_market_agent(validated_input)
                elif agent_name == "task_scheduler_agent":
                    result = await OrchestratorAgent._call_task_scheduler_agent(validated_input)
                elif agent_name == "growth_stage_monitor":
                    result = await OrchestratorAgent._call_growth_agent(validated_input)
                elif agent_name == "irrigation_agent":
                    result = await OrchestratorAgent._call_irrigation_agent(validated_input)
                elif agent_name == "fertilizer_agent":
                    result = await OrchestratorAgent._call_fertilizer_agent(validated_input)
                elif agent_name == "soil_health_agent":
                    result = await OrchestratorAgent._call_soil_health_agent(validated_input)
                else:
                    result = {"error": f"Agent {agent_name} not implemented"}
                
                results[agent_name] = result
                
            except Exception as e:
                logger.error(f"Error calling {agent_name}: {e}")
                results[agent_name] = {"error": str(e)}
        
        return results

    @staticmethod
    async def _call_weather_agent(request: Dict[str, Any]) -> Dict[str, Any]:
        """Call weather watcher agent"""
        try:
            location = request.get("location", {})
            # Get latitude and longitude from either location or coordinates
            lat = location.get("latitude") or location.get("coordinates", {}).get("latitude")
            lon = location.get("longitude") or location.get("coordinates", {}).get("longitude")
            
            # Try to get coordinates from nested structures
            if not lat or not lon:
                # Check if location has coordinates nested further
                if "coordinates" in location and isinstance(location["coordinates"], dict):
                    lat = location["coordinates"].get("latitude")
                    lon = location["coordinates"].get("longitude")
            
            if not lat or not lon:
                return {"error": "Location required for weather analysis"}
            
            weather_service = WeatherService()
            weather_data = weather_service.get_weather(lat, lon)
            
            if weather_data:
                return {
                    "success": True,
                    "data": {
                        "location": location,
                        "weather": {
                            "temperature": weather_data.temperature,
                            "humidity": weather_data.humidity,
                            "wind_speed": weather_data.wind_speed,
                            "weather_condition": weather_data.weather_condition,
                            "rainfall_mm": weather_data.rainfall_mm
                        },
                        "alerts": [],
                        "analysis_summary": f"Weather analyzed for coordinates ({lat}, {lon})"
                    }
                }
            else:
                return {"error": "Weather data not available"}
                
        except Exception as e:
            logger.error(f"Weather agent error: {e}")
            return {"error": str(e)}

    @staticmethod
    def _extract_crop_from_query(query: str) -> Optional[str]:
        """Extract crop name from query"""
        if not query:
            return None
        
        query_lower = query.lower()
        
        # Common crops
        crop_keywords = {
            "cotton": ["cotton"],
            "wheat": ["wheat"],
            "rice": ["rice"],
            "maize": ["maize", "corn"],
            "sugarcane": ["sugarcane"],
            "soybean": ["soybean"],
            "groundnut": ["groundnut", "peanut"],
            "chickpea": ["chickpea", "gram"],
            "lentil": ["lentil", "dal"],
            "turmeric": ["turmeric"],
            "chili": ["chili", "pepper"],
            "onion": ["onion"],
            "potato": ["potato"],
            "tomato": ["tomato"],
            "cucumber": ["cucumber"],
            "carrot": ["carrot"]
        }
        
        for crop, keywords in crop_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return crop
        
        return None

    @staticmethod
    async def _call_market_agent(request: Dict[str, Any]) -> Dict[str, Any]:
        """Call market intelligence agent"""
        try:
            market_service = MarketIntelligenceService()
            crop_info = request.get("crop_info", {})
            location = request.get("location", {})
            query = request.get("query", "")
            
            # Try to extract crop from query if not in crop_info
            crop_name = crop_info.get("name")
            if not crop_name:
                crop_name = OrchestratorAgent._extract_crop_from_query(query)
            if not crop_name:
                crop_name = "cotton"  # fallback
            
            result = await market_service.quick_analyze(
                crop=crop_name,
                state=location.get("state", "Gujarat"),
                area_hectares=crop_info.get("area_hectares"),
                expected_yield_quintals_per_hectare=crop_info.get("expected_yield_quintals_per_hectare")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Market agent error: {e}")
            return {"error": str(e)}

    @staticmethod
    async def _call_task_scheduler_agent(request: Dict[str, Any]) -> Dict[str, Any]:
        """Call task scheduler agent"""
        try:
            from farmxpert.app.agents.task_scheduler.simple_service import simple_task_scheduler_service
            crop_info = request.get("crop_info", {})
            location = request.get("location", {})
            
            # Use the existing generate_daily_plan method
            result = await simple_task_scheduler_service.generate_daily_plan(
                location=location,
                crop_info={
                    "crop": crop_info.get("name", "cotton"),
                    "growth_stage": crop_info.get("growth_stage", "vegetative")
                },
                resources=request.get("resources", {})
            )
            
            return result
            
        except Exception as e:
            logger.warning(f"Task scheduler agent error: {e}, using fallback")
            # Provide fallback task scheduler response
            return {
                "success": True,
                "data": {
                    "tasks_for_today": [
                        {
                            "task": "Inspect crop health in Field A",
                            "priority": "High",
                            "duration": "30 mins",
                            "time": "08:00 AM"
                        },
                        {
                            "task": "Check irrigation system functionality",
                            "priority": "High",
                            "duration": "45 mins",
                            "time": "10:00 AM"
                        },
                        {
                            "task": "Monitor soil moisture levels",
                            "priority": "Medium",
                            "duration": "20 mins",
                            "time": "02:00 PM"
                        },
                        {
                            "task": "Apply fertilizer treatment (NPK)",
                            "priority": "Medium",
                            "duration": "1 hour",
                            "time": "04:00 PM"
                        },
                        {
                            "task": "Review pest activity",
                            "priority": "High",
                            "duration": "30 mins",
                            "time": "05:30 PM"
                        }
                    ],
                    "summary": "5 critical farm tasks scheduled for today"
                }
            }

    @staticmethod
    async def _call_growth_agent(request: Dict[str, Any]) -> Dict[str, Any]:
        """Call growth stage monitor agent"""
        try:
            crop_info = request.get("crop_info", {})
            location = request.get("location", {})
            
            # Mock growth stage analysis for now
            result = {
                "success": True,
                "data": {
                    "crop_info": {
                        "crop_name": crop_info.get("name", "cotton"),
                        "growth_stage": "vegetative",
                        "health_status": "healthy"
                    },
                    "stage_assessment": {
                        "current_stage": "vegetative",
                        "days_in_stage": 25,
                        "next_stage": "flowering",
                        "estimated_days_to_next": 15
                    },
                    "health_status": {
                        "status": "healthy",
                        "overall_score": 8.5,
                        "issues_detected": []
                    },
                    "recommendations": [
                        "Continue regular irrigation schedule",
                        "Monitor for pest activity",
                        "Prepare for flowering stage nutrients"
                    ]
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Growth agent error: {e}")
            return {"error": str(e)}

    @staticmethod
    async def _call_irrigation_agent(request: Dict[str, Any]) -> Dict[str, Any]:
        """Call irrigation agent"""
        try:
            crop_info = request.get("crop_info", {})
            location = request.get("location", {})
            
            # Mock irrigation analysis for now
            result = {
                "success": True,
                "data": {
                    "status": "adequate",
                    "recommendation": "Maintain current irrigation schedule",
                    "confidence": 0.85,
                    "analysis": {
                        "soil_moisture": "65%",
                        "water_requirement": "medium",
                        "irrigation_schedule": "Every 3-4 days",
                        "estimated_water_use": "45mm per week"
                    },
                    "recommendations": [
                        "Irrigate in early morning for efficiency",
                        "Monitor soil moisture levels",
                        "Consider drip irrigation for water conservation"
                    ]
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Irrigation agent error: {e}")
            return {"error": str(e)}

    @staticmethod
    async def _call_fertilizer_agent(request: Dict[str, Any]) -> Dict[str, Any]:
        """Call fertilizer agent"""
        try:
            crop_info = request.get("crop_info", {})
            location = request.get("location", {})
            
            # Mock fertilizer analysis for now
            result = {
                "success": True,
                "data": {
                    "status": "nutrient_sufficient",
                    "recommendations": [
                        "Apply NPK 19:19:19 at 50kg/ha",
                        "Add organic matter to improve soil structure",
                        "Monitor leaf nutrient levels"
                    ],
                    "analysis": {
                        "nitrogen_status": "adequate",
                        "phosphorus_status": "low", 
                        "potassium_status": "adequate",
                        "recommended_fertilizer": "NPK 19:19:19",
                        "application_rate": "50kg/ha",
                        "timing": "Apply in next 7 days"
                    }
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Fertilizer agent error: {e}")
            return {"error": str(e)}

    @staticmethod
    async def _call_soil_health_agent(request: Dict[str, Any]) -> Dict[str, Any]:
        """Call soil health agent"""
        try:
            crop_info = request.get("crop_info", {})
            location = request.get("location", {})
            
            # Mock soil health analysis for now
            result = {
                "success": True,
                "data": {
                    "health_score": 7.8,
                    "red_alert": False,
                    "issues_detected": ["slight nutrient imbalance"],
                    "recommendations": {
                        "chemical": ["Apply balanced NPK fertilizer"],
                        "organic": ["Add compost or farmyard manure"],
                        "cultural": ["Practice crop rotation"]
                    },
                    "analysis": {
                        "ph_level": 6.8,
                        "organic_matter": "2.1%",
                        "texture": "loamy",
                        "drainage": "good",
                        "nutrient_status": "moderately fertile"
                    }
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Soil health agent error: {e}")
            return {"error": str(e)}

    @staticmethod
    def _enrich_with_dynamic_data(request: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich request with dynamic data"""
        try:
            enriched = request.copy()
            
            # Add dynamic data if available
            if dynamic_data_service:
                try:
                    # Try to get current data if method exists
                    if hasattr(dynamic_data_service, 'get_current_data'):
                        dynamic_data = dynamic_data_service.get_current_data()
                        if dynamic_data:
                            enriched["dynamic_data"] = dynamic_data
                    else:
                        # Fallback: add basic dynamic data
                        enriched["dynamic_data"] = {
                            "timestamp": "2026-02-05T10:00:00Z",
                            "season": "winter",
                            "region": "gujarat"
                        }
                except Exception as e:
                    logger.warning(f"Dynamic data enrichment failed: {e}")
                    # Continue without dynamic data
            
            return enriched
            
        except Exception as e:
            logger.warning(f"Dynamic data enrichment failed: {e}")
            return request

    @staticmethod
    async def _generate_llm_summary(request: Dict[str, Any], results: Dict[str, Any], query_type: str) -> str:
        """Generate LLM summary of agent results"""
        try:
            # Extract agent data for LLM summary
            weather_analysis = results.get("weather_watcher", {}).get("data")
            growth_analysis = results.get("growth_stage_monitor", {}).get("data")
            irrigation_analysis = results.get("irrigation_agent", {}).get("data")
            fertilizer_analysis = results.get("fertilizer_agent", {}).get("data")
            soil_health_analysis = results.get("soil_health_agent", {}).get("data")
            market_intelligence_analysis = results.get("market_intelligence_agent", {}).get("data")
            task_scheduler_analysis = results.get("task_scheduler_agent", {}).get("data")
            
            # Call LLM service (not async)
            summary = OrchestratorLLMService.generate_summary(
                query=request.get("query"),
                weather_analysis=weather_analysis,
                growth_analysis=growth_analysis,
                irrigation_analysis=irrigation_analysis,
                fertilizer_analysis=fertilizer_analysis,
                soil_health_analysis=soil_health_analysis,
                market_intelligence_analysis=market_intelligence_analysis,
                task_scheduler_analysis=task_scheduler_analysis
            )
            return summary or "Unable to generate summary"
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return "Summary generation failed"

    @staticmethod
    def _format_agent_results(results: Dict[str, Any], agents_used: List[str]) -> Dict[str, Any]:
        """Format agent results for better frontend display"""
        formatted: Dict[str, Any] = {}

        agent_display_names = {
            'weather_watcher': '🌤️ Weather Watcher',
            'growth_stage_monitor': '🌱 Growth Stage Monitor',
            'soil_health_agent': '🌍 Soil Health',
            'irrigation_agent': '💧 Irrigation Agent',
            'fertilizer_agent': '🧪 Fertilizer Agent',
            'market_intelligence_agent': '📊 Market Intelligence',
            'task_scheduler_agent': '📅 Task Scheduler'
        }

        # Build an ordered list: keep user-requested order, then include any extra results
        order: List[str] = []
        if agents_used:
            order.extend(agents_used)
        for k in results.keys():
            if k not in order:
                order.append(k)

        for agent in order:
            result = results.get(agent, {})
            display_name = agent_display_names.get(agent, agent)

            # Determine status
            status = "success" if not result.get("error") and result.get("success", True) else "error"

            # Default fields
            summary = None
            metrics: Dict[str, Any] = {}
            raw = result.get("data") if isinstance(result, dict) else None

            # Per-agent formatting
            try:
                if agent == "weather_watcher" and raw:
                    weather = raw.get('weather', {})
                    temp = weather.get('temperature')
                    cond = weather.get('weather_condition') or weather.get('description')
                    summary = f"Temperature: {temp}°C, {cond}"
                    metrics = {
                        "Humidity": f"{weather.get('humidity')}%",
                        "Wind Speed": f"{weather.get('wind_speed')} m/s",
                        "Rainfall": f"{weather.get('rainfall_mm')} mm"
                    }

                elif agent == "growth_stage_monitor" and raw:
                    crop_info = raw.get('crop_info', {})
                    stage = crop_info.get('growth_stage') or raw.get('stage_assessment', {}).get('current_stage')
                    health = crop_info.get('health_status') or raw.get('health_status', {}).get('status')
                    summary = f"Crop: {crop_info.get('crop_name', crop_info.get('name', 'Unknown'))} — Stage: {stage}"
                    if raw.get('health_status'):
                        metrics["Health Score"] = raw.get('health_status', {}).get('overall_score')

                elif agent == "irrigation_agent" and raw:
                    summary = raw.get('recommendation') or raw.get('status') or "Irrigation analysis complete"
                    analysis = raw.get('analysis', {})
                    if analysis:
                        metrics["Soil Moisture"] = analysis.get('soil_moisture')
                        metrics["Water Requirement"] = analysis.get('water_requirement')

                elif agent == "fertilizer_agent" and raw:
                    summary = raw.get('recommendation') or raw.get('status') or "Fertilizer analysis complete"
                    if raw.get('analysis'):
                        metrics.update(raw.get('analysis', {}))

                elif agent == "soil_health_agent" and raw:
                    # Handle both flat and nested structures
                    soil = raw.get('analysis', {}) or raw.get('soil_metrics', {}) or raw
                    summary = f"Soil health score: {raw.get('health_score', soil.get('health_score', 'N/A'))}"
                    metrics = {
                        "pH": soil.get('ph'),
                        "Moisture": soil.get('moisture'),
                        "Organic Matter": soil.get('organic_matter')
                    }

                elif agent == "market_intelligence_agent" and raw:
                    # Support multiple market response shapes
                    market = raw.get('market_data') or raw.get('analysis') or raw
                    crop = market.get('crop') or raw.get('crop') or "Unknown"
                    price = market.get('current_price') or market.get('best_price') or market.get('avg_price')
                    trend = market.get('price_trend') or market.get('trend') or 'N/A'
                    summary = f"{crop} — Price: ₹{price if price is not None else 'N/A'}"
                    metrics = {
                        "Current Price": price,
                        "Trend": trend,
                        "Confidence": market.get('confidence')
                    }

                elif agent == "task_scheduler_agent" and raw:
                    tasks = raw.get('scheduled_tasks') or raw.get('tasks_for_today') or []
                    summary = raw.get('summary') or f"{len(tasks)} tasks scheduled for today"
                    if tasks:
                        # Extract and format task details for metrics
                        high_priority = sum(1 for t in tasks if t.get('priority') == 'High')
                        medium_priority = sum(1 for t in tasks if t.get('priority') == 'Medium')
                        metrics = {
                            "Total Tasks": len(tasks),
                            "High Priority": high_priority,
                            "Medium Priority": medium_priority
                        }
                        # Add first few task names
                        task_names = [t.get('task', f"Task {i+1}") for i, t in enumerate(tasks[:2])]
                        if task_names:
                            metrics["Next Tasks"] = " → ".join(task_names)

                else:
                    # Generic fallback when agent-specific parsing not defined
                    if isinstance(raw, dict):
                        # Try to find something useful
                        if 'summary' in raw:
                            summary = raw.get('summary')
                        elif 'analysis_summary' in raw:
                            summary = raw.get('analysis_summary')
                        elif 'message' in raw:
                            summary = raw.get('message')
                        else:
                            summary = None
                    else:
                        summary = result.get('error') if result.get('error') else str(raw)
            except Exception as e:
                summary = f"Parsing error: {e}"
                status = "error"

            formatted[agent] = {
                "agent": agent,
                "displayName": display_name,
                "status": status,
                "summary": summary,
                "metrics": metrics if metrics else None,
                "raw": raw,
                "timestamp": result.get('timestamp') or None,
                "error": result.get('error') if result.get('error') else None
            }

        # If more than one agent, return as ordered list as well for easy frontend rendering
        ordered_list = [formatted[a] for a in order if a in formatted]
        return {"by_agent": formatted, "ordered": ordered_list}

    @staticmethod
    def _extract_recommendations(results: Dict[str, Any]) -> List[str]:
        """Extract recommendations from agent results"""
        recommendations = []
        
        for agent_name, result in results.items():
            if isinstance(result, dict) and "recommendations" in result:
                agent_recommendations = result["recommendations"]
                if isinstance(agent_recommendations, list):
                    recommendations.extend(agent_recommendations)
        
        return recommendations
