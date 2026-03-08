from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime, timedelta
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import MaintenanceTrackerTool, PredictiveMaintenanceTool
from farmxpert.services.gemini_service import gemini_service


class MachineryEquipmentAgent(EnhancedBaseAgent):
    name = "machinery_equipment_agent"
    description = "Advises on the use and scheduling of farm tools (tractors, sprayers), including maintenance tips"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            from farmxpert.tools.operations.machinery_tracker import MachineryTrackerTool
            self.maintenance_tool = MachineryTrackerTool()
        except ImportError:
            self.maintenance_tool = None
            self.logger.warning("Could not import MachineryTrackerTool")

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Provide machinery recommendations using dynamic tools and predictive maintenance"""
        try:
            tools = inputs.get("tools", {})
            context = inputs.get("context", {})
            query = inputs.get("query", "")

            farm_size = context.get("farm_size", inputs.get("farm_size", 0))
            available_equipment = context.get("available_equipment", inputs.get("available_equipment", []))
            current_tasks = context.get("current_tasks", inputs.get("current_tasks", []))
            budget = context.get("budget", inputs.get("budget", 0))
            usage_stats = context.get("usage_stats", {})
            telemetry = context.get("telemetry", {})
            equipment_meta = context.get("equipment_meta", [])

            # Traditional analysis
            recommendations = self._analyze_equipment_needs(farm_size, available_equipment, current_tasks)
            maintenance_schedule = self._generate_maintenance_schedule(available_equipment)
            usage_optimization = self._optimize_equipment_usage(available_equipment, current_tasks)
            budget_recommendations = self._analyze_budget_needs(recommendations, budget)

            # Tool-driven enhancements
            maintenance_plan = {}
            service_tracking = {}
            failure_predictions = {}
            uptime_optimization = {}

            # --- REAL TOOL INTEGRATION ---
            if self.maintenance_tool:
                try:
                    # In a real scenario, we'd get farm_id from context
                    farm_id = context.get("farm_id") or 1 
                    real_alerts = self.maintenance_tool.get_maintenance_alerts(farm_id)
                    if real_alerts:
                        maintenance_plan["real_time_alerts"] = real_alerts
                        self.logger.info("Integrated MachineryTracker alerts")
                except Exception as e:
                    self.logger.warning(f"Failed to fetch maintenance alerts: {e}")
            # -----------------------------

            if "maintenance_tracker" in tools:
                try:
                    gemini_plan = await tools["maintenance_tracker"].build_maintenance_plan(
                        [{"name": e} for e in available_equipment], usage_stats
                    )
                    maintenance_plan.update(gemini_plan)
                except Exception as e:
                    self.logger.warning(f"Failed to build maintenance plan: {e}")

            if "predictive_maintenance" in tools:
                try:
                    failure_predictions = await tools["predictive_maintenance"].predict_failures(
                        telemetry, equipment_meta
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to predict failures: {e}")

            if "predictive_maintenance" in tools and maintenance_plan:
                try:
                    uptime_optimization = await tools["predictive_maintenance"].optimize_uptime(
                        maintenance_plan, context.get("spare_inventory", {})
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to optimize uptime: {e}")

            prompt = f"""
You are a machinery and equipment advisor for farms. Based on the following data, provide equipment recommendations, maintenance plan highlights, and risk mitigation steps.

Query: "{query}"
Farm Size: {farm_size} acres
Equipment: {available_equipment}
Tasks: {current_tasks}
Budget: {budget}
Maintenance Plan: {json.dumps(maintenance_plan.get('maintenance_schedule', {}), indent=2)}
Predicted Failures: {json.dumps(failure_predictions.get('high_risk_components', {}), indent=2)}
Uptime Optimization: {json.dumps(uptime_optimization.get('optimized_plan', {}), indent=2)}

