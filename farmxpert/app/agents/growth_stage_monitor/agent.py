"""
Growth Stage Monitor Agent
Core logic for crop growth stage and health monitoring
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .services.growth_stage_engine import GrowthStageEngine
from .services.growth_health_engine import GrowthHealthEngine
from .services.growth_weather_corelation import GrowthWeatherCorrelation
from .services.llm_services import GrowthLLMService
from .models.input_models import GrowthMonitorInput, CropInfo, CropImage, GrowthLocation
from .models.output_models import GrowthMonitorOutput
from farmxpert.app.shared.utils import logger, create_success_response, create_error_response
from farmxpert.app.shared.exceptions import GrowthAnalysisException, LLMServiceException


class GrowthStageMonitorAgent:
    """Crop growth stage and health monitoring agent"""
    
    @staticmethod
    def analyze_growth(crop_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze crop growth stage and health
        
        Args:
            crop_data: Dictionary containing crop information, location, and images
            
        Returns:
            Dictionary with growth analysis results and recommendations
        """
        try:
            logger.info(f"Analyzing crop growth for: {crop_data.get('farmer_id', 'unknown')}")
            
            # Convert dict to GrowthMonitorInput
            input_data = GrowthStageMonitorAgent._dict_to_input_model(crop_data)
            
            # Step 1: Estimate growth stage
            logger.info("Estimating growth stage...")
            stage_assessment = GrowthStageEngine.estimate_stage(input_data)
            
            # Step 2: Evaluate health
            logger.info("Evaluating crop health...")
            health_status, alerts = GrowthHealthEngine.evaluate(input_data, stage_assessment)
            
            # Step 3: Weather correlation (if health issues detected)
            if health_status.status != "NORMAL" and crop_data.get("weather_data"):
                logger.info("Performing weather correlation analysis...")
                try:
                    # Create weather summary from weather data
                    weather_summary = GrowthStageMonitorAgent._create_weather_summary(
                        crop_data["weather_data"], input_data.field_id
                    )
                    
                    health_status, alerts = GrowthWeatherCorrelation.correlate(
                        stage_assessment, health_status, alerts, weather_summary
                    )
                except Exception as e:
                    logger.warning(f"Weather correlation failed: {e}")
            
            # Step 4: Generate final output
            output = GrowthMonitorOutput(
                stage_assessment=stage_assessment,
                health_status=health_status,
                alerts=alerts,
                recommendation=None,
                generated_at=datetime.now()
            )
            
            # Step 5: Generate LLM explanation if alerts exist
            llm_explanation = None
            if alerts:
                try:
                    logger.info("Generating LLM explanation...")
                    llm_explanation = GrowthLLMService.explain_growth_alert(
                        crop_name=input_data.crop.crop_name,
                        stage=stage_assessment,
                        health=health_status,
                        alert=alerts[0]
                    )
                except Exception as e:
                    logger.warning(f"LLM explanation failed: {e}")
                    llm_explanation = "Unable to generate explanation"
            
            # Prepare response data
            response_data = {
                "farmer_id": input_data.farmer_id,
                "field_id": input_data.field_id,
                "crop_info": {
                    "crop_name": input_data.crop.crop_name,
                    "variety": input_data.crop.variety,
                    "days_since_sowing": (input_data.triggered_at - input_data.crop.sowing_date).days if input_data.crop.sowing_date else 0,
                },
                "location": {
                    "latitude": input_data.location.latitude,
                    "longitude": input_data.location.longitude,
                    "district": input_data.location.district,
                    "state": input_data.location.state
                },
                "stage_assessment": stage_assessment.model_dump(),
                "health_status": health_status.model_dump(),
                "alerts": [alert.model_dump() for alert in alerts],
                "alert_count": len(alerts),
                "llm_explanation": llm_explanation,
                "analysis_summary": f"Growth analysis completed for {input_data.crop.crop_name} crop"
            }
            
            return create_success_response(
                response_data,
                message=f"Growth analysis completed for {input_data.crop.crop_name} crop",
                metadata={
                    "crop_name": input_data.crop.crop_name,
                    "current_stage": stage_assessment.current_stage,
                    "health_status": health_status.status,
                    "alert_count": len(alerts)
                }
            )
            
        except GrowthAnalysisException as e:
            logger.error(f"Growth analysis error: {e.message}")
            return create_error_response(
                e.error_code or "GROWTH_ANALYSIS_ERROR",
                e.message,
                e.details
            )
        except Exception as e:
            logger.error(f"Unexpected error in growth analysis: {e}")
            return create_error_response(
                "UNEXPECTED_ERROR",
                f"Unexpected error: {str(e)}",
                {"crop_data": crop_data}
            )
    
    @staticmethod
    def _dict_to_input_model(crop_data: Dict[str, Any]) -> GrowthMonitorInput:
        """Convert dictionary to GrowthMonitorInput model"""
        try:
            return GrowthMonitorInput(
                farmer_id=crop_data["farmer_id"],
                field_id=crop_data["field_id"],
                crop=CropInfo(
                    crop_name=crop_data["crop"]["crop_name"],
                    sowing_date=crop_data["crop"]["sowing_date"],
                    variety=crop_data["crop"].get("variety")
                ),
                location=GrowthLocation(
                    latitude=crop_data["location"]["latitude"],
                    longitude=crop_data["location"]["longitude"],
                    district=crop_data["location"].get("district"),
                    state=crop_data["location"].get("state"),
                    country=crop_data["location"].get("country", "India")
                ),
                images=[
                    CropImage(
                        image_id=img["image_id"],
                        image_url=img["image_url"],
                        captured_at=img["captured_at"],
                        angle=img.get("angle")
                    ) for img in crop_data.get("images", [])
                ],
                triggered_at=crop_data.get("triggered_at", datetime.now())
            )
        except KeyError as e:
            raise GrowthAnalysisException(
                f"Missing required field: {str(e)}",
                crop_type=crop_data.get("crop", {}).get("crop_name", "unknown")
            )
    
    @staticmethod
    def _create_weather_summary(weather_data: Dict[str, Any], field_id: str):
        """Create weather summary from weather data"""
        from .models.weather_summary_models import WeatherSummary
        
        return WeatherSummary(
            location_id=field_id,
            start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d"),
            avg_temperature=weather_data.get("temperature", 25.0),
            total_rainfall_mm=weather_data.get("rainfall_mm", 0.0),
            heat_stress_days=1 if weather_data.get("temperature", 0) > 35 else 0,
            heavy_rain_days=1 if weather_data.get("rainfall_mm", 0) > 10 else 0,
            dry_days=1 if weather_data.get("rainfall_mm", 0) < 2 else 0,
            confidence=0.9
        )
