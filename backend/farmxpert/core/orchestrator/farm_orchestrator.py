from __future__ import annotations
from typing import Dict, Any, Optional, List
from datetime import datetime
from farmxpert.core.utils.logger import get_logger
from farmxpert.core.base_agent.agent_registry import create_agent
from .intent_engine import IntentEngine, IntentResult
from .workflow_engine import WorkflowEngine, WorkflowResult
from .session_manager import SessionManager, ConversationTurn
from .response_synthesizer import ResponseSynthesizer


class FarmOrchestrator:
    """Enhanced Farm Orchestrator with intent understanding, workflow management, and session tracking"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", session_manager: SessionManager | None = None) -> None:
        self.logger = get_logger("orchestrator")
        
        # Initialize core components
        self.intent_engine = IntentEngine()
        self.workflow_engine = WorkflowEngine()
        # Allow dependency injection for shared session manager to avoid mismatch
        self.session_manager = session_manager if session_manager is not None else SessionManager(redis_url)
        self.synthesizer = ResponseSynthesizer()

        # Agent factory function
        self.agent_factory = create_agent
    
    async def orchestrate(self, query: str, session_id: Optional[str] = None, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Main orchestration method that handles the complete workflow"""
        start_time = datetime.now()
        workflow_id = None
        
        try:
            # Step 1: Get or create session
            if not session_id:
                session_id = await self.session_manager.create_session()
            
            # Step 2: Classify intent
            intent_result = self.intent_engine.classify_intent(query)
            self.logger.info("intent_classified", 
                           intent=intent_result.intent_type.value,
                           confidence=intent_result.confidence,
                           entities=intent_result.entities)
            
            # Step 3: Create workflow based on intent
            workflow_id = f"workflow_{int(start_time.timestamp())}"
            workflow = await self.workflow_engine.create_workflow(
                workflow_id=workflow_id,
                intent_type=intent_result.intent_type,
                session_id=session_id
            )
            
            # Step 4: Execute agents based on intent
            agent_responses = {}
            recommendations = []
            warnings = []
            insights = []
            
            # Determine which agents to invoke based on intent
            agents_to_invoke = self._get_agents_for_intent(intent_result.intent_type)
            
            for agent_name in agents_to_invoke:
                try:
                    # Create agent instance
                    agent = self.agent_factory(agent_name)
                    
                    # Prepare agent input
                    session_context = await self.session_manager.get_context_for_query(session_id, query)
                    merged_context = {**(context or {}), **session_context}
                    agent_input = {
                        "query": query,
                        "intent": intent_result.intent_type.value,
                        "entities": intent_result.entities,
                        "context": merged_context,
                        "session_id": session_id,
                        "workflow_id": workflow_id
                    }
                    
                    # Execute agent
                    agent_start = datetime.now()
                    agent_response = await agent.handle(agent_input)
                    agent_execution_time = (datetime.now() - agent_start).total_seconds()
                    
                    # Store agent response
                    agent_responses[agent_name] = {
                        "response": agent_response,
                        "execution_time": agent_execution_time,
                        "success": True
                    }
                    
                    # Extract recommendations, warnings, and insights
                    if isinstance(agent_response, dict):
                        recommendations.extend(agent_response.get("recommendations", []))
                        warnings.extend(agent_response.get("warnings", []))
                        insights.extend(agent_response.get("insights", []))
                    
                    self.logger.info("agent_completed", 
                                   agent=agent_name,
                                   execution_time=agent_execution_time,
                                   success=True)
                    
                except Exception as e:
                    self.logger.error("agent_failed", 
                                    agent=agent_name,
                                    error=str(e))
                    agent_responses[agent_name] = {
                        "error": str(e),
                        "success": False
                    }
                    warnings.append(f"Agent {agent_name} failed: {str(e)}")
            
            # Step 5: Synthesize final response
            # Simple recommendation aggregation and de-dup
            for resp in agent_responses.values():
                if isinstance(resp, dict) and resp.get("success") and isinstance(resp.get("response"), dict):
                    # normalize if agent returned Enhanced format
                    if "recommendations" in resp["response"]:
                        recommendations.extend(resp["response"].get("recommendations", []))
                        warnings.extend(resp["response"].get("warnings", []))
                        insights.extend(resp["response"].get("insights", []))

            # Deduplicate while preserving order
            def _dedup(seq):
                seen = set()
                out = []
                for x in seq:
                    # Normalize to string to avoid unhashable types (e.g., dict)
                    s = str(x)
                    if s not in seen:
                        seen.add(s)
                        out.append(s)
                return out
            recommendations = _dedup(recommendations)
            warnings = _dedup(warnings)
            insights = _dedup(insights)

            # Persist simple farm data from entities
            try:
                meas = intent_result.entities.get("measurement") if intent_result and intent_result.entities else None
                loc = intent_result.entities.get("location") if intent_result and intent_result.entities else None
                farm_updates: Dict[str, Any] = {}
                if isinstance(meas, dict) and str(meas.get("unit", "")).lower() in ["acre", "acres"]:
                    farm_updates["farm_size"] = meas.get("value")
                    farm_updates["farm_size_unit"] = "acres"
                if isinstance(loc, str) and loc:
                    farm_updates["farm_location"] = loc
                if farm_updates:
                    await self.session_manager.update_farm_data(session_id, farm_updates)
            except Exception:
                pass

            final_response = await self.synthesizer.synthesize_response(
                intent_result=intent_result,
                agent_responses=agent_responses,
                query=query
            )
            
            # Step 6: Update workflow status
            await self.workflow_engine.complete_workflow(workflow_id, agent_responses)
            
            # Step 7: Store conversation turn
            from .session_manager import ConversationTurn
            turn = ConversationTurn(
                timestamp=start_time,
                user_query=query,
                intent_result=intent_result,
                workflow_id=workflow_id,
                agent_responses=agent_responses,
                final_response=final_response,
                execution_time=(datetime.now() - start_time).total_seconds(),
                success=True
            )
            await self.session_manager.add_conversation_turn(session_id, turn)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            response = {
                "session_id": session_id,
                "workflow_id": workflow_id,
                "intent": {
                    "type": intent_result.intent_type.value,
                    "confidence": intent_result.confidence,
                    "entities": intent_result.entities,
                    "language": intent_result.language
                },
                "response": final_response,
                "execution_time": execution_time,
                "success": True,
                "workflow_summary": {
                    "status": "completed",
                    "agents_invoked": list(agent_responses.keys()),
                    "total_agents": len(agents_to_invoke),
                    "successful_agents": len([r for r in agent_responses.values() if r.get("success", False)])
                },
                "recommendations": recommendations[:5],  # Limit to top 5
                "warnings": warnings[:3],  # Limit to top 3
                "insights": insights[:3],  # Limit to top 3
                "agent_details": {
                    agent: {
                        "success": resp.get("success", False),
                        "execution_time": resp.get("execution_time", 0)
                    }
                    for agent, resp in agent_responses.items()
                }
            }
            
            self.logger.info("orchestration_completed", 
                           session_id=session_id,
                           workflow_id=workflow_id,
                           intent=intent_result.intent_type.value,
                           execution_time=execution_time,
                           success=True,
                           agents_invoked=len(agents_to_invoke))
            
            return response
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error("orchestration_failed", 
                            session_id=session_id,
                            query=query,
                            error=str(e),
                            execution_time=execution_time)
            
            # Create error turn if session exists
            if session_id:
                try:
                    intent_result = self.intent_engine.classify_intent(query)
                    turn = ConversationTurn(
                        timestamp=start_time,
                        user_query=query,
                        intent_result=intent_result,
                        workflow_id=workflow_id,
                        execution_time=execution_time,
                        success=False,
                        error_message=str(e)
                    )
                    await self.session_manager.add_conversation_turn(session_id, turn)
                except:
                    pass  # Don't fail if session storage fails
            
            return {
                "session_id": session_id,
                "error": str(e),
                "workflow_id": workflow_id,
                "execution_time": execution_time,
                "success": False
            }
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific workflow"""
        return self.workflow_engine.get_workflow_status(workflow_id)
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session"""
        session = await self.session_manager.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "farm_location": session.farm_location,
            "farm_size": session.farm_size,
            "farm_size_unit": session.farm_size_unit,
            "preferred_language": session.preferred_language,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "conversation_turns": len(session.conversation_history),
            "active_workflows": session.active_workflows,
            "farm_data_keys": list(session.farm_data.keys()),
            "preferences": session.preferences
        }
    
    async def update_farm_data(self, session_id: str, farm_data: Dict[str, Any]):
        """Update farm data for a session"""
        await self.session_manager.update_farm_data(session_id, farm_data)
    
    async def update_preferences(self, session_id: str, preferences: Dict[str, Any]):
        """Update user preferences for a session"""
        await self.session_manager.update_preferences(session_id, preferences)
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        return await self.session_manager.get_session_statistics(session_id)
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        await self.session_manager.cleanup_expired_sessions()
    
    def classify_intent(self, query: str) -> IntentResult:
        """Classify the intent of a query (for testing/debugging)"""
        return self.intent_engine.classify_intent(query)
    
    def get_available_intents(self) -> Dict[str, str]:
        """Get all available intent types and their descriptions"""
        from .intent_engine import IntentType
        return {intent.value: intent.name for intent in IntentType}
    
    def _get_agents_for_intent(self, intent_type) -> List[str]:
        """Determine which agents to invoke based on intent type"""
        from .intent_engine import IntentType
        
        # Map intents to relevant agents
        intent_agent_mapping = {
            IntentType.CROP_PLANNING: [
                "crop_selector",
                "soil_health", 
                "weather_watcher",
                "seed_selection"
            ],
            IntentType.SOIL_HEALTH: [
                "soil_health",
                "fertilizer_advisor"
            ],
            IntentType.PEST_DISEASE_DIAGNOSIS: [
                "pest_disease_diagnostic",
                "soil_health"
            ],
            IntentType.YIELD_OPTIMIZATION: [
                "yield_predictor",
                "soil_health",
                "fertilizer_advisor",
                "irrigation_planner"
            ],
            IntentType.TASK_SCHEDULING: [
                "task_scheduler",
                "weather_watcher"
            ],
            IntentType.MARKET_ANALYSIS: [
                "market_intelligence",
                "profit_optimization"
            ],
            IntentType.WEATHER_QUERY: [
                "weather_watcher"
            ],
            IntentType.FERTILIZER_ADVICE: [
                "fertilizer_advisor",
                "soil_health"
            ],
            IntentType.IRRIGATION_PLANNING: [
                "irrigation_planner",
                "weather_watcher"
            ],
            IntentType.HARVEST_PLANNING: [
                "growth_stage_monitor",
                "task_scheduler"
            ],
            IntentType.RISK_MANAGEMENT: [
                "crop_insurance_risk",
                "weather_watcher"
            ],
            IntentType.FARMER_SUPPORT: [
                "farmer_coach",
                "community_engagement"
            ]
        }
        
        # Get agents for the intent, fallback to general agents
        agents = intent_agent_mapping.get(intent_type, [
            "farmer_coach",
            "soil_health"
        ])
        
        # Filter to only include agents that exist in the registry
        try:
            from farmxpert.core.base_agent.agent_registry import AgentRegistry
            registry = AgentRegistry()
            available_agents = registry.list_agents().keys()
            return [agent for agent in agents if agent in available_agents]
        except:
            # Fallback to basic agents if registry fails
            return ["crop_selector", "soil_health"]


