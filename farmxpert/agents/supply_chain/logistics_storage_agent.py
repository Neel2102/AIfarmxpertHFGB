from __future__ import annotations
from typing import Dict, Any, List
from farmxpert.core.base_agent.base_agent import BaseAgent


class LogisticsStorageAgent(BaseAgent):
    name = "logistics_storage_agent"
    description = "Helps plan post-harvest activities: when to store, sell, or transport based on price windows and spoilage risks"

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide logistics and storage recommendations with LLM reasoning."""
        crops = inputs.get("crops", [])
        harvest_quantity = inputs.get("harvest_quantity", {})
        storage_capacity = inputs.get("storage_capacity", 0)
        
        # Tools: Generate storage recommendations & Plan logistics
        storage_recommendations = self._generate_storage_recommendations(crops, harvest_quantity, storage_capacity)
        logistics_plan = self._plan_logistics(crops, harvest_quantity)
        
        # INJECT TOOL DATA INTO LLM CONTEXT
        # This allows the expert persona to discuss specific costs/routes
        inputs["additional_data"] = inputs.get("additional_data", {})
        inputs["additional_data"]["logistics_plan"] = logistics_plan
        inputs["additional_data"]["storage_recommendations"] = storage_recommendations

        return await self._handle_with_llm(inputs)
    
    def _generate_storage_recommendations(self, crops: List[str], harvest_quantity: Dict, storage_capacity: float) -> Dict[str, Any]:
        """Generate storage recommendations for crops"""
        recommendations = {
            "immediate_sale": [],
            "short_term_storage": [],
            "long_term_storage": [],
            "storage_requirements": {}
        }
        
        for crop in crops:
            quantity = harvest_quantity.get(crop, 0)
            
            # Determine storage strategy based on crop characteristics
            if crop in ["sugarcane", "vegetables"]:
                recommendations["immediate_sale"].append({
                    "crop": crop,
                    "quantity": quantity,
                    "reason": "Perishable crop - sell immediately"
                })
            elif crop in ["wheat", "maize", "rice"]:
                if storage_capacity >= quantity * 0.5:
                    recommendations["long_term_storage"].append({
                        "crop": crop,
                        "quantity": quantity * 0.5,
                        "reason": "Stable crop - can be stored for better prices"
                    })
                    recommendations["immediate_sale"].append({
                        "crop": crop,
                        "quantity": quantity * 0.5,
                        "reason": "Sell portion for immediate cash flow"
                    })
                else:
                    recommendations["immediate_sale"].append({
                        "crop": crop,
                        "quantity": quantity,
                        "reason": "Insufficient storage capacity"
                    })
            else:
                recommendations["short_term_storage"].append({
                    "crop": crop,
                    "quantity": quantity,
                    "reason": "Moderate storage life"
                })
        
        return recommendations
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            from farmxpert.tools.supply_chain.logistics_manager import LogisticsManagerTool
            self.logistics_tool = LogisticsManagerTool()
        except ImportError:
            self.logistics_tool = None
            # self.logger.warning("Could not import LogisticsManagerTool")

    def _plan_logistics(self, crops: List[str], harvest_quantity: Dict) -> Dict[str, Any]:
        """Plan logistics for crop transportation using real tool if available"""
        logistics = {
            "transport_requirements": {},
            "timeline": {},
            "cost_estimates": {}
        }
        
        # Default farm location (Gujarat) if not in context, for simulation
        farm_loc = (21.5, 71.0) 
        
        for crop in crops:
            quantity = harvest_quantity.get(crop, 0)
            
            # Use tool to find storage/market
            route_info = {}
            if self.logistics_tool:
                try:
                    # Find nearest storage
                    storages = self.logistics_tool.find_nearest_storage(farm_loc)
                    if storages:
                        nearest = storages[0]
                        # Calculate route to it
                        route = self.logistics_tool.calculate_route(farm_loc, (nearest["lat"], nearest["lon"]))
                        if route["success"]:
                            route_info = {
                                "destination": nearest["name"],
                                "distance_km": route["distance_km"],
                                "est_time_hours": route["duration_hours"],
                                "est_cost_per_trip": route["estimated_cost_inr"]
                            }
                except Exception as e:
                    pass

            trips = max(1, int(quantity / 5))
            
            reqs = {
                "quantity_tons": quantity,
                "vehicle_type": "truck" if quantity < 10 else "truck_combination",
                "trips_needed": trips
            }
            if route_info:
                reqs.update(route_info)

            logistics["transport_requirements"][crop] = reqs
            
            # Calculate total cost
            base_cost = quantity * 120 # Fallback
            if route_info:
                base_cost = trips * route_info["est_cost_per_trip"] + (quantity * 20) # Trip cost + loading

            logistics["cost_estimates"][crop] = {
                "transport_cost": base_cost,
                "loading_cost": quantity * 20,
                "total_cost": base_cost + (quantity * 20)
            }
        
        return logistics
    
    def _generate_recommendations(self, crops: List[str], storage_capacity: float) -> List[str]:
        """Generate logistics recommendations"""
        return [
            "Prioritize immediate sale of perishable crops",
            "Store stable crops for better market prices",
            "Plan transportation during off-peak hours",
            "Ensure proper packaging for long-distance transport",
            "Consider cold storage for temperature-sensitive crops"
        ]
