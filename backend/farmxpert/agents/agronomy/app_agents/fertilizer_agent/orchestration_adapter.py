"""
Orchestration Adapter for Fertilizer Advisor Agent

Bridges the existing fertilizer_advisor.py logic with the new
orchestration-ready input/output models.

This adapter demonstrates how the agent can be called by an
orchestrator while maintaining clean data contracts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
from typing import List

from fertilizer_advisor import fertilizer_agent as legacy_fertilizer_agent
from input_models import FertilizerAdvisorInput
from output_models import (
    FertilizerAdvisorOutput, 
    FertilizerRecommendation,
    NutrientType,
    RDFSource,
    AgentStatus,
    create_blocked_response,
    create_ok_response
)


def convert_input_to_legacy(input_model: FertilizerAdvisorInput) -> dict:
    """Convert orchestration input to legacy fertilizer_agent format"""
    return {
        "crop": input_model.crop_name,
        "growth_stage": input_model.growth_stage,
        "area_acres": input_model.area_acres,
        "soil": {
            "n": input_model.soil.nitrogen_kg_per_acre,
            "p": input_model.soil.phosphorus_kg_per_acre,
            "k": input_model.soil.potassium_kg_per_acre
        },
        "recent_weather": {
            "rain_last_3_days_mm": input_model.weather.rainfall_last_3_days_mm,
            "forecast_next_5_days": input_model.weather.forecast_next_5_days
        }
    }


def convert_legacy_recommendations(
    legacy_recs: List[dict], 
    rdf_source: str
) -> List[FertilizerRecommendation]:
    """Convert legacy recommendations to orchestration format"""
    recommendations = []
    
    for rec in legacy_recs:
        # Map fertilizer to nutrient type
        fertilizer_to_nutrient = {
            "nitrogen_source": NutrientType.NITROGEN,
            "phosphorus_source": NutrientType.PHOSPHORUS,
            "potassium_source": NutrientType.POTASSIUM
        }
        
        nutrient_type = fertilizer_to_nutrient.get(rec["fertilizer"])
        if not nutrient_type:
            continue  # Skip unknown fertilizers
            
        recommendation = FertilizerRecommendation(
            nutrient_type=nutrient_type,
            fertilizer_name=rec["fertilizer"],
            dose_per_acre_kg=rec["dose_per_acre_kg"],
            total_quantity_kg=rec["total_quantity_kg"],
            application_method=rec["application_method"],
            timing="Within 3 days",  # Default timing
            reason=rec["reason"],
            rdf_source=RDFSource(rdf_source),
            recommendation_confidence=rec.get("confidence", 0.0),
            safety_notes=rec.get("safety_notes", [])
        )
        recommendations.append(recommendation)
    
    return recommendations


def fertilizer_advisor_orchestrated(input_model: FertilizerAdvisorInput) -> FertilizerAdvisorOutput:
    """
    Orchestration-ready fertilizer advisor function
    
    This function:
    1. Accepts the orchestration input model
    2. Calls the existing legacy fertilizer agent
    3. Converts the output to orchestration format
    4. Returns structured, machine-readable results
    """
    
    # Convert input to legacy format
    legacy_input = convert_input_to_legacy(input_model)
    
    # Call existing fertilizer advisor logic
    legacy_result = legacy_fertilizer_agent(legacy_input)
    
    # Extract RDF source from first recommendation (if available)
    rdf_source = "generic"  # Default
    if legacy_result.get("recommendations"):
        rdf_source = legacy_result["recommendations"][0].get("rdf_source", "generic")
    
    # Convert based on status
    if legacy_result["status"] == "blocked":
        return create_blocked_response(
            blockers=legacy_result["blockers"],
            request_id=input_model.trigger.request_id,
            farmer_id=input_model.farmer_id,
            field_id=input_model.field_id
        )
    else:
        # Convert recommendations
        recommendations = convert_legacy_recommendations(
            legacy_result["recommendations"],
            rdf_source
        )
        
        return create_ok_response(
            recommendations=recommendations,
            confidence=legacy_result["confidence"],
            alerts=legacy_result["alerts"],
            request_id=input_model.trigger.request_id,
            farmer_id=input_model.farmer_id,
            field_id=input_model.field_id
        )


# Example usage for orchestrator
def example_orchestrator_call():
    """Example of how an orchestrator would call this agent"""
    from input_models import FertilizerAdvisorInput, SoilContext, WeatherContext, TriggerMetadata
    
    # Orchestrator assembles input from various sources
    input_data = FertilizerAdvisorInput(
        farmer_id="farmer_001",
        field_id="field_alpha", 
        crop_name="wheat",
        growth_stage="tillering",
        area_acres=2.5,
        soil=SoilContext(
            nitrogen_kg_per_acre=12.0,
            phosphorus_kg_per_acre=8.0,
            potassium_kg_per_acre=15.0
        ),
        weather=WeatherContext(
            rainfall_last_3_days_mm=5.0,
            forecast_next_5_days=["sunny", "sunny", "cloudy", "sunny", "sunny"]
        ),
        trigger=TriggerMetadata(
            triggered_at=datetime.now(timezone.utc),
            trigger_source="orchestrator",
            request_id="req_12345"
        )
    )
    
    # Orchestrator calls the agent
    result = fertilizer_advisor_orchestrated(input_data)
    
    # Orchestrator processes the result
    if result.status == AgentStatus.BLOCKED:
        print(f"Application blocked: {result.blockers}")
    else:
        print(f"Confidence: {result.confidence}")
        for rec in result.recommendations:
            print(f"Recommend: {rec.fertilizer_name} - {rec.total_quantity_kg}kg")
    
    return result


if __name__ == "__main__":
    # Run example
    result = example_orchestrator_call()
    print("\nFull result:")
    import json
    result_dict = result.model_dump()
    # Convert datetime to string for JSON serialization
    result_dict["generated_at"] = result_dict["generated_at"].isoformat()
    print(json.dumps(result_dict, indent=2, default=str))
