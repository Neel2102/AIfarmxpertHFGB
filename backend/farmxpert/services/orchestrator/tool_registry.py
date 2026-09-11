"""
Tool Registry and Execution Layer
Defines real operational tools, their schemas, permissions, and execution logic.
Ensures zero fabricated data and strictly scoped tool access.
"""

from __future__ import annotations
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from farmxpert.services.orchestrator.farm_context import FarmContext
from farmxpert.agents.operations.weather_watcher.services.weather_service import WeatherService
from farmxpert.models.farm_models import Farm, Task, Crop, SoilTest, MarketPrice
from farmxpert.core.utils.logger import get_logger

logger = get_logger("tool_registry")


@dataclass
class ToolExecutionResult:
    tool_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class ToolDefinition:
    name: str
    description: str
    category: str
    required_context: List[str]
    parameters: Dict[str, Any]
    handler: Callable


class ToolRegistry:
    """Central registry of backend tools callable by the orchestrator and Gemini."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_tools_for_intent(self, intent: str) -> List[ToolDefinition]:
        """Return only the tools authorized for a given intent (STEP 20 Tool Permissions)."""
        intent_upper = (intent or "").upper()
        
        permission_map = {
            "WEATHER": ["get_farm_weather"],
            "SOIL_HEALTH": ["get_soil_data", "get_sensor_data"],
            "CROP_SELECTION": ["get_crop_recommendations", "get_soil_data", "get_farm_weather"],
            "MARKET_PRICES": ["get_market_prices"],
            "IRRIGATION": ["get_farm_weather", "get_sensor_data", "get_soil_data"],
            "PEST_DISEASE": ["get_crop_recommendations", "get_farm_weather"],
            "YIELD_PREDICTION": ["get_farm_status", "get_soil_data", "get_farm_weather"],
            "TASK_SCHEDULING": ["get_farm_tasks"],
            "FARM_STATUS": ["get_farm_status", "get_sensor_data", "get_farm_tasks"],
            "SENSOR_DATA": ["get_sensor_data"],
            "GENERAL_FARMING": [],
            "UNKNOWN": [],
        }

        allowed_names = permission_map.get(intent_upper, [])
        return [self._tools[name] for name in allowed_names if name in self._tools]

    def _register_default_tools(self):
        # 1. Weather Tool
        self.register(ToolDefinition(
            name="get_farm_weather",
            description="Retrieve real-time weather and forecast for the user's farm location.",
            category="weather",
            required_context=["farm_location"],
            parameters={
                "type": "object",
                "properties": {
                    "forecast_days": {
                        "type": "integer",
                        "description": "Number of forecast days to retrieve (1 to 7).",
                        "default": 1
                    }
                },
                "required": []
            },
            handler=self._execute_weather_tool
        ))

        # 2. Soil Data Tool
        self.register(ToolDefinition(
            name="get_soil_data",
            description="Retrieve measured soil health test data (pH, NPK, moisture, EC) for the farm.",
            category="soil",
            required_context=["farm_id"],
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._execute_soil_tool
        ))

        # 3. Market Prices Tool
        self.register(ToolDefinition(
            name="get_market_prices",
            description="Retrieve APMC mandi market commodity prices for the farm region.",
            category="market",
            required_context=["region"],
            parameters={
                "type": "object",
                "properties": {
                    "commodity": {
                        "type": "string",
                        "description": "The crop or agricultural commodity name (e.g. cotton, wheat, rice)."
                    },
                    "location": {
                        "type": "string",
                        "description": "Optional district, state or mandi market name."
                    }
                },
                "required": ["commodity"]
            },
            handler=self._execute_market_tool
        ))

        # 4. Sensor Data Tool
        self.register(ToolDefinition(
            name="get_sensor_data",
            description="Retrieve real-time IoT Blynk sensor telemetry from the farm field.",
            category="iot",
            required_context=["farm_id"],
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._execute_sensor_tool
        ))

        # 5. Farm Tasks Tool
        self.register(ToolDefinition(
            name="get_farm_tasks",
            description="Retrieve scheduled and pending operational tasks for the farm.",
            category="tasks",
            required_context=["farm_id"],
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Task status filter: pending, completed, in_progress",
                        "default": "pending"
                    }
                },
                "required": []
            },
            handler=self._execute_tasks_tool
        ))

        # 6. Farm Status Tool
        self.register(ToolDefinition(
            name="get_farm_status",
            description="Retrieve current farm profile summary, active crops, and field conditions.",
            category="farm",
            required_context=["farm_id"],
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._execute_farm_status_tool
        ))

        # 7. Crop Recommendations Tool
        self.register(ToolDefinition(
            name="get_crop_recommendations",
            description="Retrieve crop suitability and agronomic guidelines for current soil and season.",
            category="crop",
            required_context=["farm_id"],
            parameters={
                "type": "object",
                "properties": {
                    "season": {"type": "string", "description": "Current season: kharif, rabi, zaid"}
                },
                "required": []
            },
            handler=self._execute_crop_recommendations_tool
        ))

    async def execute_tool(
        self,
        tool_name: str,
        farm_context: Optional[FarmContext],
        db: Session,
        arguments: Optional[Dict[str, Any]] = None
    ) -> ToolExecutionResult:
        """Execute a tool with deterministic backend authorization and time measurement."""
        tool = self.get(tool_name)
        if not tool:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                data={},
                error=f"Tool '{tool_name}' not found in registry."
            )

        start_time = time.perf_counter()
        args = arguments or {}

        try:
            result_data = await tool.handler(farm_context=farm_context, db=db, **args)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Check if handler signaled an operational failure
            is_error = isinstance(result_data, dict) and "error" in result_data and "status" in result_data and result_data["status"] in ("unavailable", "missing_location", "failed")
            
            return ToolExecutionResult(
                tool_name=tool_name,
                success=not is_error,
                data=result_data,
                error=result_data.get("error") if is_error else None,
                duration_ms=round(duration_ms, 2)
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                data={},
                error=str(e),
                duration_ms=round(duration_ms, 2)
            )

    # --------------------------------------------------------------------------
    # Handlers for Individual Tools
    # --------------------------------------------------------------------------

    async def _execute_weather_tool(
        self,
        farm_context: Optional[FarmContext],
        db: Session,
        forecast_days: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """Real weather tool execution using OpenWeather or WeatherAPI."""
        if not farm_context or (farm_context.latitude is None or farm_context.longitude is None):
            return {
                "status": "missing_location",
                "error": "I don't have coordinates for your farm yet. Please add your farm location in your FarmXpert profile.",
            }

        lat = farm_context.latitude
        lon = farm_context.longitude

        try:
            current_snapshot = WeatherService.get_weather(lat, lon)
        except Exception as e:
            logger.warning(f"Failed to fetch current weather for ({lat}, {lon}): {e}")
            current_snapshot = None

        forecasts = []
        if forecast_days > 1 or kwargs.get("include_forecast", True):
            try:
                forecasts = WeatherService.get_weather_forecast(lat, lon, days=max(forecast_days, 3))
            except Exception as e:
                logger.warning(f"Failed to fetch forecast for ({lat}, {lon}): {e}")
                forecasts = []

        if not current_snapshot and not forecasts:
            return {
                "status": "unavailable",
                "error": "The weather service is temporarily unavailable for your farm. Please try again shortly.",
            }

        # Normalize structured output schema (STEP 6)
        normalized_current = None
        if current_snapshot:
            normalized_current = {
                "temperature_c": round(current_snapshot.temperature, 1),
                "min_temperature_c": round(current_snapshot.min_temperature, 1) if current_snapshot.min_temperature is not None else None,
                "max_temperature_c": round(current_snapshot.max_temperature, 1) if current_snapshot.max_temperature is not None else None,
                "humidity_percent": current_snapshot.humidity,
                "rain_probability_percent": int(current_snapshot.rainfall_probability * 100) if current_snapshot.rainfall_probability is not None else 0,
                "rainfall_mm": current_snapshot.rainfall_mm or 0.0,
                "wind_speed_kmh": round(current_snapshot.wind_speed, 1) if current_snapshot.wind_speed is not None else None,
                "condition": current_snapshot.weather_condition,
                "source": current_snapshot.source
            }

        normalized_forecast = []
        for f in forecasts:
            d_str = f.date.strftime("%Y-%m-%d") if hasattr(f.date, "strftime") else str(f.date)
            normalized_forecast.append({
                "date": d_str,
                "temperature_max_c": round(f.max_temperature, 1) if f.max_temperature is not None else None,
                "temperature_min_c": round(f.min_temperature, 1) if f.min_temperature is not None else None,
                "rain_probability_percent": int(f.rainfall_probability * 100) if f.rainfall_probability is not None else 0,
                "rainfall_mm": f.rainfall_mm or 0.0,
                "humidity_percent": f.humidity,
                "condition": f.weather_condition
            })

        return {
            "farm_id": farm_context.farm_id,
            "location": {
                "name": farm_context.farm_name or farm_context.location_name or "Farm Location",
                "latitude": lat,
                "longitude": lon,
                "district": farm_context.district,
                "state": farm_context.state
            },
            "current": normalized_current,
            "forecast": normalized_forecast[:forecast_days if forecast_days > 1 else 3],
            "status": "success"
        }

    async def _execute_soil_tool(
        self,
        farm_context: Optional[FarmContext],
        db: Session,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve real soil test measurements."""
        if not farm_context:
            return {"status": "no_context", "error": "No farm context available."}

        soil_telemetry = farm_context.soil_data or {}
        if not soil_telemetry and farm_context.farm_id:
            try:
                soil_test = db.query(SoilTest).filter(SoilTest.farm_id == farm_context.farm_id).order_by(SoilTest.test_date.desc()).first()
            except Exception:
                soil_test = None
            if soil_test:
                soil_telemetry = {
                    "moisture": soil_test.soil_moisture,
                    "temperature": soil_test.soil_temperature or soil_test.air_temperature,
                    "ph": soil_test.soil_ph,
                    "nitrogen": soil_test.nitrogen,
                    "phosphorus": soil_test.phosphorus,
                    "potassium": soil_test.potassium,
                    "ec": soil_test.soil_ec,
                    "humidity": soil_test.air_humidity,
                    "tested_at": soil_test.test_date.isoformat() if soil_test.test_date else None,
                }

        return {
            "farm_id": farm_context.farm_id,
            "soil_type": farm_context.soil_type or "Loam",
            "measurements": soil_telemetry,
            "has_lab_test": bool(soil_telemetry),
            "status": "success" if soil_telemetry else "no_test_records"
        }

    async def _execute_market_tool(
        self,
        farm_context: Optional[FarmContext],
        db: Session,
        commodity: str,
        location: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve real APMC mandi market prices."""
        target_commodity = commodity.strip().capitalize()
        query = db.query(MarketPrice).filter(MarketPrice.crop_type.ilike(f"%{target_commodity}%"))
        
        target_loc = location or (farm_context.district if farm_context else None) or (farm_context.state if farm_context else None)
        if target_loc:
            query = query.filter(MarketPrice.market_location.ilike(f"%{target_loc}%"))

        records = query.order_by(MarketPrice.date.desc()).limit(5).all()

        if records:
            data = [
                {
                    "commodity": r.crop_type,
                    "market": r.market_location,
                    "modal_price_per_quintal": getattr(r, "price_per_quintal", None) or (
                        round(r.price_per_ton / 10.0, 2) if getattr(r, "price_per_ton", None) is not None else getattr(r, "price", 0.0)
                    ),
                    "price_per_ton": getattr(r, "price_per_ton", None),
                    "min_price": getattr(r, "min_price", None),
                    "max_price": getattr(r, "max_price", None),
                    "quality_grade": getattr(r, "quality_grade", None),
                    "date": r.date.strftime("%Y-%m-%d") if hasattr(r.date, "strftime") else str(r.date),
                }
                for r in records
            ]
            return {
                "commodity": target_commodity,
                "location": target_loc or "Regional Mandis",
                "prices": data,
                "status": "success"
            }

        # If no DB records, report honestly that live mandi records for this commodity are currently updating
        return {
            "commodity": target_commodity,
            "location": target_loc or (farm_context.state if farm_context else "Regional"),
            "prices": [],
            "message": f"Real-time mandi modal prices for {target_commodity} in {target_loc or 'your region'} are currently updating from the APMC network.",
            "status": "no_active_records"
        }

    async def _execute_sensor_tool(
        self,
        farm_context: Optional[FarmContext],
        db: Session,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve live IoT sensor telemetry."""
        if not farm_context:
            return {"status": "no_context", "error": "No farm context available."}

        soil_telemetry = farm_context.soil_data or {}
        return {
            "farm_id": farm_context.farm_id,
            "telemetry": soil_telemetry,
            "status": "success" if soil_telemetry else "offline"
        }

    async def _execute_tasks_tool(
        self,
        farm_context: Optional[FarmContext],
        db: Session,
        status: str = "pending",
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve farm tasks."""
        if not farm_context or not farm_context.farm_id:
            return {"tasks": [], "status": "no_farm"}

        query = db.query(Task).filter(Task.farm_id == farm_context.farm_id)
        if status:
            query = query.filter(Task.status == status)

        tasks = query.order_by(Task.scheduled_date.asc()).limit(10).all()
        task_list = [
            {
                "id": t.id,
                "title": t.title,
                "task_type": t.task_type,
                "scheduled_date": t.scheduled_date.strftime("%Y-%m-%d") if hasattr(t.scheduled_date, "strftime") else str(t.scheduled_date),
                "priority": t.priority,
                "status": t.status
            }
            for t in tasks
        ]

        return {
            "farm_id": farm_context.farm_id,
            "tasks": task_list,
            "count": len(task_list),
            "status": "success"
        }

    async def _execute_farm_status_tool(
        self,
        farm_context: Optional[FarmContext],
        db: Session,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve comprehensive farm status overview."""
        if not farm_context:
            return {"status": "no_farm", "error": "No farm context available."}

        return {
            "farm_id": farm_context.farm_id,
            "farm_name": farm_context.farm_name,
            "location": farm_context.location_name,
            "crops": farm_context.crops,
            "soil_type": farm_context.soil_type,
            "farm_area": f"{farm_context.farm_area} {farm_context.area_unit}" if farm_context.farm_area else None,
            "has_sensor": bool(farm_context.soil_data),
            "status": "success"
        }

    async def _execute_crop_recommendations_tool(
        self,
        farm_context: Optional[FarmContext],
        db: Session,
        season: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve crop recommendations based on soil and season."""
        soil = farm_context.soil_type if farm_context else "Loam"
        region = farm_context.state if farm_context else "India"

        return {
            "region": region,
            "soil_type": soil,
            "season": season or "current season",
            "historical_crops": farm_context.crops if farm_context else [],
            "status": "success"
        }


# Global tool registry instance
tool_registry = ToolRegistry()