Provide: equipment_plan, maintenance_highlights, risk_mitigation, spare_parts_recs, cost_summary, next_actions
"""
            response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "machinery_advice"})

            return {
                "agent": self.name,
                "success": True,
                "response": response,
                "data": {
                    "recommendations": recommendations,
                    "maintenance_schedule": maintenance_schedule,
                    "usage_optimization": usage_optimization,
                    "budget_analysis": budget_recommendations,
                    "maintenance_plan": maintenance_plan,
                    "failure_predictions": failure_predictions,
                    "uptime_optimization": uptime_optimization
                },
                "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
            }
        except Exception as e:
            self.logger.error(f"Error in machinery equipment agent: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_equipment_needs(self, farm_size: float, available: List[str], tasks: List[str]) -> Dict[str, Any]:
        """Analyze what equipment is needed based on farm size and tasks"""
        recommendations = {
            "essential_equipment": [],
            "recommended_equipment": [],
            "optional_equipment": [],
            "missing_equipment": []
        }
        
        # Essential equipment for any farm
        essential = ["tractor", "plow", "harvester", "irrigation_system"]
        for item in essential:
            if item not in available:
                recommendations["missing_equipment"].append({
                    "equipment": item,
                    "priority": "essential",
                    "estimated_cost": self._get_equipment_cost(item),
                    "reason": f"Essential for basic farming operations"
                })
        
        # Size-based recommendations
        if farm_size > 50:
            if "large_tractor" not in available:
                recommendations["recommended_equipment"].append({
                    "equipment": "large_tractor",
                    "priority": "high",
                    "estimated_cost": 50000,
                    "reason": f"Farm size ({farm_size} acres) requires larger equipment"
                })
        
        if farm_size > 100:
            if "combine_harvester" not in available:
                recommendations["recommended_equipment"].append({
                    "equipment": "combine_harvester",
                    "priority": "high",
                    "estimated_cost": 100000,
                    "reason": f"Large farm ({farm_size} acres) needs efficient harvesting"
                })
        
        # Task-based recommendations
        task_equipment_map = {
            "spraying": ["sprayer", "pesticide_applicator"],
            "irrigation": ["drip_irrigation", "sprinkler_system"],
            "harvesting": ["harvester", "thresher"],
            "soil_preparation": ["rotavator", "disc_plow"]
        }
        
        for task in tasks:
            if task in task_equipment_map:
                for equipment in task_equipment_map[task]:
                    if equipment not in available:
                        recommendations["missing_equipment"].append({
                            "equipment": equipment,
                            "priority": "task_specific",
                            "estimated_cost": self._get_equipment_cost(equipment),
                            "reason": f"Required for {task} operations"
                        })
        
        return recommendations
    
    def _generate_maintenance_schedule(self, equipment: List[str]) -> List[Dict[str, Any]]:
        """Generate maintenance schedule for available equipment"""
        maintenance_schedule = []
        
        maintenance_map = {
            "tractor": {
                "frequency": "monthly",
                "tasks": ["Oil change", "Filter replacement", "Tire pressure check"],
                "estimated_cost": 200
            },
            "harvester": {
                "frequency": "seasonal",
                "tasks": ["Blade sharpening", "Belt replacement", "Engine tune-up"],
                "estimated_cost": 500
            },
            "irrigation_system": {
                "frequency": "weekly",
                "tasks": ["Filter cleaning", "Pipe inspection", "Pump maintenance"],
                "estimated_cost": 100
            },
            "sprayer": {
                "frequency": "monthly",
                "tasks": ["Nozzle cleaning", "Tank cleaning", "Calibration check"],
                "estimated_cost": 150
            }
        }
        
        for item in equipment:
            if item in maintenance_map:
                schedule = maintenance_map[item].copy()
                schedule["equipment"] = item
                schedule["next_maintenance"] = self._calculate_next_maintenance(schedule["frequency"])
                maintenance_schedule.append(schedule)
        
        return maintenance_schedule
    
    def _optimize_equipment_usage(self, equipment: List[str], tasks: List[str]) -> Dict[str, Any]:
        """Optimize equipment usage for efficiency"""
        optimization = {
            "usage_schedule": {},
            "efficiency_tips": [],
            "cost_savings": 0
        }
        
        # Create usage schedule
        for item in equipment:
            optimization["usage_schedule"][item] = {
                "recommended_hours_per_day": self._get_optimal_hours(item),
                "maintenance_breaks": self._get_maintenance_breaks(item),
                "fuel_efficiency_tips": self._get_efficiency_tips(item)
            }
        
        # Add efficiency tips
        optimization["efficiency_tips"] = [
            "Schedule similar tasks together to reduce equipment setup time",
            "Use GPS guidance for precise field operations",
            "Maintain proper tire pressure for fuel efficiency",
            "Clean equipment after each use to prevent corrosion"
        ]
        
        # Calculate potential cost savings
        optimization["cost_savings"] = len(equipment) * 500  # Estimated annual savings
        
        return optimization
    
    def _analyze_budget_needs(self, recommendations: Dict, budget: float) -> Dict[str, Any]:
        """Analyze budget requirements for equipment"""
        total_cost = 0
        priority_costs = {"essential": 0, "high": 0, "medium": 0, "low": 0}
        
        # Calculate costs for missing equipment
        for category in ["missing_equipment", "recommended_equipment"]:
            for item in recommendations.get(category, []):
                cost = item.get("estimated_cost", 0)
                priority = item.get("priority", "medium")
                priority_costs[priority] += cost
                total_cost += cost
        
        return {
            "total_required_budget": total_cost,
            "budget_by_priority": priority_costs,
            "budget_available": budget,
            "budget_deficit": max(0, total_cost - budget),
            "recommendations": self._get_budget_recommendations(total_cost, budget)
        }
    
    def _get_equipment_cost(self, equipment: str) -> float:
        """Get estimated cost for equipment"""
        cost_map = {
            "tractor": 25000,
            "large_tractor": 50000,
            "harvester": 75000,
            "combine_harvester": 100000,
            "sprayer": 15000,
            "irrigation_system": 20000,
            "drip_irrigation": 30000,
            "sprinkler_system": 25000,
            "rotavator": 8000,
            "disc_plow": 5000,
            "thresher": 12000,
            "pesticide_applicator": 10000
        }
        return cost_map.get(equipment, 10000)
    
    def _calculate_next_maintenance(self, frequency: str) -> str:
        """Calculate next maintenance date"""
        today = datetime.now()
        if frequency == "weekly":
            next_date = today + timedelta(weeks=1)
        elif frequency == "monthly":
            next_date = today + timedelta(days=30)
        elif frequency == "seasonal":
            next_date = today + timedelta(days=90)
        else:
            next_date = today + timedelta(days=30)
        
        return next_date.strftime("%Y-%m-%d")
    
    def _get_optimal_hours(self, equipment: str) -> int:
        """Get optimal daily usage hours for equipment"""
        hours_map = {
            "tractor": 8,
            "harvester": 10,
            "sprayer": 6,
            "irrigation_system": 24
        }
        return hours_map.get(equipment, 8)
    
    def _get_maintenance_breaks(self, equipment: str) -> List[str]:
        """Get recommended maintenance breaks for equipment"""
        return ["Every 50 hours", "Before and after season", "When performance degrades"]
    
    def _get_efficiency_tips(self, equipment: str) -> List[str]:
        """Get efficiency tips for specific equipment"""
        tips_map = {
            "tractor": ["Maintain proper RPM", "Use appropriate gear ratios", "Keep tires properly inflated"],
            "harvester": ["Adjust settings for crop conditions", "Clean regularly", "Monitor grain loss"],
            "sprayer": ["Calibrate nozzles", "Use proper pressure", "Avoid spraying in wind"]
        }
        return tips_map.get(equipment, ["Regular maintenance", "Proper operation", "Timely repairs"])
    
    def _get_budget_recommendations(self, required: float, available: float) -> List[str]:
        """Get budget recommendations"""
        recommendations = []
        
        if required > available:
            recommendations.append("Consider equipment leasing for expensive items")
            recommendations.append("Prioritize essential equipment purchases")
            recommendations.append("Look for government subsidies or financing options")
            recommendations.append("Consider used equipment for cost savings")
        else:
            recommendations.append("Budget is sufficient for recommended equipment")
            recommendations.append("Consider additional optional equipment")
            recommendations.append("Set aside funds for maintenance and repairs")
        
        return recommendations
    
    def _calculate_equipment_value(self, equipment: List[str]) -> float:
        """Calculate total value of available equipment"""
        total_value = 0
        for item in equipment:
            total_value += self._get_equipment_cost(item)
        return total_value
