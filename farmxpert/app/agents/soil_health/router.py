"""
Soil Health Agent Router
API endpoints for soil health analysis
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
from farmxpert.app.agents.soil_health.services.soil_health_service import SoilHealthAnalysisService
from farmxpert.app.agents.soil_health.models.input_models import SoilHealthInput, QuickSoilCheckInput
from farmxpert.app.agents.soil_health.models.output_models import SoilHealthResponse
from farmxpert.app.shared.utils import logger, create_success_response, create_error_response
from farmxpert.services.providers.blynk_iot_provider import blynk_iot_provider
from farmxpert.services.gemini_service import gemini_service

router = APIRouter()


@router.get("/iot/latest")
async def get_latest_iot_soil_data():
    """Fetch latest soil sensor readings from hardware IoT (Blynk)."""
    try:
        payload = await blynk_iot_provider.get_soil_sensor_payload()
        if not payload.get("success"):
            return create_error_response(
                "IOT_UNAVAILABLE",
                payload.get("error") or "IoT provider unavailable",
                {"provider": "Blynk"},
            )
        return create_success_response(payload)
    except Exception as e:
        return create_error_response(
            "IOT_FETCH_FAILED",
            str(e),
            {"provider": "Blynk"},
        )

@router.get("/")
async def soil_health_info():
    """Get soil health agent information"""
    return {
        "name": "Soil Health Agent",
        "description": "Analyzes soil health parameters and provides recommendations",
        "version": "2.0.0",
        "architecture": "Optimized for FarmXpert modular monolith",
        "capabilities": [
            "Soil pH analysis",
            "Nutrient level assessment (N, P, K)",
            "Salinity detection",
            "Chemical and organic recommendations",
            "Health scoring",
            "Crop-specific analysis",
            "Location-aware recommendations"
        ],
        "models": {
            "input": ["SoilHealthInput", "QuickSoilCheckInput"],
            "output": ["SoilHealthAnalysis", "QuickSoilCheckResult"]
        },
        "services": ["SoilHealthAnalysisService"],
        "constraints": ["soil_constraints.py with crop-specific thresholds"],
        "endpoints": [
            "/agents/soil_health/analyze",
            "/agents/soil_health/quick_check"
        ]
    }

@router.post("/analyze")
async def analyze_soil(request: Dict[str, Any]):
    """
    Comprehensive soil health analysis
    
    Request format:
    {
        "location": {
            "latitude": 21.7051,
            "longitude": 72.9959,
            "district": "Ankleshwar",
            "state": "Gujarat"
        },
        "soil_data": {
            "pH": 6.5,
            "nitrogen": 50,
            "phosphorus": 20,
            "potassium": 100,
            "electrical_conductivity": 1.5,
            "moisture": 35.0,
            "temperature": 18.0
        },
        "crop_type": "cotton",
        "growth_stage": "vegetative"
    }
    """
    try:
        logger.info("🌱 Received comprehensive soil health analysis request")
        
        # Validate and parse input
        try:
            # Create location input
            from farmxpert.app.agents.soil_health.models.input_models import LocationInput, SoilSensorData
            from farmxpert.app.agents.soil_health.models.input_models import SoilHealthInput

            location_obj = request.get("location")
            if not isinstance(location_obj, dict):
                location_obj = {}

            latitude = location_obj.get("latitude")
            longitude = location_obj.get("longitude")
            if latitude is None or longitude is None:
                latitude = 23.2144
                longitude = 72.6843

            location_input = LocationInput(
                latitude=float(latitude),
                longitude=float(longitude),
                district=location_obj.get("district", "Gandhinagar"),
                state=location_obj.get("state", "Gujarat"),
                field_id=request.get("field_id"),
            )
            
            # Create soil sensor data
            soil_data = request.get("soil_data")
            if not isinstance(soil_data, dict):
                soil_data = {}

            # Support flat payloads where soil params are at top-level
            if not soil_data:
                soil_data = request if isinstance(request, dict) else {}

            # Normalize common key variants
            if "pH" not in soil_data and "ph" in soil_data:
                soil_data["pH"] = soil_data.get("ph")

            required_keys = [
                "pH",
                "nitrogen",
                "phosphorus",
                "potassium",
                "electrical_conductivity",
            ]
            missing = [k for k in required_keys if soil_data.get(k) is None]
            iot_status: Dict[str, Any] = {"attempted": False}
            if missing:
                # Try to fetch from Hardware IoT (Blynk) before falling back
                try:
                    iot_status["attempted"] = True
                    iot_payload = await blynk_iot_provider.get_soil_sensor_payload()
                    iot_status["provider"] = "Blynk"
                    iot_status["success"] = bool(iot_payload.get("success"))
                    iot_status["error"] = iot_payload.get("error")
                    iot_status["fetched_at"] = iot_payload.get("fetched_at")

                    if iot_payload.get("success") and isinstance(iot_payload.get("soil_data"), dict):
                        # Merge IoT data into soil_data only where missing
                        for k in required_keys + ["moisture", "temperature", "organic_matter"]:
                            if soil_data.get(k) is None and iot_payload["soil_data"].get(k) is not None:
                                soil_data[k] = iot_payload["soil_data"].get(k)

                        missing = [k for k in required_keys if soil_data.get(k) is None]
                except Exception as e:
                    iot_status["attempted"] = True
                    iot_status["success"] = False
                    iot_status["error"] = str(e)

            if missing:
                crop_type = request.get("crop_type") if isinstance(request, dict) else None
                growth_stage = request.get("growth_stage") if isinstance(request, dict) else None

                llm_response = None
                try:
                    prompt = f"""
