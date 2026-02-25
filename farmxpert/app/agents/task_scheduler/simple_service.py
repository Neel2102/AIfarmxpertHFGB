"""
Simple Task Scheduler Service for FarmXpert Main Project
A simplified version that works without complex dependencies
"""

import asyncio
import warnings
import sys
import os
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from pathlib import Path

# Suppress all warnings for this module
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Add app to path
app_path = Path(__file__).resolve().parents[3] / "app"
sys.path.insert(0, str(app_path))


class SimpleTaskSchedulerService:
    """Simplified Task Scheduler Service that works with the main project"""
    
    def __init__(self):
        """Initialize the Simple Task Scheduler Service"""
        pass
    
    async def generate_daily_plan(self, 
                                 location: Dict[str, Any],
                                 crop_info: Dict[str, Any],
                                 resources: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a daily farm task plan using basic logic and available data
        
        Args:
            location: Location data with city, state, coordinates
            crop_info: Crop information (name, growth_stage, area)
            resources: Resource constraints (labor, tractor_hours, pump_hours)
        """
        try:
            # Generate basic task plan
            tasks = self._generate_basic_tasks(crop_info, location)
            
            # Prioritize tasks based on crop stage and conditions
            prioritized_tasks = self._prioritize_tasks(tasks, crop_info)
            
            # Generate LLM explanation
            explanation = await self._generate_simple_explanation(crop_info, prioritized_tasks)
            
            result = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "crop": crop_info.get("crop", "Unknown crop"),
                "growth_stage": crop_info.get("growth_stage", "Unknown stage"),
                "location": location.get("city", "Unknown location"),
                "tasks_for_today": prioritized_tasks,
                "warnings": self._generate_warnings(crop_info),
                "recommendations": self._generate_recommendations(crop_info, prioritized_tasks),
                "summary": f"Generated {len(prioritized_tasks)} tasks for {crop_info.get('crop', 'crop')} management",
                "llm_explanation": explanation,
                "agent_data_summary": {
                    "status": "simplified_mode",
                    "note": "Using simplified task scheduling without full agent integration"
                }
            }
            
            return {
                "success": True,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Task scheduling failed: {str(e)}",
                "error_type": "ProcessingError"
            }
    
    def _generate_basic_tasks(self, crop_info: Dict[str, Any], location: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate basic tasks based on crop and location"""
        crop_name = crop_info.get("crop", "crops")
        growth_stage = crop_info.get("growth_stage", "current stage")
        
        tasks = []
        
        # Irrigation task
        tasks.append({
            "task": "Irrigation",
            "action": "IRRIGATE",
            "details": f"Apply water for {crop_name} in {growth_stage} stage",
            "reason": "Regular irrigation needed for crop health",
            "priority": "High"
        })
        
        # Fertilizer task
        tasks.append({
            "task": "Fertilizer application",
            "action": "APPLY",
            "details": f"Apply balanced fertilizer for {crop_name} in {growth_stage}",
            "reason": "Nutrient management for crop development",
            "priority": "Medium"
        })
        
        # Monitoring task
        tasks.append({
            "task": "Crop monitoring",
            "action": "MONITOR",
            "details": f"Monitor {crop_name} growth and health in {growth_stage}",
            "reason": "Regular monitoring for early issue detection",
            "priority": "Medium"
        })
        
        # Soil health task
        tasks.append({
            "task": "Soil health check",
            "action": "CHECK",
            "details": f"Check soil moisture and health for {crop_name}",
            "reason": "Soil health monitoring for optimal growth",
            "priority": "Low"
        })
        
        # Pest control task (conditional)
        if growth_stage.lower() in ["vegetative", "flowering", "fruiting"]:
            tasks.append({
                "task": "Pest control",
                "action": "SPRAY",
                "details": f"Apply preventive pest control for {crop_name}",
                "reason": "Pest prevention during active growth stages",
                "priority": "Medium"
            })
        
        return tasks
    
    def _prioritize_tasks(self, tasks: List[Dict[str, Any]], crop_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize tasks based on crop stage and conditions"""
        growth_stage = crop_info.get("growth_stage", "").lower()
        
        # Adjust priorities based on growth stage
        for task in tasks:
            task_name = task["task"].lower()
            
            if "seedling" in growth_stage or "nursery" in growth_stage:
                if "irrigation" in task_name:
                    task["priority"] = "High"
                elif "fertilizer" in task_name:
                    task["priority"] = "Low"
            elif "vegetative" in growth_stage:
                if "fertilizer" in task_name:
                    task["priority"] = "High"
                elif "irrigation" in task_name:
                    task["priority"] = "High"
            elif "flowering" in growth_stage or "fruiting" in growth_stage:
                if "pest control" in task_name:
                    task["priority"] = "High"
                elif "irrigation" in task_name:
                    task["priority"] = "High"
            elif "harvest" in growth_stage:
                if "monitoring" in task_name:
                    task["priority"] = "High"
        
        # Sort by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        tasks.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return tasks
    
    def _generate_warnings(self, crop_info: Dict[str, Any]) -> List[str]:
        """Generate relevant warnings based on crop info"""
        warnings = []
        growth_stage = crop_info.get("growth_stage", "").lower()
        
        if "flowering" in growth_stage:
            warnings.append("Monitor for pest pressure during flowering stage")
        
        if "harvest" in growth_stage:
            warnings.append("Prepare for harvest - check weather conditions")
        
        return warnings
    
    def _generate_recommendations(self, crop_info: Dict[str, Any], tasks: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on tasks and crop info"""
        recommendations = []
        crop_name = crop_info.get("crop", "crops")
        
        # Add general recommendations
        recommendations.append(f"Maintain regular monitoring schedule for {crop_name}")
        
        # Add task-specific recommendations
        high_priority_tasks = [t for t in tasks if t["priority"] == "High"]
        if high_priority_tasks:
            recommendations.append("Focus on completing high-priority tasks first")
        
        return recommendations
    
    async def _generate_simple_explanation(self, crop_info: Dict[str, Any], tasks: List[Dict[str, Any]]) -> str:
        """Generate a simple explanation without LLM"""
        crop_name = crop_info.get("crop", "crops")
        growth_stage = crop_info.get("growth_stage", "current stage")
        high_priority_count = len([t for t in tasks if t["priority"] == "High"])
        
        explanation = (
            f"Today's farm plan for {crop_name} in {growth_stage} stage includes {len(tasks)} tasks. "
            f"Focus on the {high_priority_count} high-priority tasks first, particularly irrigation and monitoring. "
            f"Regular attention to these tasks will ensure optimal crop development and yield."
        )
        
        return explanation
    
    async def update_task_status(self, 
                                task_name: str, 
                                task_date: str, 
                                status: str) -> Dict[str, Any]:
        """Update the status of a specific task (simplified version)"""
        return {
            "success": True,
            "message": f"Task '{task_name}' status updated to '{status}' (simplified mode)",
            "timestamp": datetime.now().isoformat(),
            "note": "Task tracking not available in simplified mode"
        }
    
    async def get_task_status(self, task_name: str, task_date: str) -> Dict[str, Any]:
        """Get the current status of a specific task (simplified version)"""
        return {
            "success": True,
            "task_name": task_name,
            "date": task_date,
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
            "note": "Task tracking not available in simplified mode"
        }


# Create singleton instance
simple_task_scheduler_service = SimpleTaskSchedulerService()
