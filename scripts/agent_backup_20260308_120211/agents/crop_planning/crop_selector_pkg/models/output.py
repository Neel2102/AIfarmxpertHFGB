"""
Output Models - Data models for crop advisor system outputs
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import json


@dataclass
class CropRecommendation:
    """Individual crop recommendation"""
    crop: str
    confidence: str
    risk_level: str
    score: float
    category: str  # safest/balanced/higher_risk


@dataclass
class AgentInputsSummary:
    """Summary of agent inputs"""
    weather: Dict[str, Any]
    soil_health: Dict[str, Any]
    irrigation: Dict[str, Any]
    fertilizer: Dict[str, Any]
    market: Dict[str, Any]


@dataclass
class DetailedReasoning:
    """Detailed reasoning for recommendation"""
    weather_impact: str
    soil_impact: str
    water_impact: str
    market_impact: str
    fertilizer_impact: str


@dataclass
class PracticalGuidance:
    """Practical guidance for implementation"""
    sowing_window: str
    seed_requirements: str
    land_preparation: str
    irrigation_schedule: str
    fertilizer_recommendation: str
    expected_challenges: List[str]


@dataclass
class CropAdvisorOutput:
    """Complete output model for crop advisor"""
    recommendation: CropRecommendation
    agent_inputs_summary: AgentInputsSummary
    detailed_reasoning: DetailedReasoning
    all_recommendations: Dict[str, List[Dict[str, Any]]]
    practical_guidance: PracticalGuidance
    next_steps: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "recommendation": asdict(self.recommendation),
            "agent_inputs_summary": asdict(self.agent_inputs_summary),
            "detailed_reasoning": asdict(self.detailed_reasoning),
            "all_recommendations": self.all_recommendations,
            "practical_guidance": asdict(self.practical_guidance),
            "next_steps": self.next_steps,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class SimpleRecommendation:
    """Simple output model for basic recommendations"""
    crop: str
    confidence: str
    score: float
    risk_level: str
    weather_summary: str
    soil_summary: str
    water_summary: str
    market_summary: str
    practical_guidance: str
    next_steps: List[str]
    bottom_line: str


@dataclass
class HumanReadableRecommendation:
    """Human-readable recommendation format"""
    title: str
    location: str
    season: str
    recommended_crop: str
    confidence: str
    risk_level: str
    match_score: float
    current_conditions: Dict[str, str]
    why_best: Dict[str, str]
    practical_guidance: Dict[str, str]
    expected_challenges: List[str]
    next_steps: List[str]
    executive_summary: str


@dataclass
class JSONRecommendation:
    """JSON format recommendation"""
    recommendation: Dict[str, Any]
    agent_inputs_summary: Dict[str, Any]
    detailed_reasoning: Dict[str, Any]
    all_recommendations: Dict[str, List[Dict[str, Any]]]
    practical_guidance: Dict[str, Any]
    next_steps: List[str]
    metadata: Dict[str, Any]


@dataclass
class DetailedRecommendation:
    """Detailed recommendation with all options"""
    primary_recommendation: Dict[str, Any]
    all_recommendations: Dict[str, List[Dict[str, Any]]]
    agent_analysis: Dict[str, Any]
    detailed_reasoning: Dict[str, Any]
    practical_guidance: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    next_steps: List[str]
    alternatives: Dict[str, List[Dict[str, Any]]]


# Output format factories
class OutputFactory:
    """Factory for creating different output formats"""
    
    @staticmethod
    def create_simple_output(recommendation: CropRecommendation, 
                           weather_summary: str,
                           soil_summary: str,
                           water_summary: str,
                           market_summary: str,
                           practical_guidance: str,
                           next_steps: List[str]) -> SimpleRecommendation:
        """Create simple recommendation output"""
        return SimpleRecommendation(
            crop=recommendation.crop,
            confidence=recommendation.confidence,
            score=recommendation.score,
            risk_level=recommendation.risk_level,
            weather_summary=weather_summary,
            soil_summary=soil_summary,
            water_summary=water_summary,
            market_summary=market_summary,
            practical_guidance=practical_guidance,
            next_steps=next_steps,
            bottom_line=f"{recommendation.crop.upper()} is your best choice with {recommendation.score:.1%} match to current conditions."
        )
    
    @staticmethod
    def create_human_output(title: str,
                           location: str,
                           season: str,
                           recommended_crop: str,
                           confidence: str,
                           risk_level: str,
                           match_score: float,
                           current_conditions: Dict[str, str],
                           why_best: Dict[str, str],
                           practical_guidance: Dict[str, str],
                           expected_challenges: List[str],
                           next_steps: List[str],
                           executive_summary: str) -> HumanReadableRecommendation:
        """Create human-readable recommendation output"""
        return HumanReadableRecommendation(
            title=title,
            location=location,
            season=season,
            recommended_crop=recommended_crop,
            confidence=confidence,
            risk_level=risk_level,
            match_score=match_score,
            current_conditions=current_conditions,
            why_best=why_best,
            practical_guidance=practical_guidance,
            expected_challenges=expected_challenges,
            next_steps=next_steps,
            executive_summary=executive_summary
        )
    
    @staticmethod
    def create_json_output(recommendation: Dict[str, Any],
                          agent_inputs_summary: Dict[str, Any],
                          detailed_reasoning: Dict[str, Any],
                          all_recommendations: Dict[str, List[Dict[str, Any]]],
                          practical_guidance: Dict[str, Any],
                          next_steps: List[str],
                          metadata: Dict[str, Any]) -> JSONRecommendation:
        """Create JSON recommendation output"""
        return JSONRecommendation(
            recommendation=recommendation,
            agent_inputs_summary=agent_inputs_summary,
            detailed_reasoning=detailed_reasoning,
            all_recommendations=all_recommendations,
            practical_guidance=practical_guidance,
            next_steps=next_steps,
            metadata=metadata
        )
    
    @staticmethod
    def create_detailed_output(primary_recommendation: Dict[str, Any],
                              all_recommendations: Dict[str, List[Dict[str, Any]]],
                              agent_analysis: Dict[str, Any],
                              detailed_reasoning: Dict[str, Any],
                              practical_guidance: Dict[str, Any],
                              risk_assessment: Dict[str, Any],
                              next_steps: List[str],
                              alternatives: Dict[str, List[Dict[str, Any]]]) -> DetailedRecommendation:
        """Create detailed recommendation output"""
        return DetailedRecommendation(
            primary_recommendation=primary_recommendation,
            all_recommendations=all_recommendations,
            agent_analysis=agent_analysis,
            detailed_reasoning=detailed_reasoning,
            practical_guidance=practical_guidance,
            risk_assessment=risk_assessment,
            next_steps=next_steps,
            alternatives=alternatives
        )