You are an agricultural assistant. The farmer asked about improving soil health.

Context:
- Location: {location_obj.get('district', 'Gandhinagar')}, {location_obj.get('state', 'Gujarat')} (IIT Gandhinagar default)
- Crop: {crop_type or 'unknown'}
- Growth stage: {growth_stage or 'unknown'}
- Available IoT status: {iot_status}
- Missing soil readings: {', '.join(missing)}

Task:
Write a natural 2-3 sentence response (no bullets, no headings) that:
1) Explains what data is needed and why.
2) If IoT is available, ask to keep device online / configure token.
3) If not, ask for soil test values.
Keep it concise.
"""
                    llm_response = await gemini_service.generate_response(
                        prompt,
                        {
                            "agent": "soil_health",
                            "task": "soil_health_missing_values",
                            "concise": True,
                        },
                    )
                    if isinstance(llm_response, str):
                        llm_response = llm_response.strip().strip('"')
                        if not llm_response:
                            llm_response = None
                except Exception:
                    llm_response = None

                guidance = {
                    "response": llm_response
                    or "To improve soil health, I need your soil readings (pH, N, P, K, EC). If your IoT device is online, I can pull them automatically; otherwise share a soil test report. Once I have values, I’ll give precise fertilizer and amendment steps.",
                    "location": {
                        "district": location_obj.get("district", "Gandhinagar"),
                        "state": location_obj.get("state", "Gujarat"),
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                        "name": "IIT Gandhinagar",
                    },
                    "missing_fields": missing,
                    "iot": iot_status,
                    "next_steps": [
                        "If you have a soil test report: share pH, N, P, K, EC.",
                        "If you have IoT sensors: set BLYNK_TOKEN in backend .env and keep device online.",
                        "If neither: share crop, growth stage, and last fertilizer applied.",
                    ],
                }
                resp = create_success_response(guidance)
                # Frontend prefers top-level 'response' over generic 'message'
                resp["response"] = guidance.get("response")
                return resp

            soil_sensor_data = SoilSensorData(
                pH=soil_data["pH"],
                nitrogen=soil_data["nitrogen"],
                phosphorus=soil_data["phosphorus"],
                potassium=soil_data["potassium"],
                electrical_conductivity=soil_data["electrical_conductivity"],
                moisture=soil_data.get("moisture"),
                temperature=soil_data.get("temperature"),
                organic_matter=soil_data.get("organic_matter")
            )
            
            # Create soil health input
            soil_input = SoilHealthInput(
                location=location_input,
                soil_data=soil_sensor_data,
                crop_type=request.get("crop_type"),
                growth_stage=request.get("growth_stage"),
                triggered_at=datetime.now(),
                request_source=request.get("request_source", "api"),
                field_id=request.get("field_id")
            )
            
        except Exception as e:
            return create_error_response(
                "INVALID_INPUT",
                f"Invalid input format: {str(e)}",
                {"request": request}
            )
        
        # Perform analysis
        analysis = SoilHealthAnalysisService.analyze_soil_health(soil_input)

        user_question = request.get("query") if isinstance(request, dict) else None
        crop_type = request.get("crop_type") if isinstance(request, dict) else None
        growth_stage = request.get("growth_stage") if isinstance(request, dict) else None
        llm_success_response = None
        try:
            prompt = f"""
