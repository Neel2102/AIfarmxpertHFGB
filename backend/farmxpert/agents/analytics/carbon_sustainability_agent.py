from __future__ import annotations
from typing import Dict, Any, List
import math
from farmxpert.core.base_agent.base_agent import BaseAgent


class CarbonSustainabilityAgent(BaseAgent):
    name = "carbon_sustainability_agent"
    description = "Recommends regenerative farming practices and tracks eligibility for carbon credits and sustainability programs"

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze farm sustainability and provide carbon credit recommendations"""
        current_practices = inputs.get("current_practices", {})
        farm_size = inputs.get("farm_size", 0)
        soil_data = inputs.get("soil_data", {})
        crop_history = inputs.get("crop_history", [])
        equipment_usage = inputs.get("equipment_usage", {})
        fertilizer_usage = inputs.get("fertilizer_usage", {})
        
        # Calculate current carbon footprint
        carbon_footprint = self._calculate_carbon_footprint(
            current_practices, farm_size, equipment_usage, fertilizer_usage
        )
        
        # Assess current sustainability practices
        sustainability_assessment = self._assess_sustainability_practices(current_practices)
        
        # Generate regenerative farming recommendations
        regenerative_recommendations = self._generate_regenerative_recommendations(
            current_practices, farm_size, soil_data
        )
        
        # Calculate carbon credit potential
        carbon_credit_potential = self._calculate_carbon_credit_potential(
            regenerative_recommendations, farm_size, current_practices
        )
        
        # Identify sustainability programs
        sustainability_programs = self._identify_sustainability_programs(
            current_practices, farm_size, carbon_footprint
        )
        
        return {
            "agent": self.name,
            "carbon_footprint": carbon_footprint,
            "sustainability_assessment": sustainability_assessment,
            "regenerative_recommendations": regenerative_recommendations,
            "carbon_credit_potential": carbon_credit_potential,
            "sustainability_programs": sustainability_programs,
            "implementation_roadmap": self._create_implementation_roadmap(regenerative_recommendations),
            "financial_benefits": self._calculate_financial_benefits(carbon_credit_potential, sustainability_programs)
        }
    
    def _calculate_carbon_footprint(self, practices: Dict, farm_size: float, 
                                  equipment: Dict, fertilizer: Dict) -> Dict[str, Any]:
        """Calculate current carbon footprint of the farm"""
        footprint = {
            "total_emissions_co2e": 0,
            "emissions_by_source": {},
            "emissions_per_acre": 0,
            "carbon_intensity": 0
        }
        
        # Equipment emissions
        equipment_emissions = 0
        for equipment_type, usage in equipment.items():
            if equipment_type == "tractor":
                emissions_per_hour = 15  # kg CO2e per hour
                equipment_emissions += usage.get("hours_per_year", 0) * emissions_per_hour
            elif equipment_type == "harvester":
                emissions_per_hour = 20
                equipment_emissions += usage.get("hours_per_year", 0) * emissions_per_hour
            elif equipment_type == "irrigation_pump":
                emissions_per_hour = 8
                equipment_emissions += usage.get("hours_per_year", 0) * emissions_per_hour
        
        footprint["emissions_by_source"]["equipment"] = equipment_emissions
        
        # Fertilizer emissions
        fertilizer_emissions = 0
        for fertilizer_type, usage in fertilizer.items():
            if fertilizer_type == "nitrogen":
                # N2O emissions from nitrogen fertilizer
                n2o_factor = 298  # N2O is 298 times more potent than CO2
                fertilizer_emissions += usage.get("kg_per_acre", 0) * farm_size * 0.01 * n2o_factor
            elif fertilizer_type == "phosphorus":
                # CO2 emissions from phosphorus fertilizer production
                fertilizer_emissions += usage.get("kg_per_acre", 0) * farm_size * 0.5
            elif fertilizer_type == "potassium":
                fertilizer_emissions += usage.get("kg_per_acre", 0) * farm_size * 0.3
        
        footprint["emissions_by_source"]["fertilizer"] = fertilizer_emissions
        
        # Tillage emissions
        tillage_practices = practices.get("tillage", "conventional")
        if tillage_practices == "conventional":
            tillage_emissions = farm_size * 0.3  # tons CO2e per acre
        elif tillage_practices == "reduced":
            tillage_emissions = farm_size * 0.15
        else:  # no-till
            tillage_emissions = farm_size * 0.05
        
        footprint["emissions_by_source"]["tillage"] = tillage_emissions
        
        # Crop residue management
        residue_management = practices.get("residue_management", "burning")
        if residue_management == "burning":
            residue_emissions = farm_size * 0.2
        elif residue_management == "incorporation":
            residue_emissions = farm_size * 0.05
        else:  # mulching
            residue_emissions = farm_size * 0.02
        
        footprint["emissions_by_source"]["residue_management"] = residue_emissions
        
        # Calculate total emissions
        total_emissions = sum(footprint["emissions_by_source"].values())
        footprint["total_emissions_co2e"] = total_emissions
        footprint["emissions_per_acre"] = total_emissions / farm_size if farm_size > 0 else 0
        
        # Calculate carbon intensity (emissions per unit of production)
        expected_yield = farm_size * 2.5  # tons per acre average
        footprint["carbon_intensity"] = total_emissions / expected_yield if expected_yield > 0 else 0
        
        return footprint
    
    def _assess_sustainability_practices(self, practices: Dict) -> Dict[str, Any]:
        """Assess current sustainability practices"""
        assessment = {
            "overall_score": 0,
            "practice_scores": {},
            "strengths": [],
            "improvement_areas": [],
            "certification_readiness": {}
        }
        
        # Define practice weights and scoring
        practice_weights = {
            "tillage": 0.20,
            "crop_rotation": 0.15,
            "cover_crops": 0.15,
            "irrigation_efficiency": 0.15,
            "pest_management": 0.10,
            "nutrient_management": 0.15,
            "residue_management": 0.10
        }
        
        total_score = 0
        
        # Assess each practice
        for practice, weight in practice_weights.items():
            practice_value = practices.get(practice, "conventional")
            score = self._score_practice(practice, practice_value)
            assessment["practice_scores"][practice] = {
                "current_practice": practice_value,
                "score": score,
                "weight": weight,
                "weighted_score": score * weight
            }
            total_score += score * weight
        
        assessment["overall_score"] = total_score
        
        # Identify strengths and improvement areas
        for practice, practice_data in assessment["practice_scores"].items():
            if practice_data["score"] >= 0.8:
                assessment["strengths"].append(f"Strong {practice.replace('_', ' ')} practices")
            elif practice_data["score"] <= 0.4:
                assessment["improvement_areas"].append(f"Improve {practice.replace('_', ' ')} practices")
        
        # Assess certification readiness
        assessment["certification_readiness"] = {
            "organic": self._assess_organic_readiness(practices),
            "regenerative": self._assess_regenerative_readiness(practices),
            "carbon_farming": self._assess_carbon_farming_readiness(practices)
        }
        
        return assessment
    
    def _score_practice(self, practice: str, value: str) -> float:
        """Score individual practices"""
        scoring = {
            "tillage": {
                "conventional": 0.2,
                "reduced": 0.6,
                "no_till": 1.0
            },
            "crop_rotation": {
                "monoculture": 0.1,
                "simple_rotation": 0.5,
                "complex_rotation": 1.0
            },
            "cover_crops": {
                "none": 0.0,
                "occasional": 0.4,
                "regular": 0.8,
                "year_round": 1.0
            },
            "irrigation_efficiency": {
                "flood": 0.2,
                "sprinkler": 0.6,
                "drip": 1.0
            },
            "pest_management": {
                "conventional": 0.2,
                "integrated": 0.7,
                "organic": 1.0
            },
            "nutrient_management": {
                "synthetic_only": 0.2,
                "mixed": 0.6,
                "organic": 1.0
            },
            "residue_management": {
                "burning": 0.0,
                "removal": 0.3,
                "incorporation": 0.7,
                "mulching": 1.0
            }
        }
        
        return scoring.get(practice, {}).get(value, 0.5)
    
    def _generate_regenerative_recommendations(self, current_practices: Dict, 
                                             farm_size: float, soil_data: Dict) -> List[Dict[str, Any]]:
        """Generate regenerative farming recommendations"""
        recommendations = []
        
        # No-till farming
        if current_practices.get("tillage") != "no_till":
            recommendations.append({
                "practice": "No-till farming",
                "description": "Eliminate tillage to reduce soil erosion and increase carbon sequestration",
                "carbon_sequestration_potential": farm_size * 0.3,  # tons CO2e per acre per year
                "implementation_cost": farm_size * 50,  # $50 per acre
                "implementation_time": "1-2 years",
                "difficulty": "medium",
                "priority": "high"
            })
        
        # Cover crops
        if current_practices.get("cover_crops") in ["none", "occasional"]:
            recommendations.append({
                "practice": "Cover cropping",
                "description": "Plant cover crops to improve soil health and reduce erosion",
                "carbon_sequestration_potential": farm_size * 0.2,
                "implementation_cost": farm_size * 30,
                "implementation_time": "immediate",
                "difficulty": "low",
                "priority": "high"
            })
        
        # Crop rotation
        if current_practices.get("crop_rotation") == "monoculture":
            recommendations.append({
                "practice": "Diverse crop rotation",
                "description": "Implement diverse crop rotations to improve soil health and reduce pest pressure",
                "carbon_sequestration_potential": farm_size * 0.15,
                "implementation_cost": farm_size * 20,
                "implementation_time": "2-3 years",
                "difficulty": "medium",
                "priority": "medium"
            })
        
        # Organic amendments
        recommendations.append({
            "practice": "Organic soil amendments",
            "description": "Apply compost, manure, or other organic amendments to improve soil health",
            "carbon_sequestration_potential": farm_size * 0.25,
            "implementation_cost": farm_size * 100,
            "implementation_time": "immediate",
            "difficulty": "low",
            "priority": "medium"
        })
        
        # Agroforestry
        if farm_size > 50:  # Only for larger farms
            recommendations.append({
                "practice": "Agroforestry",
                "description": "Integrate trees and shrubs into farming systems for additional carbon sequestration",
                "carbon_sequestration_potential": farm_size * 0.4,
                "implementation_cost": farm_size * 200,
                "implementation_time": "3-5 years",
                "difficulty": "high",
                "priority": "low"
            })
        
        # Precision agriculture
        recommendations.append({
            "practice": "Precision agriculture",
            "description": "Use technology to optimize inputs and reduce waste",
            "carbon_sequestration_potential": farm_size * 0.1,
            "implementation_cost": farm_size * 150,
            "implementation_time": "1 year",
            "difficulty": "medium",
            "priority": "medium"
        })
        
        return recommendations
    
    def _calculate_carbon_credit_potential(self, recommendations: List[Dict], 
                                         farm_size: float, current_practices: Dict) -> Dict[str, Any]:
        """Calculate potential carbon credits from implementing recommendations"""
        carbon_potential = {
            "total_sequestration_potential": 0,
            "annual_credits_potential": 0,
            "credits_by_practice": {},
            "market_value": 0,
            "payback_period": 0,
            "implementation_priority": []
        }
        
        total_sequestration = 0
        total_implementation_cost = 0
        
        for rec in recommendations:
            sequestration = rec["carbon_sequestration_potential"]
            cost = rec["implementation_cost"]
            
            carbon_potential["credits_by_practice"][rec["practice"]] = {
                "annual_sequestration": sequestration,
                "implementation_cost": cost,
                "credits_per_year": sequestration,  # 1 ton CO2e = 1 carbon credit
                "market_value": sequestration * 20,  # $20 per credit (current market rate)
                "payback_period_years": cost / (sequestration * 20) if sequestration > 0 else float('inf')
            }
            
            total_sequestration += sequestration
            total_implementation_cost += cost
        
        carbon_potential["total_sequestration_potential"] = total_sequestration
        carbon_potential["annual_credits_potential"] = total_sequestration
        carbon_potential["market_value"] = total_sequestration * 20
        carbon_potential["payback_period"] = total_implementation_cost / carbon_potential["market_value"] if carbon_potential["market_value"] > 0 else float('inf')
        
        # Sort by payback period for implementation priority
        sorted_practices = sorted(
            carbon_potential["credits_by_practice"].items(),
            key=lambda x: x[1]["payback_period_years"]
        )
        carbon_potential["implementation_priority"] = [practice for practice, _ in sorted_practices]
        
        return carbon_potential
    
    def _identify_sustainability_programs(self, current_practices: Dict, 
                                        farm_size: float, carbon_footprint: Dict) -> List[Dict[str, Any]]:
        """Identify applicable sustainability programs and certifications"""
        programs = []
        
        # Carbon farming programs
        if carbon_footprint["emissions_per_acre"] < 0.5:  # Low emissions threshold
            programs.append({
                "program": "Carbon Farming Initiative",
                "type": "carbon_credits",
                "eligibility": "eligible",
                "requirements": ["Implement carbon sequestration practices", "Maintain records for 5 years"],
                "benefits": ["Carbon credit payments", "Technical assistance", "Market access"],
                "application_deadline": "Rolling",
                "estimated_annual_benefit": farm_size * 25
            })
        
        # Organic certification
        if self._assess_organic_readiness(current_practices)["score"] > 0.7:
            programs.append({
                "program": "USDA Organic Certification",
                "type": "certification",
                "eligibility": "eligible",
                "requirements": ["3-year transition period", "No synthetic inputs", "Organic management plan"],
                "benefits": ["Premium prices", "Market access", "Consumer trust"],
                "application_deadline": "Year-round",
                "estimated_annual_benefit": farm_size * 200
            })
        
        # Regenerative agriculture programs
        if self._assess_regenerative_readiness(current_practices)["score"] > 0.6:
            programs.append({
                "program": "Regenerative Agriculture Certification",
                "type": "certification",
                "eligibility": "eligible",
                "requirements": ["Soil health practices", "Biodiversity enhancement", "Community engagement"],
                "benefits": ["Market differentiation", "Consumer demand", "Environmental impact"],
                "application_deadline": "Quarterly",
                "estimated_annual_benefit": farm_size * 150
            })
        
        # Conservation programs
        programs.append({
            "program": "Conservation Stewardship Program",
            "type": "conservation",
            "eligibility": "likely_eligible",
            "requirements": ["Implement conservation practices", "Maintain existing practices"],
            "benefits": ["Annual payments", "Technical assistance", "Equipment cost-share"],
            "application_deadline": "Annual",
            "estimated_annual_benefit": farm_size * 15
        })
        
        # State-specific programs
        programs.append({
            "program": "State Agricultural Enhancement Program",
            "type": "state_support",
            "eligibility": "check_local",
            "requirements": ["Varies by state", "Contact local extension office"],
            "benefits": ["Cost-share assistance", "Technical support", "Market development"],
            "application_deadline": "Varies",
            "estimated_annual_benefit": farm_size * 50
        })
        
        return programs
    
    def _assess_organic_readiness(self, practices: Dict) -> Dict[str, Any]:
        """Assess readiness for organic certification"""
        score = 0
        requirements = []
        
        # Check current practices
        if practices.get("pest_management") == "organic":
            score += 0.3
        else:
            requirements.append("Transition to organic pest management")
        
        if practices.get("nutrient_management") == "organic":
            score += 0.3
        else:
            requirements.append("Transition to organic nutrient management")
        
        if practices.get("crop_rotation") != "monoculture":
            score += 0.2
        else:
            requirements.append("Implement crop rotation")
        
        if practices.get("residue_management") != "burning":
            score += 0.2
        else:
            requirements.append("Stop burning crop residues")
        
        return {
            "score": score,
            "requirements": requirements,
            "transition_period": "3 years",
            "estimated_cost": 5000
        }
    
    def _assess_regenerative_readiness(self, practices: Dict) -> Dict[str, Any]:
        """Assess readiness for regenerative agriculture certification"""
        score = 0
        requirements = []
        
        # Check regenerative practices
        if practices.get("tillage") == "no_till":
            score += 0.25
        else:
            requirements.append("Implement no-till farming")
        
        if practices.get("cover_crops") in ["regular", "year_round"]:
            score += 0.25
        else:
            requirements.append("Implement cover cropping")
        
        if practices.get("crop_rotation") == "complex_rotation":
            score += 0.25
        else:
            requirements.append("Implement diverse crop rotation")
        
        if practices.get("irrigation_efficiency") == "drip":
            score += 0.25
        else:
            requirements.append("Improve irrigation efficiency")
        
        return {
            "score": score,
            "requirements": requirements,
            "transition_period": "2-3 years",
            "estimated_cost": 3000
        }
    
    def _assess_carbon_farming_readiness(self, practices: Dict) -> Dict[str, Any]:
        """Assess readiness for carbon farming programs"""
        score = 0
        requirements = []
        
        # Check carbon-friendly practices
        if practices.get("tillage") in ["reduced", "no_till"]:
            score += 0.4
        else:
            requirements.append("Reduce or eliminate tillage")
        
        if practices.get("cover_crops") != "none":
            score += 0.3
        else:
            requirements.append("Implement cover crops")
        
        if practices.get("residue_management") in ["incorporation", "mulching"]:
            score += 0.3
        else:
            requirements.append("Improve residue management")
            
        return {
            "score": score,
            "requirements": requirements,
            "transition_period": "1-2 years",
            "estimated_cost": 2000
        }
    
    def _create_implementation_roadmap(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Create implementation roadmap for regenerative practices"""
        roadmap = {
            "phase_1": {"duration": "6 months", "practices": [], "cost": 0},
            "phase_2": {"duration": "1 year", "practices": [], "cost": 0},
            "phase_3": {"duration": "2 years", "practices": [], "cost": 0}
        }
        
        # Sort recommendations by priority and difficulty
        sorted_recs = sorted(recommendations, key=lambda x: (x["priority"] == "high", x["difficulty"] == "low"))
        
        for rec in sorted_recs:
            if rec["difficulty"] == "low" and rec["priority"] == "high":
                roadmap["phase_1"]["practices"].append(rec["practice"])
                roadmap["phase_1"]["cost"] += rec["implementation_cost"]
            elif rec["difficulty"] == "medium" or rec["priority"] == "medium":
                roadmap["phase_2"]["practices"].append(rec["practice"])
                roadmap["phase_2"]["cost"] += rec["implementation_cost"]
            else:
                roadmap["phase_3"]["practices"].append(rec["practice"])
                roadmap["phase_3"]["cost"] += rec["implementation_cost"]
        
        return roadmap
    
    def _calculate_financial_benefits(self, carbon_potential: Dict, programs: List[Dict]) -> Dict[str, Any]:
        """Calculate financial benefits of sustainability practices"""
        benefits = {
            "carbon_credit_revenue": carbon_potential["market_value"],
            "program_payments": sum(program["estimated_annual_benefit"] for program in programs),
            "premium_prices": 0,
            "cost_savings": 0,
            "total_annual_benefits": 0,
            "roi_analysis": {}
        }
        
        # Calculate premium prices for organic/regenerative products
        organic_programs = [p for p in programs if "organic" in p["program"].lower()]
        if organic_programs:
            benefits["premium_prices"] = 500  # Estimated premium per acre
        
        # Calculate cost savings from reduced inputs
        benefits["cost_savings"] = 200  # Estimated savings per acre
        
        # Total benefits
        benefits["total_annual_benefits"] = (
            benefits["carbon_credit_revenue"] +
            benefits["program_payments"] +
            benefits["premium_prices"] +
            benefits["cost_savings"]
        )
        
        # ROI analysis
        total_implementation_cost = sum(phase["cost"] for phase in self._create_implementation_roadmap([]).values())
        if total_implementation_cost > 0:
            benefits["roi_analysis"] = {
                "total_implementation_cost": total_implementation_cost,
                "annual_benefits": benefits["total_annual_benefits"],
                "payback_period_years": total_implementation_cost / benefits["total_annual_benefits"],
                "roi_percentage": (benefits["total_annual_benefits"] / total_implementation_cost * 100) if total_implementation_cost > 0 else 0
            }
        
        return benefits
