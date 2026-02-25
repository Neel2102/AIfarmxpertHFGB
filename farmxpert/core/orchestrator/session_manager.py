from __future__ import annotations
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import asyncio
import json
import redis
from datetime import datetime, timedelta
from farmxpert.core.utils.logger import get_logger
from .intent_engine import IntentResult


@dataclass
class UserSession:
    """Represents a user session with context and memory"""
    session_id: str
    user_id: Optional[str] = None
    farm_location: Optional[str] = None
    farm_size: Optional[float] = None
    farm_size_unit: str = "hectares"
    preferred_language: str = "en"
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    farm_data: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    active_workflows: List[str] = field(default_factory=list)


@dataclass
class ConversationTurn:
    """Represents a single conversation turn"""
    timestamp: datetime
    user_query: str
    intent_result: IntentResult
    workflow_id: Optional[str] = None
    agent_responses: Dict[str, Any] = field(default_factory=dict)
    final_response: Optional[str] = None
    execution_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


class SessionManager:
    """Manages user sessions and conversation memory"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.logger = get_logger("session_manager")
        self.session_timeout = timedelta(hours=24)  # 24 hours
        self.max_conversation_history = 50  # Keep last 50 turns
        
        # Try to connect to Redis, fallback to in-memory if unavailable
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            self.logger.info("redis_connected", redis_url=redis_url)
        except Exception as e:
            self.logger.warning("redis_connection_failed", error=str(e), fallback="in_memory")
            self.use_redis = False
            self.redis_client = None
            self._in_memory_sessions = {}
    
    async def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new user session"""
        session_id = f"session_{user_id or 'anonymous'}_{int(asyncio.get_event_loop().time() * 1000)}"
        
        session = UserSession(
            session_id=session_id,
            user_id=user_id
        )
        
        # Store session
        await self._store_session(session)
        
        self.logger.info("session_created", session_id=session_id, user_id=user_id)
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Retrieve a user session from Redis or in-memory"""
        try:
            session_dict = None
            
            if self.use_redis and self.redis_client:
                # Try Redis first
                try:
                    session_data = self.redis_client.get(f"session:{session_id}")
                    if session_data:
                        session_dict = json.loads(session_data)
                except Exception as e:
                    self.logger.warning("redis_retrieval_failed", session_id=session_id, error=str(e))
            
            # Fallback to in-memory if Redis failed or not available
            if not session_dict and session_id in self._in_memory_sessions:
                session_dict = self._in_memory_sessions[session_id]
            
            if not session_dict:
                return None
            
            # Reconstruct session object
            session = UserSession(
                session_id=session_dict["session_id"],
                user_id=session_dict.get("user_id"),
                farm_location=session_dict.get("farm_location"),
                farm_size=session_dict.get("farm_size"),
                farm_size_unit=session_dict.get("farm_size_unit", "hectares"),
                preferred_language=session_dict.get("preferred_language", "en"),
                created_at=datetime.fromisoformat(session_dict["created_at"]),
                last_activity=datetime.fromisoformat(session_dict["last_activity"]),
                conversation_history=session_dict.get("conversation_history", []),
                farm_data=session_dict.get("farm_data", {}),
                preferences=session_dict.get("preferences", {}),
                active_workflows=session_dict.get("active_workflows", [])
            )
            
            return session
            
        except Exception as e:
            self.logger.error("session_retrieval_failed", session_id=session_id, error=str(e))
            return None
    
    async def update_session(self, session: UserSession):
        """Update a user session"""
        session.last_activity = datetime.now()
        await self._store_session(session)
    
    async def add_conversation_turn(self, session_id: str, turn: ConversationTurn):
        """Add a conversation turn to the session history"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Convert turn to dict for storage
        turn_dict = {
            "timestamp": turn.timestamp.isoformat(),
            "user_query": turn.user_query,
            "intent_result": {
                "intent_type": turn.intent_result.intent_type.value,
                "confidence": turn.intent_result.confidence,
                "entities": turn.intent_result.entities,
                "language": turn.intent_result.language
            },
            "workflow_id": turn.workflow_id,
            "agent_responses": turn.agent_responses,
            "final_response": turn.final_response,
            "execution_time": turn.execution_time,
            "success": turn.success,
            "error_message": turn.error_message
        }
        
        session.conversation_history.append(turn_dict)
        
        # Keep only the last N turns
        if len(session.conversation_history) > self.max_conversation_history:
            session.conversation_history = session.conversation_history[-self.max_conversation_history:]
        
        await self.update_session(session)
        
        self.logger.info("conversation_turn_added", 
                        session_id=session_id, 
                        turn_count=len(session.conversation_history))
    
    async def update_farm_data(self, session_id: str, farm_data: Dict[str, Any]):
        """Update farm data for a session"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.farm_data.update(farm_data)
        await self.update_session(session)
        
        self.logger.info("farm_data_updated", session_id=session_id, data_keys=list(farm_data.keys()))
    
    async def update_preferences(self, session_id: str, preferences: Dict[str, Any]):
        """Update user preferences for a session"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.preferences.update(preferences)
        await self.update_session(session)
        
        self.logger.info("preferences_updated", session_id=session_id, preference_keys=list(preferences.keys()))
    
    async def add_active_workflow(self, session_id: str, workflow_id: str):
        """Add an active workflow to the session"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if workflow_id not in session.active_workflows:
            session.active_workflows.append(workflow_id)
            await self.update_session(session)
            
            self.logger.info("active_workflow_added", session_id=session_id, workflow_id=workflow_id)
    
    async def remove_active_workflow(self, session_id: str, workflow_id: str):
        """Remove an active workflow from the session"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if workflow_id in session.active_workflows:
            session.active_workflows.remove(workflow_id)
            await self.update_session(session)
            
            self.logger.info("active_workflow_removed", session_id=session_id, workflow_id=workflow_id)
    
    async def get_context_for_query(self, session_id: str, query: str) -> Dict[str, Any]:
        """Get context information for a new query"""
        session = await self.get_session(session_id)
        if not session:
            return {}
        
        context = {
            "session_id": session_id,
            "user_id": session.user_id,
            "farm_location": session.farm_location,
            "farm_size": session.farm_size,
            "farm_size_unit": session.farm_size_unit,
            "preferred_language": session.preferred_language,
            "farm_data": session.farm_data,
            "preferences": session.preferences,
            "active_workflows": session.active_workflows,
            "recent_queries": self._get_recent_queries(session),
            "common_topics": self._extract_common_topics(session)
        }
        
        return context
    
    def _get_recent_queries(self, session: UserSession) -> List[str]:
        """Get recent user queries from conversation history"""
        recent_turns = session.conversation_history[-5:]  # Last 5 turns
        return [turn["user_query"] for turn in recent_turns]
    
    def _extract_common_topics(self, session: UserSession) -> List[str]:
        """Extract common topics from conversation history"""
        topics = []
        intent_counts = {}
        
        for turn in session.conversation_history:
            intent_type = turn["intent_result"]["intent_type"]
            intent_counts[intent_type] = intent_counts.get(intent_type, 0) + 1
        
        # Get top 3 most common intents
        sorted_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
        topics = [intent for intent, count in sorted_intents[:3]]
        
        return topics
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions from Redis and in-memory"""
        try:
            # Clean up Redis sessions
            if self.use_redis and self.redis_client:
                try:
                    session_keys = self.redis_client.keys("session:*")
                    
                    for key in session_keys:
                        session_data = self.redis_client.get(key)
                        if session_data:
                            session_dict = json.loads(session_data)
                            last_activity = datetime.fromisoformat(session_dict["last_activity"])
                            
                            if datetime.now() - last_activity > self.session_timeout:
                                self.redis_client.delete(key)
                                self.logger.info("expired_session_cleaned", session_key=key)
                except Exception as e:
                    self.logger.warning("redis_cleanup_failed", error=str(e))
            
            # Clean up in-memory sessions
            expired_keys = []
            for session_id, session_dict in self._in_memory_sessions.items():
                last_activity = datetime.fromisoformat(session_dict["last_activity"])
                if datetime.now() - last_activity > self.session_timeout:
                    expired_keys.append(session_id)
            
            for key in expired_keys:
                del self._in_memory_sessions[key]
                self.logger.info("expired_in_memory_session_cleaned", session_id=key)
            
        except Exception as e:
            self.logger.error("session_cleanup_failed", error=str(e))
    
    async def _store_session(self, session: UserSession):
        """Store session data in Redis or in-memory"""
        try:
            session_dict = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "farm_location": session.farm_location,
                "farm_size": session.farm_size,
                "farm_size_unit": session.farm_size_unit,
                "preferred_language": session.preferred_language,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "conversation_history": session.conversation_history,
                "farm_data": session.farm_data,
                "preferences": session.preferences,
                "active_workflows": session.active_workflows
            }
            
            if self.use_redis and self.redis_client:
                # Store with expiration in Redis
                key = f"session:{session.session_id}"
                self.redis_client.setex(
                    key,
                    int(self.session_timeout.total_seconds()),
                    json.dumps(session_dict)
                )
            else:
                # Store in memory
                self._in_memory_sessions[session.session_id] = session_dict
                self.logger.info("session_stored_in_memory", session_id=session.session_id)
            
        except Exception as e:
            self.logger.error("session_storage_failed", session_id=session.session_id, error=str(e))
            # Don't raise, just log the error and continue with in-memory
            if not self.use_redis:
                # Fallback to in-memory storage
                self._in_memory_sessions[session.session_id] = session_dict
                self.logger.info("session_fallback_to_memory", session_id=session.session_id)
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        session = await self.get_session(session_id)
        if not session:
            return {}
        
        total_turns = len(session.conversation_history)
        successful_turns = len([t for t in session.conversation_history if t.get("success", True)])
        
        # Calculate average execution time
        execution_times = [t.get("execution_time", 0) for t in session.conversation_history if t.get("execution_time")]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Get most common intents
        intent_counts = {}
        for turn in session.conversation_history:
            intent_type = turn["intent_result"]["intent_type"]
            intent_counts[intent_type] = intent_counts.get(intent_type, 0) + 1
        
        return {
            "session_id": session_id,
            "total_turns": total_turns,
            "successful_turns": successful_turns,
            "success_rate": (successful_turns / total_turns * 100) if total_turns > 0 else 0,
            "average_execution_time": avg_execution_time,
            "most_common_intents": intent_counts,
            "session_duration": (datetime.now() - session.created_at).total_seconds(),
            "active_workflows_count": len(session.active_workflows)
        }
