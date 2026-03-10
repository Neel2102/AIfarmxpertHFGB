from typing import List, Dict, Any
from datetime import datetime, timedelta

class TaskOptimizerTool:
    """
    Optimizes farm task scheduling using a greedy selection algorithm based on priority and constraints.
    """
    
    def optimize_schedule(self, tasks: List[Dict[str, Any]], available_hours_per_day: float = 8.0) -> Dict[str, Any]:
        """
        Schedule tasks based on priority (High > Medium > Low) and available time.
        """
        # Sort tasks by priority (High=3, Medium=2, Low=1)
        priority_map = {"high": 3, "medium": 2, "low": 1}
        
        sorted_tasks = sorted(
            tasks, 
            key=lambda x: priority_map.get(str(x.get("priority", "low")).lower(), 1), 
            reverse=True
        )
        
        schedule = {}
        current_date = datetime.now().date()
        daily_load = {}
        
        optimized_plan = []
        
        for task in sorted_tasks:
            duration = float(task.get("estimated_hours", 2.0))
            
            # Find first available day
            assigned_date = current_date
            while True:
                date_str = assigned_date.isoformat()
                current_load = daily_load.get(date_str, 0)
                
                if current_load + duration <= available_hours_per_day:
                    # Assign to this day
                    daily_load[date_str] = current_load + duration
                    
                    optimized_plan.append({
                        "task_id": task.get("id"),
                        "title": task.get("title"),
                        "scheduled_date": date_str,
                        "priority": task.get("priority"),
                        "status": "scheduled"
                    })
                    break
                else:
                    # Try next day
                    assigned_date += timedelta(days=1)
                    
        return {
            "success": True,
            "optimized_schedule": optimized_plan,
            "total_days_required": len(daily_load),
            "resource_utilization": daily_load
        }