You are an agricultural assistant.

Farmer question: {user_question or 'How can I improve my soil health?'}

Context:
- Location: {location_obj.get('district', 'Gandhinagar')}, {location_obj.get('state', 'Gujarat')}
- Crop: {crop_type or 'unknown'}
- Growth stage: {growth_stage or 'unknown'}

Soil readings:
- pH: {soil_data.get('pH')}
- Nitrogen: {soil_data.get('nitrogen')}
- Phosphorus: {soil_data.get('phosphorus')}
- Potassium: {soil_data.get('potassium')}
- Electrical conductivity: {soil_data.get('electrical_conductivity')}
- Moisture: {soil_data.get('moisture')}
- Temperature: {soil_data.get('temperature')}

Analysis output (JSON): {analysis.dict()}

Task:
Write a natural 2-3 sentence answer (no bullets, no headings) directly addressing the farmer question. Use the values above and the analysis to give practical next steps.
"""
            llm_success_response = await gemini_service.generate_response(
                prompt,
                {
                    "agent": "soil_health",
                    "task": "soil_health_success",
                    "concise": True,
                },
            )
            if isinstance(llm_success_response, str):
                llm_success_response = llm_success_response.strip().strip('"')
                if not llm_success_response:
                    llm_success_response = None
        except Exception:
            llm_success_response = None

        resp = create_success_response(
            analysis.dict(),
            message=llm_success_response or "Comprehensive soil health analysis completed successfully",
        )
        resp["response"] = llm_success_response or resp.get("message")
        return resp
        
    except Exception as e:
        logger.error(f"Soil health analysis error: {e}")
        return create_error_response(
            "SOIL_HEALTH_ANALYSIS_ERROR",
            str(e),
            {"request": request}
        )

@router.post("/quick_check")
async def quick_soil_check(request: Dict[str, Any]):
    """
    Quick soil health check with minimal parameters
    
    Request format:
    {
        "pH": 6.5,
        "nitrogen": 50,
        "phosphorus": 20,
        "potassium": 100,
        "electrical_conductivity": 1.5,
        "moisture": 35.0,
        "temperature": 18.0
    }
    """
    try:
        logger.info("🌱 Received quick soil health check")
        
        # Validate and parse input
        try:
            quick_input = QuickSoilCheckInput(**request)
        except Exception as e:
            return create_error_response(
                "INVALID_INPUT",
                f"Invalid input format: {str(e)}",
                {"request": request}
            )
        
        # Perform quick check
        result = SoilHealthAnalysisService.quick_soil_check(quick_input)
        
        return create_success_response(
            result.dict(),
            message="Quick soil health check completed"
        )
        
    except Exception as e:
        logger.error(f"Quick soil check error: {e}")
        return create_error_response(
            "QUICK_SOIL_CHECK_ERROR",
            str(e),
            {"request": request}
        )

@router.get("/health")
async def soil_health_agent_health():
    """Health check for soil health agent"""
    return {
        "status": "healthy",
        "agent": "soil_health_agent",
        "version": "2.0.0",
        "timestamp": "2026-02-03T22:15:00Z",
        "architecture": "FarmXpert modular monolith optimized",
        "capabilities": [
            "soil_ph_analysis",
            "nutrient_assessment", 
            "salinity_detection",
            "recommendation_generation",
            "health_scoring",
            "crop_specific_analysis",
            "location_aware_recommendations"
        ],
        "parameters_monitored": [
            "pH", "nitrogen", "phosphorus", "potassium", 
            "electrical_conductivity", "moisture", "temperature"
        ],
        "supported_crops": [
            "cotton", "wheat", "rice", "maize", "default"
        ],
        "models_loaded": True,
        "constraints_loaded": True,
        "services_active": 1
    }
