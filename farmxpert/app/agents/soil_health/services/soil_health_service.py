"""
Soil Health Analysis Service
Core service for analyzing soil health and generating recommendations
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from farmxpert.app.agents.soil_health.models.input_models import SoilHealthInput, QuickSoilCheckInput
from farmxpert.app.agents.soil_health.models.output_models import (
    SoilHealthAnalysis, SoilIssue, Recommendation, SoilRecommendations,
    HealthScoreBreakdown, QuickSoilCheckResult
)
from farmxpert.app.agents.soil_health.constraints.soil_constraints import (
    SoilIssueType, UrgencyLevel, get_thresholds_for_crop, get_issue_definition,
    HEALTH_SCORE_WEIGHTS, CROP_NUTRIENT_REQUIREMENTS
)
from farmxpert.app.shared.utils import logger


class SoilHealthAnalysisService:
    """Service for comprehensive soil health analysis"""
    
    @staticmethod
    def analyze_soil_health(input_data: SoilHealthInput) -> SoilHealthAnalysis:
        """
        Perform comprehensive soil health analysis
        
        Args:
            input_data: Soil health input with location and sensor data
            
        Returns:
            SoilHealthAnalysis: Comprehensive analysis results
        """
        try:
            logger.info(f"🌱 Starting soil health analysis for field: {input_data.field_id}")
            
            # Get appropriate thresholds for crop type
            crop_type = input_data.crop_type or "default"
            thresholds = get_thresholds_for_crop(crop_type)
            
            # Analyze soil parameters and detect issues
            issues = SoilHealthAnalysisService._detect_soil_issues(
                input_data.soil_data.dict(), thresholds
            )
            
            # Calculate health scores
            health_scores = SoilHealthAnalysisService._calculate_health_scores(
                input_data.soil_data.dict(), thresholds, issues
            )
            
            # Generate recommendations
            recommendations = SoilHealthAnalysisService._generate_recommendations(issues)
            
            # Determine if red alert is needed
            red_alert = any(issue.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL] for issue in issues)
            
            # Create analysis result
            analysis = SoilHealthAnalysis(
                agent="soil_health_agent",
                analysis_id=str(uuid.uuid4()),
                location=input_data.location.dict(),
                soil_data_analyzed=input_data.soil_data,
                health_score=health_scores,
                issues_detected=issues,
                red_alert=red_alert,
                recommendations=recommendations,
                analyzed_at=input_data.triggered_at
            )
            
            logger.info(f"✅ Soil health analysis completed. Health score: {health_scores.overall_score:.1f}/100")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Soil health analysis failed: {e}")
            raise
    
    @staticmethod
    def quick_soil_check(input_data: QuickSoilCheckInput) -> QuickSoilCheckResult:
        """
        Perform quick soil health check
        
        Args:
            input_data: Simplified soil data for quick check
            
        Returns:
            QuickSoilCheckResult: Simplified analysis results
        """
        try:
            logger.info("🌱 Starting quick soil health check")
            
            # Use default thresholds for quick check
            thresholds = get_thresholds_for_crop("default")
            
            # Convert to soil sensor data format
            soil_data_dict = quick_input.dict()
            
            # Detect issues
            issues = SoilHealthAnalysisService._detect_soil_issues(soil_data_dict, thresholds)
            
            # Calculate overall health score
            health_scores = SoilHealthAnalysisService._calculate_health_scores(
                soil_data_dict, thresholds, issues
            )
            
            # Generate top recommendations
            recommendations = SoilHealthAnalysisService._generate_recommendations(issues)
            top_recommendations = [
                f"{rec.name}: {rec.description}" 
                for rec in recommendations.chemical[:2] + recommendations.organic[:1]
            ]
            
            # Determine urgency
            urgency_levels = [issue.urgency for issue in issues]
            urgency = max(urgency_levels) if urgency_levels else UrgencyLevel.LOW
            
            # Determine overall status
            if health_scores.overall_score >= 80:
                overall_status = "excellent"
            elif health_scores.overall_score >= 60:
                overall_status = "good"
            elif health_scores.overall_score >= 40:
                overall_status = "fair"
            else:
                overall_status = "poor"
            
            result = QuickSoilCheckResult(
                health_score=health_scores.overall_score,
                red_alert=urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL],
                issues_count=len(issues),
                overall_status=overall_status,
                urgency=urgency,
                top_recommendations=top_recommendations,
                checked_at=datetime.now()
            )
            
            logger.info(f"✅ Quick soil check completed. Score: {result.health_score:.1f}/100")
            return result
            
        except Exception as e:
            logger.error(f"❌ Quick soil check failed: {e}")
            raise
    
    @staticmethod
    def _detect_soil_issues(soil_data: Dict[str, Any], thresholds: Dict[str, Any]) -> List[SoilIssue]:
        """Detect soil issues based on sensor data and thresholds"""
        issues = []
        
        # Check pH
        pH = soil_data.get("pH", 0)
        pH_thresholds = thresholds.get("pH", {})
        
        if pH < pH_thresholds.get("critical_low", 5.0):
            issues.append(SoilIssue(
                problem=SoilIssueType.ACIDIC_SOIL,
                cause="Highly acidic soil conditions",
                effect="Severe nutrient availability issues and potential metal toxicity",
                severity="critical",
                urgency=UrgencyLevel.CRITICAL
            ))
        elif pH < pH_thresholds.get("warning_low", 5.5):
            issue_def = get_issue_definition(SoilIssueType.ACIDIC_SOIL)
            issues.append(SoilIssue(
                problem=SoilIssueType.ACIDIC_SOIL,
                cause=issue_def.get("cause", ""),
                effect=issue_def.get("effect", ""),
                severity="moderate",
                urgency=issue_def.get("urgency", UrgencyLevel.MEDIUM)
            ))
        elif pH > pH_thresholds.get("critical_high", 9.0):
            issues.append(SoilIssue(
                problem=SoilIssueType.ALKALINE_SOIL,
                cause="Highly alkaline soil conditions",
                effect="Severe micronutrient deficiencies and poor nutrient uptake",
                severity="critical",
                urgency=UrgencyLevel.CRITICAL
            ))
        elif pH > pH_thresholds.get("warning_high", 8.0):
            issue_def = get_issue_definition(SoilIssueType.ALKALINE_SOIL)
            issues.append(SoilIssue(
                problem=SoilIssueType.ALKALINE_SOIL,
                cause=issue_def.get("cause", ""),
                effect=issue_def.get("effect", ""),
                severity="moderate",
                urgency=issue_def.get("urgency", UrgencyLevel.MEDIUM)
            ))
        
        # Check electrical conductivity (salinity)
        EC = soil_data.get("electrical_conductivity", 0)
        EC_thresholds = thresholds.get("electrical_conductivity", {})
        
        if EC > EC_thresholds.get("critical_high", 4.0):
            issues.append(SoilIssue(
                problem=SoilIssueType.HIGH_SALINITY,
                cause="Severe soil salinity",
                effect="Severe osmotic stress and potential crop failure",
                severity="critical",
                urgency=UrgencyLevel.CRITICAL
            ))
        elif EC > EC_thresholds.get("warning_high", 3.0):
            issue_def = get_issue_definition(SoilIssueType.HIGH_SALINITY)
            issues.append(SoilIssue(
                problem=SoilIssueType.HIGH_SALINITY,
                cause=issue_def.get("cause", ""),
                effect=issue_def.get("effect", ""),
                severity="moderate",
                urgency=issue_def.get("urgency", UrgencyLevel.HIGH)
            ))
        
        # Check nutrients
        nutrients = [
            ("nitrogen", SoilIssueType.LOW_NITROGEN),
            ("phosphorus", SoilIssueType.LOW_PHOSPHORUS),
            ("potassium", SoilIssueType.LOW_POTASSIUM)
        ]
        
        for nutrient_name, issue_type in nutrients:
            nutrient_value = soil_data.get(nutrient_name, 0)
            nutrient_thresholds = thresholds.get(f"{nutrient_name}_ppm", {})
            
            if nutrient_value < nutrient_thresholds.get("critical_low", 20):
                issues.append(SoilIssue(
                    problem=issue_type,
                    cause=f"Critical deficiency of {nutrient_name}",
                    effect=f"Severe growth and yield reduction due to {nutrient_name} deficiency",
                    severity="critical",
                    urgency=UrgencyLevel.HIGH
                ))
            elif nutrient_value < nutrient_thresholds.get("warning_low", 30):
                issue_def = get_issue_definition(issue_type)
                issues.append(SoilIssue(
                    problem=issue_type,
                    cause=issue_def.get("cause", ""),
                    effect=issue_def.get("effect", ""),
                    severity="moderate",
                    urgency=issue_def.get("urgency", UrgencyLevel.MEDIUM)
                ))
        
        return issues
    
    @staticmethod
    def _calculate_health_scores(
        soil_data: Dict[str, Any], 
        thresholds: Dict[str, Any], 
        issues: List[SoilIssue]
    ) -> HealthScoreBreakdown:
        """Calculate health scores for different soil parameters"""
        
        # pH score
        pH = soil_data.get("pH", 7.0)
        pH_thresholds = thresholds.get("pH", {})
        optimal_min = pH_thresholds.get("optimal_min", 6.0)
        optimal_max = pH_thresholds.get("optimal_max", 7.5)
        
        if optimal_min <= pH <= optimal_max:
            pH_score = 100
        elif pH < optimal_min:
            pH_score = max(0, 100 - (optimal_min - pH) * 20)
        else:
            pH_score = max(0, 100 - (pH - optimal_max) * 15)
        
        # Nutrient scores
        nitrogen = soil_data.get("nitrogen", 0)
        phosphorus = soil_data.get("phosphorus", 0)
        potassium = soil_data.get("potassium", 0)
        
        def calculate_nutrient_score(value, thresholds, nutrient_name):
            optimal_min = thresholds.get(f"{nutrient_name}_ppm", {}).get("optimal_min", 50)
            warning_low = thresholds.get(f"{nutrient_name}_ppm", {}).get("warning_low", 30)
            
            if value >= optimal_min:
                return 100
            elif value >= warning_low:
                return 60 + (value - warning_low) / (optimal_min - warning_low) * 40
            else:
                return max(0, value / warning_low * 60)
        
        nitrogen_score = calculate_nutrient_score(nitrogen, thresholds, "nitrogen")
        phosphorus_score = calculate_nutrient_score(phosphorus, thresholds, "phosphorus")
        potassium_score = calculate_nutrient_score(potassium, thresholds, "potassium")
        
        # Salinity score
        EC = soil_data.get("electrical_conductivity", 0)
        EC_thresholds = thresholds.get("electrical_conductivity", {})
        optimal_max = EC_thresholds.get("optimal_max", 2.0)
        warning_high = EC_thresholds.get("warning_high", 3.0)
        
        if EC <= optimal_max:
            salinity_score = 100
        elif EC <= warning_high:
            salinity_score = 100 - (EC - optimal_max) / (warning_high - optimal_max) * 30
        else:
            salinity_score = max(0, 70 - (EC - warning_high) * 10)
        
        # Calculate weighted overall score
        overall_score = (
            pH_score * HEALTH_SCORE_WEIGHTS["pH"] +
            nitrogen_score * HEALTH_SCORE_WEIGHTS["nitrogen"] +
            phosphorus_score * HEALTH_SCORE_WEIGHTS["phosphorus"] +
            potassium_score * HEALTH_SCORE_WEIGHTS["potassium"] +
            salinity_score * HEALTH_SCORE_WEIGHTS["salinity"]
        )
        
        # Apply penalties for detected issues
        for issue in issues:
            if issue.urgency == UrgencyLevel.CRITICAL:
                overall_score -= 15
            elif issue.urgency == UrgencyLevel.HIGH:
                overall_score -= 10
            elif issue.urgency == UrgencyLevel.MEDIUM:
                overall_score -= 5
        
        overall_score = max(0, min(100, overall_score))
        
        return HealthScoreBreakdown(
            pH_score=pH_score,
            nutrient_score=(nitrogen_score + phosphorus_score + potassium_score) / 3,
            salinity_score=salinity_score,
            overall_score=overall_score
        )
    
    @staticmethod
    def _generate_recommendations(issues: List[SoilIssue]) -> SoilRecommendations:
        """Generate recommendations based on detected issues"""
        chemical_recs = []
        organic_recs = []
        cultural_recs = []
        
        for issue in issues:
            issue_def = get_issue_definition(issue.problem)
            
            # Add chemical recommendations
            for chem_rec in issue_def.get("chemical_recommendations", []):
                chemical_recs.append(Recommendation(
                    type="chemical",
                    name=chem_rec.get("name", ""),
                    description=chem_rec.get("description", ""),
                    application_rate=chem_rec.get("application_rate"),
                    timing=chem_rec.get("timing"),
                    cost_estimate=None
                ))
            
            # Add organic recommendations
            for org_rec in issue_def.get("organic_recommendations", []):
                organic_recs.append(Recommendation(
                    type="organic",
                    name=org_rec.get("name", ""),
                    description=org_rec.get("description", ""),
                    application_rate=org_rec.get("application_rate"),
                    timing=org_rec.get("timing"),
                    cost_estimate=None
                ))
            
            # Add cultural recommendations
            for cult_rec in issue_def.get("cultural_recommendations", []):
                cultural_recs.append(Recommendation(
                    type="cultural",
                    name=cult_rec.get("name", ""),
                    description=cult_rec.get("description", ""),
                    application_rate=cult_rec.get("application_rate"),
                    timing=cult_rec.get("timing"),
                    cost_estimate=None
                ))
        
        return SoilRecommendations(
            chemical=chemical_recs,
            organic=organic_recs,
            cultural=cultural_recs
        )


# Legacy function for backward compatibility
def run_soil_health(sensor_data: dict) -> dict:
    """Legacy function for backward compatibility with existing soil health agent"""
    try:
        # Convert legacy format to new format
        from farmxpert.app.agents.soil_health.models.input_models import QuickSoilCheckInput
        
        input_data = QuickSoilCheckInput(
            pH=sensor_data.get("pH", 7.0),
            nitrogen=sensor_data.get("N", 50),
            phosphorus=sensor_data.get("P", 20),
            potassium=sensor_data.get("K", 100),
            electrical_conductivity=sensor_data.get("EC", 1.5),
            moisture=sensor_data.get("moisture"),
            temperature=sensor_data.get("temperature")
        )
        
        # Perform quick check
        result = SoilHealthAnalysisService.quick_soil_check(input_data)
        
        # Convert back to legacy format
        issues = []
        recommendations = {"chemical": [], "organic": []}
        
        # Map results back to legacy format
        if result.health_score < 60:
            # Add some sample issues based on low score
            if input_data.pH < 6.0:
                issues.append({
                    "problem": "acidic_soil",
                    "cause": "Low pH due to acidic conditions",
                    "effect": "Reduced nutrient availability"
                })
                recommendations["chemical"].append("Lime application")
                recommendations["organic"].append("Compost application")
            
            if input_data.nitrogen < 50:
                issues.append({
                    "problem": "low_nitrogen",
                    "cause": "Insufficient nitrogen",
                    "effect": "Stunted growth"
                })
                recommendations["chemical"].append("Urea application")
                recommendations["organic"].append("Farmyard manure")
        
        return {
            "agent": "SoilHealthAgent",
            "red_alert": result.red_alert,
            "issues": issues,
            "recommendations": recommendations,
        }
        
    except Exception as e:
        logger.error(f"Legacy soil health function failed: {e}")
        return {
            "agent": "SoilHealthAgent",
            "red_alert": False,
            "issues": [],
            "recommendations": {"chemical": [], "organic": []},
        }
