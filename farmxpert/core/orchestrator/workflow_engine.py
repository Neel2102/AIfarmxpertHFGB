from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, deque
from farmxpert.core.utils.logger import get_logger
from .intent_engine import IntentType


class TaskStatus(Enum):
    """Status of a task in the workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    """Priority levels for task execution"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WorkflowTask:
    """Represents a task in the workflow"""
    id: str
    agent_name: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    workflow_id: str
    tasks: Dict[str, WorkflowTask]
    final_output: Dict[str, Any]
    execution_time: float
    success: bool
    error_message: Optional[str] = None


class WorkflowEngine:
    """Engine for managing DAG-based agent workflows"""
    
    def __init__(self):
        self.logger = get_logger("workflow_engine")
        self._workflow_templates = self._build_workflow_templates()
        self._agent_dependencies = self._build_agent_dependencies()
        self._active_workflows: Dict[str, Dict[str, WorkflowTask]] = {}
    
    def _build_workflow_templates(self) -> Dict[IntentType, List[Dict[str, Any]]]:
        """Build workflow templates for different intents"""
        return {
            IntentType.CROP_PLANNING: [
                {"agent": "soil_health_agent", "priority": TaskPriority.HIGH},
                {"agent": "weather_watcher_agent", "priority": TaskPriority.HIGH},
                {"agent": "market_intelligence_agent", "priority": TaskPriority.NORMAL},
                {"agent": "crop_selector_agent", "priority": TaskPriority.CRITICAL, 
                 "depends_on": ["soil_health_agent", "weather_watcher_agent", "market_intelligence_agent"]},
                {"agent": "seed_selection_agent", "priority": TaskPriority.HIGH,
                 "depends_on": ["crop_selector_agent"]},
                {"agent": "fertilizer_advisor_agent", "priority": TaskPriority.NORMAL,
                 "depends_on": ["soil_health_agent", "crop_selector_agent"]},
                {"agent": "irrigation_planner_agent", "priority": TaskPriority.NORMAL,
                 "depends_on": ["weather_watcher_agent", "crop_selector_agent"]}
            ],
            IntentType.PEST_DISEASE_DIAGNOSIS: [
                {"agent": "pest_disease_diagnostic_agent", "priority": TaskPriority.CRITICAL},
                {"agent": "fertilizer_advisor_agent", "priority": TaskPriority.NORMAL,
                 "depends_on": ["pest_disease_diagnostic_agent"]},
                {"agent": "irrigation_planner_agent", "priority": TaskPriority.LOW,
                 "depends_on": ["pest_disease_diagnostic_agent"]}
            ],
            IntentType.YIELD_OPTIMIZATION: [
                {"agent": "yield_predictor_agent", "priority": TaskPriority.HIGH},
                {"agent": "soil_health_agent", "priority": TaskPriority.NORMAL},
                {"agent": "fertilizer_advisor_agent", "priority": TaskPriority.HIGH,
                 "depends_on": ["soil_health_agent"]},
                {"agent": "irrigation_planner_agent", "priority": TaskPriority.NORMAL},
                {"agent": "profit_optimization_agent", "priority": TaskPriority.CRITICAL,
                 "depends_on": ["yield_predictor_agent", "fertilizer_advisor_agent"]}
            ],
            IntentType.TASK_SCHEDULING: [
                {"agent": "task_scheduler_agent", "priority": TaskPriority.CRITICAL},
                {"agent": "machinery_equipment_agent", "priority": TaskPriority.NORMAL,
                 "depends_on": ["task_scheduler_agent"]},
                {"agent": "farm_layout_mapping_agent", "priority": TaskPriority.LOW,
                 "depends_on": ["task_scheduler_agent"]}
            ],
            IntentType.MARKET_ANALYSIS: [
                {"agent": "market_intelligence_agent", "priority": TaskPriority.CRITICAL},
                {"agent": "profit_optimization_agent", "priority": TaskPriority.HIGH,
                 "depends_on": ["market_intelligence_agent"]},
                {"agent": "logistics_storage_agent", "priority": TaskPriority.NORMAL,
                 "depends_on": ["market_intelligence_agent"]}
            ],
            IntentType.SOIL_HEALTH: [
                {"agent": "soil_health_agent", "priority": TaskPriority.CRITICAL},
                {"agent": "fertilizer_advisor_agent", "priority": TaskPriority.HIGH,
                 "depends_on": ["soil_health_agent"]}
            ],
            IntentType.WEATHER_QUERY: [
                {"agent": "weather_watcher_agent", "priority": TaskPriority.CRITICAL}
            ],
            IntentType.FERTILIZER_ADVICE: [
                {"agent": "soil_health_agent", "priority": TaskPriority.HIGH},
                {"agent": "fertilizer_advisor_agent", "priority": TaskPriority.CRITICAL,
                 "depends_on": ["soil_health_agent"]}
            ],
            IntentType.IRRIGATION_PLANNING: [
                {"agent": "weather_watcher_agent", "priority": TaskPriority.HIGH},
                {"agent": "irrigation_planner_agent", "priority": TaskPriority.CRITICAL,
                 "depends_on": ["weather_watcher_agent"]}
            ],
            IntentType.HARVEST_PLANNING: [
                {"agent": "yield_predictor_agent", "priority": TaskPriority.HIGH},
                {"agent": "market_intelligence_agent", "priority": TaskPriority.HIGH},
                {"agent": "logistics_storage_agent", "priority": TaskPriority.NORMAL,
                 "depends_on": ["yield_predictor_agent", "market_intelligence_agent"]}
            ],
            IntentType.RISK_MANAGEMENT: [
                {"agent": "crop_insurance_risk_agent", "priority": TaskPriority.CRITICAL},
                {"agent": "weather_watcher_agent", "priority": TaskPriority.NORMAL},
                {"agent": "pest_disease_diagnostic_agent", "priority": TaskPriority.NORMAL}
            ],
            IntentType.FARMER_SUPPORT: [
                {"agent": "farmer_coach_agent", "priority": TaskPriority.CRITICAL},
                {"agent": "compliance_certification_agent", "priority": TaskPriority.LOW},
                {"agent": "community_engagement_agent", "priority": TaskPriority.LOW}
            ]
        }
    
    def _build_agent_dependencies(self) -> Dict[str, Set[str]]:
        """Build agent dependency mapping"""
        return {
            "crop_selector_agent": {"soil_health_agent", "weather_watcher_agent", "market_intelligence_agent"},
            "seed_selection_agent": {"crop_selector_agent"},
            "fertilizer_advisor_agent": {"soil_health_agent"},
            "irrigation_planner_agent": {"weather_watcher_agent"},
            "profit_optimization_agent": {"yield_predictor_agent", "market_intelligence_agent"},
            "logistics_storage_agent": {"yield_predictor_agent", "market_intelligence_agent"},
            "machinery_equipment_agent": {"task_scheduler_agent"},
            "farm_layout_mapping_agent": {"task_scheduler_agent"}
        }
    
    def create_workflow(self, intent: IntentType, context: Dict[str, Any]) -> str:
        """Create a new workflow for the given intent"""
        workflow_id = f"workflow_{intent.value}_{int(asyncio.get_event_loop().time() * 1000)}"
        
        # Get workflow template
        template = self._workflow_templates.get(intent, [])
        
        # Create tasks
        tasks = {}
        for i, task_config in enumerate(template):
            task_id = f"{workflow_id}_task_{i}"
            task = WorkflowTask(
                id=task_id,
                agent_name=task_config["agent"],
                inputs=context.copy(),
                priority=task_config.get("priority", TaskPriority.NORMAL),
                dependencies=set(task_config.get("depends_on", []))
            )
            tasks[task_id] = task
        
        # Build dependency graph
        self._build_dependency_graph(tasks)
        
        # Store workflow
        self._active_workflows[workflow_id] = tasks
        
        self.logger.info("workflow_created", 
                        workflow_id=workflow_id, 
                        intent=intent.value, 
                        task_count=len(tasks))
        
        return workflow_id
    
    def _build_dependency_graph(self, tasks: Dict[str, WorkflowTask]):
        """Build the dependency graph between tasks"""
        # Create mapping from agent names to task IDs
        agent_to_task = {}
        for task_id, task in tasks.items():
            agent_to_task[task.agent_name] = task_id
        
        # Set up dependencies
        for task_id, task in tasks.items():
            # Create a copy of dependencies to avoid modification during iteration
            dependencies_copy = set(task.dependencies)
            for dep_agent in dependencies_copy:
                if dep_agent in agent_to_task:
                    dep_task_id = agent_to_task[dep_agent]
                    task.dependencies.add(dep_task_id)
                    tasks[dep_task_id].dependents.add(task_id)
    
    async def execute_workflow(self, workflow_id: str, agent_factory) -> WorkflowResult:
        """Execute a workflow with the given agent factory"""
        if workflow_id not in self._active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        tasks = self._active_workflows[workflow_id]
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Execute tasks in dependency order
            await self._execute_tasks(tasks, agent_factory)
            
            # Collect final output
            final_output = self._synthesize_output(tasks)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            result = WorkflowResult(
                workflow_id=workflow_id,
                tasks=tasks,
                final_output=final_output,
                execution_time=execution_time,
                success=True
            )
            
            self.logger.info("workflow_completed", 
                           workflow_id=workflow_id, 
                           execution_time=execution_time,
                           task_count=len(tasks))
            
            return result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.error("workflow_failed", 
                            workflow_id=workflow_id, 
                            error=str(e),
                            execution_time=execution_time)
            
            return WorkflowResult(
                workflow_id=workflow_id,
                tasks=tasks,
                final_output={},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    async def _execute_tasks(self, tasks: Dict[str, WorkflowTask], agent_factory):
        """Execute tasks in dependency order"""
        # Create execution queue
        execution_queue = deque()
        completed_tasks = set()
        
        # Initialize queue with tasks that have no dependencies
        for task_id, task in tasks.items():
            if not task.dependencies:
                execution_queue.append(task_id)
        
        # Execute tasks
        while execution_queue:
            # Sort by priority
            execution_queue = deque(sorted(
                execution_queue, 
                key=lambda tid: tasks[tid].priority.value, 
                reverse=True
            ))
            
            task_id = execution_queue.popleft()
            task = tasks[task_id]
            
            if task.status == TaskStatus.COMPLETED:
                continue
            
            # Execute task
            try:
                task.status = TaskStatus.RUNNING
                task_start_time = asyncio.get_event_loop().time()
                
                # Create and execute agent
                agent = agent_factory(task.agent_name)
                result = await agent.handle(task.inputs)
                
                task.outputs = result
                task.status = TaskStatus.COMPLETED
                task.execution_time = asyncio.get_event_loop().time() - task_start_time
                
                completed_tasks.add(task_id)
                
                self.logger.info("task_completed", 
                               task_id=task_id, 
                               agent=task.agent_name,
                               execution_time=task.execution_time)
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                self.logger.error("task_failed", 
                                task_id=task_id, 
                                agent=task.agent_name,
                                error=str(e))
                raise
            
            # Add dependent tasks to queue if their dependencies are met
            for dependent_id in task.dependents:
                dependent_task = tasks[dependent_id]
                if all(dep_id in completed_tasks for dep_id in dependent_task.dependencies):
                    execution_queue.append(dependent_id)
    
    def _synthesize_output(self, tasks: Dict[str, WorkflowTask]) -> Dict[str, Any]:
        """Synthesize final output from completed tasks"""
        output = {
            "workflow_summary": {
                "total_tasks": len(tasks),
                "completed_tasks": len([t for t in tasks.values() if t.status == TaskStatus.COMPLETED]),
                "failed_tasks": len([t for t in tasks.values() if t.status == TaskStatus.FAILED])
            },
            "agent_outputs": {},
            "recommendations": [],
            "warnings": []
        }
        
        # Collect agent outputs
        for task in tasks.values():
            if task.status == TaskStatus.COMPLETED:
                output["agent_outputs"][task.agent_name] = task.outputs
                
                # Extract recommendations and warnings
                if "recommendations" in task.outputs:
                    output["recommendations"].extend(task.outputs["recommendations"])
                if "warnings" in task.outputs:
                    output["warnings"].extend(task.outputs["warnings"])
        
        return output
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow"""
        if workflow_id not in self._active_workflows:
            return None
        
        tasks = self._active_workflows[workflow_id]
        
        status_counts = defaultdict(int)
        for task in tasks.values():
            status_counts[task.status.value] += 1
        
        return {
            "workflow_id": workflow_id,
            "status_counts": dict(status_counts),
            "total_tasks": len(tasks),
            "tasks": {
                task_id: {
                    "agent": task.agent_name,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "execution_time": task.execution_time,
                    "error": task.error_message
                }
                for task_id, task in tasks.items()
            }
        }
    
    def cleanup_workflow(self, workflow_id: str):
        """Clean up a completed workflow"""
        if workflow_id in self._active_workflows:
            del self._active_workflows[workflow_id]
            self.logger.info("workflow_cleaned_up", workflow_id=workflow_id)
    
    async def create_workflow(self, workflow_id: str, intent_type: IntentType, session_id: str) -> Dict[str, Any]:
        """Create a new workflow based on intent type"""
        try:
            # For now, create a simple workflow structure
            # In a full implementation, this would create a complex DAG based on the intent
            workflow_tasks = {}
            
            self.logger.info("workflow_created", 
                           workflow_id=workflow_id,
                           intent=intent_type.value,
                           session_id=session_id)
            
            return {
                "workflow_id": workflow_id,
                "intent_type": intent_type.value,
                "session_id": session_id,
                "status": "created",
                "tasks": workflow_tasks
            }
        except Exception as e:
            self.logger.error("workflow_creation_failed", 
                            workflow_id=workflow_id,
                            error=str(e))
            raise
    
    async def complete_workflow(self, workflow_id: str, agent_responses: Dict[str, Any]) -> None:
        """Mark workflow as completed and store results"""
        try:
            # Store the workflow results
            # In a full implementation, this would update the workflow status
            self.logger.info("workflow_completed", 
                           workflow_id=workflow_id,
                           agents_count=len(agent_responses))
        except Exception as e:
            self.logger.error("workflow_completion_failed", 
                            workflow_id=workflow_id,
                            error=str(e))
            raise
    
    def get_workflow(self, workflow_id: str) -> Optional[Any]:
        """Get workflow by ID"""
        # Return None for now - in full implementation would return actual workflow
        return None
    
    def get_workflows_by_session(self, session_id: str) -> List[Any]:
        """Get all workflows for a session"""
        # Return empty list for now - in full implementation would return actual workflows
        return []
    
    def cancel_workflow(self, workflow_id: str) -> None:
        """Cancel a workflow"""
        if workflow_id in self._active_workflows:
            del self._active_workflows[workflow_id]
            self.logger.info("workflow_cancelled", workflow_id=workflow_id)
