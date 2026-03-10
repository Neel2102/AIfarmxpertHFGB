from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime
from farmxpert.core.base_agent.base_agent import BaseAgent


class CropInsuranceRiskAgent(BaseAgent):
    name = "crop_insurance_risk_agent"
    description = "Guides farmers on suitable insurance plans and provides claim process assistance in case of loss"

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide crop insurance and risk management recommendations"""
        crops = inputs.get("crops", [])
        farm_size = inputs.get("farm_size", 0)
        location = inputs.get("location", "unknown")
        risk_factors = inputs.get("risk_factors", [])
        current_insurance = inputs.get("current_insurance", {})
        
        # Assess risk profile
        risk_assessment = self._assess_risk_profile(crops, location, risk_factors)
        
        # Get available insurance plans
        insurance_plans = self._get_insurance_plans(crops, location)
        
        # Generate insurance recommendations
        insurance_recommendations = self._generate_insurance_recommendations(
            crops, farm_size, risk_assessment, insurance_plans, current_insurance
        )
        
        # Calculate premium estimates
        premium_estimates = self._calculate_premium_estimates(
            insurance_recommendations, farm_size
        )
        
        # Provide claim guidance
        claim_guidance = self._provide_claim_guidance()
        
        return {
            "agent": self.name,
            "crops": crops,
            "risk_assessment": risk_assessment,
            "insurance_plans": insurance_plans,
            "insurance_recommendations": insurance_recommendations,
            "premium_estimates": premium_estimates,
            "claim_guidance": claim_guidance,
            "recommendations": self._generate_recommendations(risk_assessment, insurance_recommendations)
        }
    
    def _assess_risk_profile(self, crops: List[str], location: str, risk_factors: List[str]) -> Dict[str, Any]:
        """Assess risk profile for the farm"""
        risk_profile = {
            "overall_risk_level": "medium",
            "crop_specific_risks": {},
            "location_risks": {},
            "environmental_risks": [],
            "financial_risks": []
        }
        
        # Assess crop-specific risks
        for crop in crops:
            crop_risks = self._assess_crop_risks(crop, location)
            risk_profile["crop_specific_risks"][crop] = crop_risks
        
        # Assess location risks
        risk_profile["location_risks"] = self._assess_location_risks(location)
        
        # Assess environmental risks
        risk_profile["environmental_risks"] = [
            "Drought risk",
            "Flood risk",
            "Pest infestation risk",
            "Disease outbreak risk"
        ]
        
        # Assess financial risks
        risk_profile["financial_risks"] = [
            "Price volatility risk",
            "Input cost risk",
            "Market access risk",
            "Credit availability risk"
        ]
        
        # Calculate overall risk level
        total_risk_score = 0
        for crop_risks in risk_profile["crop_specific_risks"].values():
            total_risk_score += crop_risks["risk_score"]
        
        avg_risk_score = total_risk_score / len(crops) if crops else 0
        
        if avg_risk_score > 0.7:
            risk_profile["overall_risk_level"] = "high"
        elif avg_risk_score < 0.3:
            risk_profile["overall_risk_level"] = "low"
        else:
            risk_profile["overall_risk_level"] = "medium"
        
        return risk_profile
    
    def _assess_crop_risks(self, crop: str, location: str) -> Dict[str, Any]:
        """Assess risks for a specific crop"""
        crop_risk_data = {
            "wheat": {
                "drought_sensitivity": 0.6,
                "pest_sensitivity": 0.4,
                "disease_sensitivity": 0.5,
                "price_volatility": 0.3,
                "risk_score": 0.45
            },
            "maize": {
                "drought_sensitivity": 0.7,
                "pest_sensitivity": 0.6,
                "disease_sensitivity": 0.4,
                "price_volatility": 0.4,
                "risk_score": 0.53
            },
            "rice": {
                "drought_sensitivity": 0.8,
                "pest_sensitivity": 0.5,
                "disease_sensitivity": 0.6,
                "price_volatility": 0.2,
                "risk_score": 0.53
            },
            "pulses": {
                "drought_sensitivity": 0.4,
                "pest_sensitivity": 0.7,
                "disease_sensitivity": 0.3,
                "price_volatility": 0.5,
                "risk_score": 0.48
            },
            "cotton": {
                "drought_sensitivity": 0.5,
                "pest_sensitivity": 0.8,
                "disease_sensitivity": 0.4,
                "price_volatility": 0.6,
                "risk_score": 0.58
            }
        }
        
        return crop_risk_data.get(crop.lower(), {
            "drought_sensitivity": 0.5,
            "pest_sensitivity": 0.5,
            "disease_sensitivity": 0.5,
            "price_volatility": 0.4,
            "risk_score": 0.5
        })
    
    def _assess_location_risks(self, location: str) -> Dict[str, Any]:
        """Assess location-specific risks"""
        location_risks = {
            "ahmedabad": {
                "drought_risk": "low",
                "flood_risk": "medium",
                "pest_risk": "medium",
                "overall_risk": "medium"
            },
            "haryana": {
                "drought_risk": "medium",
                "flood_risk": "low",
                "pest_risk": "medium",
                "overall_risk": "medium"
            },
            "uttar_pradesh": {
                "drought_risk": "medium",
                "flood_risk": "high",
                "pest_risk": "high",
                "overall_risk": "high"
            },
            "madhya_pradesh": {
                "drought_risk": "high",
                "flood_risk": "low",
                "pest_risk": "medium",
                "overall_risk": "high"
            },
            "maharashtra": {
                "drought_risk": "high",
                "flood_risk": "medium",
                "pest_risk": "medium",
                "overall_risk": "high"
            }
        }
        
        return location_risks.get(location.lower(), {
            "drought_risk": "medium",
            "flood_risk": "medium",
            "pest_risk": "medium",
            "overall_risk": "medium"
        })
    
    def _get_insurance_plans(self, crops: List[str], location: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get available insurance plans"""
        plans = {
            "PMFBY": {
                "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                "type": "government",
                "coverage": "Comprehensive crop insurance",
                "premium_rate": 0.015,  # 1.5% of sum insured
                "coverage_period": "Full crop season",
                "eligibility": "All farmers",
                "benefits": [
                    "Low premium rates",
                    "Government subsidy",
                    "Comprehensive coverage",
                    "Easy claim process"
                ]
            },
            "WBCIS": {
                "name": "Weather Based Crop Insurance Scheme (WBCIS)",
                "type": "government",
                "coverage": "Weather-related losses",
                "premium_rate": 0.02,  # 2% of sum insured
                "coverage_period": "Weather events",
                "eligibility": "All farmers",
                "benefits": [
                    "Weather-based payouts",
                    "Quick settlement",
                    "No crop cutting experiments"
                ]
            },
            "Private_Comprehensive": {
                "name": "Private Comprehensive Insurance",
                "type": "private",
                "coverage": "All risks including market risks",
                "premium_rate": 0.05,  # 5% of sum insured
                "coverage_period": "Full season + post-harvest",
                "eligibility": "Commercial farmers",
                "benefits": [
                    "Higher coverage limits",
                    "Market risk coverage",
                    "Flexible terms",
                    "Additional services"
                ]
            },
            "Private_Basic": {
                "name": "Private Basic Insurance",
                "type": "private",
                "coverage": "Basic crop damage",
                "premium_rate": 0.03,  # 3% of sum insured
                "coverage_period": "Growing season",
                "eligibility": "All farmers",
                "benefits": [
                    "Affordable premiums",
                    "Basic coverage",
                    "Easy application"
                ]
            }
        }
        
        return plans
    
    def _generate_insurance_recommendations(self, crops: List[str], farm_size: float, 
                                          risk_assessment: Dict, insurance_plans: Dict, 
                                          current_insurance: Dict) -> Dict[str, Any]:
        """Generate insurance recommendations"""
        recommendations = {
            "recommended_plans": [],
            "priority_plans": [],
            "optional_plans": [],
            "coverage_gaps": [],
            "risk_mitigation": []
        }
        
        # Determine recommended plans based on risk level
        risk_level = risk_assessment["overall_risk_level"]
        
        if risk_level == "high":
            recommendations["priority_plans"].append({
                "plan": "PMFBY",
                "reason": "High risk requires comprehensive coverage",
                "priority": "essential"
            })
            recommendations["recommended_plans"].append({
                "plan": "WBCIS",
                "reason": "Additional weather protection",
                "priority": "high"
            })
        elif risk_level == "medium":
            recommendations["recommended_plans"].append({
                "plan": "PMFBY",
                "reason": "Standard comprehensive coverage",
                "priority": "high"
            })
        else:  # low risk
            recommendations["optional_plans"].append({
                "plan": "PMFBY",
                "reason": "Basic protection recommended",
                "priority": "medium"
            })
        
        # Check for coverage gaps
        current_coverage = current_insurance.get("coverage", [])
        for crop in crops:
            if crop not in current_coverage:
                recommendations["coverage_gaps"].append({
                    "crop": crop,
                    "gap": "No insurance coverage",
                    "recommendation": "Add to insurance plan"
                })
        
        # Risk mitigation strategies
        recommendations["risk_mitigation"] = [
            "Diversify crop portfolio",
            "Implement irrigation systems",
            "Use pest-resistant varieties",
            "Maintain proper crop rotation",
            "Monitor weather forecasts regularly"
        ]
        
        return recommendations
    
    def _calculate_premium_estimates(self, insurance_recommendations: Dict, farm_size: float) -> Dict[str, Any]:
        """Calculate premium estimates for recommended plans"""
        premium_estimates = {
            "plan_estimates": {},
            "total_annual_premium": 0,
            "cost_benefit_analysis": {},
            "affordability": "affordable"
        }
        
        # Base sum insured per acre
        base_sum_insured = 50000  # ₹50,000 per acre
        
        # Calculate for each recommended plan
        for rec in insurance_recommendations["recommended_plans"]:
            plan_name = rec["plan"]
            
            if plan_name == "PMFBY":
                premium_rate = 0.015
                sum_insured = farm_size * base_sum_insured
                premium = sum_insured * premium_rate
                
                premium_estimates["plan_estimates"][plan_name] = {
                    "sum_insured": sum_insured,
                    "premium_rate": premium_rate,
                    "annual_premium": premium,
                    "government_subsidy": premium * 0.5,  # 50% subsidy
                    "farmer_contribution": premium * 0.5
                }
                
                premium_estimates["total_annual_premium"] += premium * 0.5  # Only farmer contribution
        
        # Cost-benefit analysis
        total_premium = premium_estimates["total_annual_premium"]
        potential_benefit = farm_size * base_sum_insured * 0.8  # 80% of sum insured as potential benefit
        
        premium_estimates["cost_benefit_analysis"] = {
            "total_premium": total_premium,
            "potential_benefit": potential_benefit,
            "benefit_cost_ratio": potential_benefit / total_premium if total_premium > 0 else 0,
            "break_even_probability": 0.15  # 15% chance of needing insurance
        }
        
        # Affordability assessment
        if total_premium > 10000:
            premium_estimates["affordability"] = "expensive"
        elif total_premium > 5000:
            premium_estimates["affordability"] = "moderate"
        else:
            premium_estimates["affordability"] = "affordable"
        
        return premium_estimates
    
    def _provide_claim_guidance(self) -> Dict[str, Any]:
        """Provide guidance for insurance claims"""
        return {
            "claim_process": {
                "step_1": "Notify insurance company within 24 hours of damage",
                "step_2": "Document damage with photos and videos",
                "step_3": "Submit claim form with required documents",
                "step_4": "Cooperate with survey and assessment",
                "step_5": "Receive claim settlement"
            },
            "required_documents": [
                "Insurance policy document",
                "Land ownership/lease documents",
                "Crop cutting experiment report",
                "Damage assessment report",
                "Bank account details",
                "Identity proof"
            ],
            "claim_timeline": {
                "notification": "Within 24 hours",
                "document_submission": "Within 7 days",
                "assessment": "Within 15 days",
                "settlement": "Within 30 days"
            },
            "common_issues": [
                "Delayed notification",
                "Incomplete documentation",
                "Disputed damage assessment",
                "Non-cooperation with survey"
            ],
            "tips_for_successful_claims": [
                "Report damage immediately",
                "Take clear photos of damage",
                "Keep all receipts and documents",
                "Maintain crop records",
                "Cooperate fully with surveyors"
            ]
        }
    
    def _generate_recommendations(self, risk_assessment: Dict, insurance_recommendations: Dict) -> List[str]:
        """Generate general recommendations"""
        recommendations = [
            "Enroll in PMFBY for basic crop protection",
            "Consider weather-based insurance for additional protection",
            "Maintain detailed crop records for claims",
            "Regularly monitor weather forecasts",
            "Implement risk mitigation strategies"
        ]
        
        # Risk-specific recommendations
        if risk_assessment["overall_risk_level"] == "high":
            recommendations.extend([
                "Consider multiple insurance plans for comprehensive coverage",
                "Implement advanced irrigation systems",
                "Use drought-resistant crop varieties",
                "Maintain emergency funds for crop losses"
            ])
        elif risk_assessment["overall_risk_level"] == "low":
            recommendations.extend([
                "Basic insurance coverage should be sufficient",
                "Focus on preventive measures",
                "Consider self-insurance for small losses"
            ])
        
        return recommendations
