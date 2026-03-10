from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import TaskPrioritizationTool, RealTimeTrackingTool, WeatherAPITool
from farmxpert.services.gemini_service import gemini_service


class TaskSchedulerAgent(EnhancedBaseAgent):
    name = "task_scheduler"
    description = "Schedules and prioritizes farm tasks using optimization and real-time tracking"

    def _get_system_prompt(self) -> str:
        return """You are a Task Scheduler Agent specializing in farm task prioritization and scheduling.

Your expertise includes:
- AI-driven task prioritization under constraints
- Weather-aware scheduling
- Resource allocation (labor, machinery)
- Real-time task tracking integration
- Risk assessment and mitigation

Provide clear, actionable schedules and priorities with reasoning."""

    def _get_examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "Prioritize my tasks for this week",
                "output": "I’ve prioritized irrigation and weeding first due to hot weather. Planting is scheduled for Thursday morning when temperatures are lower."
            }
        ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            from farmxpert.tools.operations.task_optimizer import TaskOptimizerTool
            self.optimizer_tool = TaskOptimizerTool()
        except ImportError:
            self.optimizer_tool = None
            self.logger.warning("Could not import TaskOptimizerTool")

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            tools = inputs.get("tools", {})
            context = inputs.get("context", {})
            query = inputs.get("query", "")

            tasks = context.get("tasks", [])
            resources = context.get("resources", {})
            constraints = context.get("constraints", {})
            board_info = context.get("board_info", {})
            location = context.get("farm_location", inputs.get("location", "unknown"))

            weather_data = {}
            prioritization = {}
            optimization = {}
            tracking_sync = {}

            if "weather_api" in tools:
                try:
                    weather_data = await tools["weather_api"].get_irrigation_weather_forecast(location, days=7)
                except Exception as e:
                    self.logger.warning(f"Failed to get weather for scheduling: {e}")

            # --- REAL TOOL INTEGRATION ---
            if self.optimizer_tool and tasks:
                try:
                    # Use the greedy optimizer
                    opt_result = self.optimizer_tool.optimize_schedule(tasks)
                    if opt_result.get("success"):
                        prioritization = {"ordered_tasks": opt_result.get("optimized_schedule")}
                        optimization = {"final_order": opt_result.get("optimized_schedule")}
                        self.logger.info("Tasks optimized using TaskOptimizerTool")
                except Exception as e:
                    self.logger.warning(f"Failed to optimize tasks with tool: {e}")
            # -----------------------------

            if "task_prioritization" in tools and not prioritization:
                try:
                    prioritization = await tools["task_prioritization"].prioritize_tasks(tasks, resources, constraints, weather_data)
                except Exception as e:
                    self.logger.warning(f"Failed to prioritize tasks: {e}")

            if "task_prioritization" in tools and isinstance(prioritization, dict) and prioritization.get("ordered_tasks"):
                try:
                    optimization = await tools["task_prioritization"].optimize_sequence(prioritization["ordered_tasks"], objective=constraints.get("objective", "minimize_lateness"))
                except Exception as e:
                    self.logger.warning(f"Failed to optimize sequence: {e}")

            if "real_time_tracking" in tools and tasks:
                try:
                    tracking_sync = await tools["real_time_tracking"].sync_tasks(board_info, tasks)
                except Exception as e:
                    self.logger.warning(f"Failed to sync tasks: {e}")

            prompt = f"""
You are a farm operations scheduler. Based on the data below, produce a clear, prioritized weekly schedule with timing windows, resource allocations, and risks.

Query: "{query}"
Location: {location}
Tasks: {json.dumps(tasks, indent=2)}
Resources: {json.dumps(resources, indent=2)}
Constraints: {json.dumps(constraints, indent=2)}
Weather: {json.dumps(weather_data.get('daily_temperature', {}), indent=2)}
Prioritization: {json.dumps(prioritization.get('ordered_tasks', {}), indent=2)}
Optimization: {json.dumps(optimization.get('final_order', {}), indent=2)}
Tracking Sync: {json.dumps(tracking_sync.get('operation_status', {}), indent=2)}

Provide: schedule_table, priorities_summary, resource_plan, dependencies, risk_notes, next_actions
"""
            response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "task_scheduling"})

            return {
                "agent": self.name,
                "success": True,
                "response": response,
                "data": {
                    "weather_data": weather_data,
                    "prioritization": prioritization,
                    "optimization": optimization,
                    "tracking_sync": tracking_sync
                },
                "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
            }
        except Exception as e:
            self.logger.error(f"Error in task scheduler agent: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_basic_schedule(self, farm_id: int, active_crops: List) -> List[Dict[str, Any]]:
        """Generate basic task schedule"""
        tasks = []
        current_date = datetime.now()
        
        # Add weekly maintenance
        for i in range(4):
            task_date = current_date + timedelta(days=i*7)
            tasks.append({
                'farm_id': farm_id,
                'task_type': 'maintenance',
                'title': 'Weekly Farm Maintenance',
                'description': 'Check equipment, clean storage, update records',
                'scheduled_date': task_date.isoformat(),
                'status': 'pending',
                'priority': 'medium'
            })
            
        return tasks

    async def generate_daily_tasks(
        self, crop: str, growth_stage: str, soil_data: Dict[str, Any], location: str, farm_size: str
    ) -> List[Dict[str, Any]]:
        """Generates exactly 3 prioritized tasks for the day."""
        prompt = f"""
You are an expert farm manager. Based on the following farm profile, generate exactly 3 high-priority, actionable tasks for the farmer to complete today.

Farm Profile:
- Crop: {crop}
- Growth Stage: {growth_stage}
- Location: {location}
- Farm Size: {farm_size}
- Soil Readings: {soil_data}

Return the output ONLY as a valid JSON array of 3 objects. Do not include any markdown formatting or markdown code blocks (like ```json), just the raw JSON array.
Each object must have the following string keys:
- "title": A short, clear task title (e.g., "Check Irrigation System")
- "description": A 1-2 sentence explanation of how/why to do it
- "category": One of: "irrigation", "pest", "fertilizer", "harvest", "maintenance", "other"
- "priority": One of: "high", "medium", "low" (at least one should be "high")
"""
        try:
            # We use gemini_service directly to get the raw response
            import re
            response_text = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "daily_tasks"})
            
            # Clean response text if it contains markdown JSON blocks
            cleaned_text = re.sub(r'```json\s*', '', response_text)
            cleaned_text = re.sub(r'\s*```', '', cleaned_text)
            
            tasks = json.loads(cleaned_text.strip())
            
            if isinstance(tasks, list) and len(tasks) == 3:
                return tasks
            else:
                self.logger.warning(f"Unexpected task format from LLM: {tasks}")
                raise ValueError("LLM did not return exactly 3 tasks in the expected format.")
                
        except Exception as e:
            self.logger.error(f"Failed to generate daily tasks: {e}")
            # Fallback tasks if API fails
            return [
                {
                    "title": f"Inspect {crop} for pests",
                    "description": "Perform a walk-through to check for early signs of pest damage.",
                    "category": "pest",
                    "priority": "high"
                },
                {
                    "title": "Check soil moisture levels",
                    "description": "Verify irrigation system is functioning correctly.",
                    "category": "irrigation",
                    "priority": "medium"
                },
                {
                    "title": "Update farm log",
                    "description": "Record any inputs or observations from today.",
                    "category": "other",
                    "priority": "low"
                }
            ]
        
        # Add crop-specific tasks
        for crop in active_crops:
            if crop.planting_date:
                days_since_planting = (current_date - crop.planting_date).days
                
                if days_since_planting < 30:
                    tasks.append({
                        'farm_id': farm_id,
                        'crop_id': crop.id,
                        'task_type': 'irrigation',
                        'title': f'Irrigate {crop.crop_type}',
                        'description': 'Regular irrigation cycle',
                        'scheduled_date': current_date + timedelta(days=3),
                        'priority': 'medium',
                        'status': 'pending'
                    })
        
        return tasks
