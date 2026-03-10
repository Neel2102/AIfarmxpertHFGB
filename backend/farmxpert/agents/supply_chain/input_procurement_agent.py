from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime
from farmxpert.core.base_agent.base_agent import BaseAgent


class InputProcurementAgent(BaseAgent):
    name = "input_procurement_agent"
    description = "Advises where and when to buy inputs like seeds, fertilizers, and agrochemicals — includes price comparison"

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide input procurement recommendations"""
        required_inputs = inputs.get("required_inputs", [])
        farm_size = inputs.get("farm_size", 0)
        budget = inputs.get("budget", 0)
        location = inputs.get("location", "unknown")
        season = inputs.get("season", "unknown")
        
        # Get supplier information
        suppliers = self._get_supplier_information(location)
        
        # Generate procurement recommendations
        procurement_recommendations = self._generate_procurement_recommendations(
            required_inputs, farm_size, budget, suppliers, season
        )
        
        # Create procurement timeline
        procurement_timeline = self._create_procurement_timeline(required_inputs, season)
        
        # Calculate cost analysis
        cost_analysis = self._analyze_costs(procurement_recommendations, budget)
        
        return {
            "agent": self.name,
            "required_inputs": required_inputs,
            "suppliers": suppliers,
            "procurement_recommendations": procurement_recommendations,
            "procurement_timeline": procurement_timeline,
            "cost_analysis": cost_analysis,
            "recommendations": self._generate_recommendations(procurement_recommendations, budget)
        }
    
    def _get_supplier_information(self, location: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get supplier information for the location"""
        suppliers = {
            "seeds": [
                {
                    "name": "Krishna Seeds",
                    "location": "Local",
                    "rating": 4.5,
                    "delivery_time": "1-2 days",
                    "payment_terms": "Cash on delivery",
                    "quality_rating": "High"
                },
                {
                    "name": "National Seeds Corporation",
                    "location": "Regional",
                    "rating": 4.2,
                    "delivery_time": "3-5 days",
                    "payment_terms": "Advance payment",
                    "quality_rating": "Very High"
                },
                {
                    "name": "Local Cooperative",
                    "location": "Local",
                    "rating": 4.0,
                    "delivery_time": "Same day",
                    "payment_terms": "Credit available",
                    "quality_rating": "Medium"
                }
            ],
            "fertilizers": [
                {
                    "name": "IFFCO",
                    "location": "Regional",
                    "rating": 4.3,
                    "delivery_time": "2-3 days",
                    "payment_terms": "Credit available",
                    "quality_rating": "High"
                },
                {
                    "name": "KRIBHCO",
                    "location": "Regional",
                    "rating": 4.1,
                    "delivery_time": "3-4 days",
                    "payment_terms": "Advance payment",
                    "quality_rating": "High"
                },
                {
                    "name": "Local Dealer",
                    "location": "Local",
                    "rating": 3.8,
                    "delivery_time": "Same day",
                    "payment_terms": "Flexible",
                    "quality_rating": "Medium"
                }
            ],
            "pesticides": [
                {
                    "name": "Bayer CropScience",
                    "location": "Regional",
                    "rating": 4.4,
                    "delivery_time": "2-3 days",
                    "payment_terms": "Advance payment",
                    "quality_rating": "Very High"
                },
                {
                    "name": "Syngenta",
                    "location": "Regional",
                    "rating": 4.2,
                    "delivery_time": "2-3 days",
                    "payment_terms": "Advance payment",
                    "quality_rating": "Very High"
                },
                {
                    "name": "Local Agro Dealer",
                    "location": "Local",
                    "rating": 3.9,
                    "delivery_time": "Same day",
                    "payment_terms": "Cash on delivery",
                    "quality_rating": "Medium"
                }
            ]
        }
        
        return suppliers
    
    def _generate_procurement_recommendations(self, required_inputs: List[str], farm_size: float, 
                                           budget: float, suppliers: Dict, season: str) -> Dict[str, Any]:
        """Generate procurement recommendations"""
        recommendations = {
            "recommended_suppliers": {},
            "quantity_recommendations": {},
            "timing_recommendations": {},
            "cost_estimates": {}
        }
        
        for input_type in required_inputs:
            if input_type in suppliers:
                # Select best supplier based on rating and delivery time
                best_supplier = max(suppliers[input_type], key=lambda x: x["rating"])
                
                # Calculate required quantity based on farm size
                quantity = self._calculate_required_quantity(input_type, farm_size)
                
                # Estimate cost
                cost_per_unit = self._get_cost_per_unit(input_type, best_supplier["name"])
                total_cost = quantity * cost_per_unit
                
                recommendations["recommended_suppliers"][input_type] = best_supplier
                recommendations["quantity_recommendations"][input_type] = {
                    "quantity": quantity,
                    "unit": self._get_unit(input_type)
                }
                recommendations["cost_estimates"][input_type] = {
                    "cost_per_unit": cost_per_unit,
                    "total_cost": total_cost,
                    "budget_percentage": (total_cost / budget * 100) if budget > 0 else 0
                }
                
                # Timing recommendations
                recommendations["timing_recommendations"][input_type] = self._get_timing_recommendation(
                    input_type, season, best_supplier["delivery_time"]
                )
        
        return recommendations
    
    def _create_procurement_timeline(self, required_inputs: List[str], season: str) -> Dict[str, Any]:
        """Create procurement timeline"""
        timeline = {
            "immediate": [],
            "within_week": [],
            "within_month": [],
            "seasonal": []
        }
        
        for input_type in required_inputs:
            if input_type == "seeds":
                timeline["immediate"].append({
                    "input": input_type,
                    "reason": "Critical for planting season",
                    "priority": "high"
                })
            elif input_type == "fertilizers":
                timeline["within_week"].append({
                    "input": input_type,
                    "reason": "Needed for crop growth",
                    "priority": "medium"
                })
            elif input_type == "pesticides":
                timeline["within_month"].append({
                    "input": input_type,
                    "reason": "Preventive application",
                    "priority": "low"
                })
        
        return timeline
    
    def _analyze_costs(self, recommendations: Dict, budget: float) -> Dict[str, Any]:
        """Analyze procurement costs"""
        total_cost = sum(
            rec["total_cost"] for rec in recommendations["cost_estimates"].values()
        )
            
        return {
            "total_procurement_cost": total_cost,
            "budget_available": budget,
            "budget_deficit": max(0, total_cost - budget),
            "budget_surplus": max(0, budget - total_cost),
            "cost_breakdown": recommendations["cost_estimates"],
            "affordability": "affordable" if total_cost <= budget else "over_budget"
        }
    
    def _calculate_required_quantity(self, input_type: str, farm_size: float) -> float:
        """Calculate required quantity based on farm size"""
        rates = {
            "seeds": 20,  # kg per acre
            "fertilizers": 100,  # kg per acre
            "pesticides": 5  # liters per acre
        }
        
        rate = rates.get(input_type, 10)
        return farm_size * rate
    
    def _get_cost_per_unit(self, input_type: str, supplier: str) -> float:
        """Get cost per unit for input"""
        base_costs = {
            "seeds": 200,  # per kg
            "fertilizers": 30,  # per kg
            "pesticides": 500  # per liter
        }
        
        # Adjust based on supplier quality
        supplier_adjustments = {
            "Krishna Seeds": 1.0,
            "National Seeds Corporation": 1.2,
            "Local Cooperative": 0.8,
            "IFFCO": 1.0,
            "KRIBHCO": 1.1,
            "Local Dealer": 0.9,
            "Bayer CropScience": 1.3,
            "Syngenta": 1.2,
            "Local Agro Dealer": 0.9
        }
        
        base_cost = base_costs.get(input_type, 100)
        adjustment = supplier_adjustments.get(supplier, 1.0)
        
        return base_cost * adjustment
    
    def _get_unit(self, input_type: str) -> str:
        """Get unit for input type"""
        units = {
            "seeds": "kg",
            "fertilizers": "kg",
            "pesticides": "liters"
        }
        return units.get(input_type, "units")
    
    def _get_timing_recommendation(self, input_type: str, season: str, delivery_time: str) -> Dict[str, Any]:
        """Get timing recommendation for procurement"""
        if input_type == "seeds":
            return {
                "procurement_time": "2 weeks before planting",
                "reason": "Ensure availability and quality testing",
                "urgency": "high"
            }
        elif input_type == "fertilizers":
            return {
                "procurement_time": "1 week before application",
                "reason": "Avoid storage issues",
                "urgency": "medium"
            }
        elif input_type == "pesticides":
            return {
                "procurement_time": "As needed basis",
                "reason": "Prevent degradation",
                "urgency": "low"
            }
        else:
            return {
                "procurement_time": "1 week before use",
                "reason": "Standard practice",
                "urgency": "medium"
            }
    
    def _generate_recommendations(self, procurement_recommendations: Dict, budget: float) -> List[str]:
        """Generate procurement recommendations"""
        recommendations = [
            "Compare prices across multiple suppliers before purchasing",
            "Check for government subsidies and schemes",
            "Consider bulk purchasing for better rates",
            "Verify product quality and expiry dates",
            "Plan procurement based on seasonal availability"
        ]
        
        # Budget-specific recommendations
        cost_analysis = procurement_recommendations.get("cost_analysis", {})
        if cost_analysis.get("affordability") == "over_budget":
            recommendations.extend([
                "Consider purchasing inputs in phases",
                "Look for credit options from suppliers",
                "Prioritize essential inputs first"
            ])
        
        return recommendations
