"""
Base Memory System for FarmXpert Agents
Provides the foundation for all memory operations in the multi-agent system
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field


class MemoryType(Enum):
    """Types of memory in the system"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"
    SHARED = "shared"
    PERSISTENT = "persistent"


class MemoryPriority(Enum):
    """Memory priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    ARCHIVE = 5


@dataclass
class MemoryMetadata:
    """Metadata for memory entries"""
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    priority: MemoryPriority = MemoryPriority.MEDIUM
    tags: List[str] = None
    source_agent: str = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed is None:
            self.last_accessed = self.created_at


class MemoryEntry(BaseModel):
    """A single memory entry"""
    id: str = Field(..., description="Unique identifier for the memory")
    content: Dict[str, Any] = Field(..., description="The actual memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    metadata: MemoryMetadata = Field(..., description="Memory metadata")
    
    class Config:
        arbitrary_types_allowed = True


class BaseMemory(ABC):
    """Abstract base class for all memory implementations"""
    
    def __init__(self, agent_id: str, memory_type: MemoryType):
        self.agent_id = agent_id
        self.memory_type = memory_type
        self._entries: Dict[str, MemoryEntry] = {}
        self._index: Dict[str, List[str]] = {}  # Tag-based indexing
    
    @abstractmethod
    async def store(self, content: Dict[str, Any], tags: List[str] = None, 
                   priority: MemoryPriority = MemoryPriority.MEDIUM,
                   expires_at: Optional[datetime] = None) -> str:
        """Store a memory entry"""
        pass
    
    @abstractmethod
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve memories based on query"""
        pass
    
    @abstractmethod
    async def update(self, memory_id: str, content: Dict[str, Any]) -> bool:
        """Update an existing memory entry"""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory entry"""
        pass
    
    @abstractmethod
    async def search_by_tags(self, tags: List[str]) -> List[MemoryEntry]:
        """Search memories by tags"""
        pass
    
    def _generate_id(self, content: Dict[str, Any]) -> str:
        """Generate a unique ID for memory content"""
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _update_access_metadata(self, memory_entry: MemoryEntry):
        """Update access metadata for a memory entry"""
        memory_entry.metadata.last_accessed = datetime.now()
        memory_entry.metadata.access_count += 1
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory system"""
        total_entries = len(self._entries)
        if total_entries == 0:
            return {
                "total_entries": 0,
                "memory_type": self.memory_type.value,
                "agent_id": self.agent_id
            }
        
        # Calculate statistics
        access_counts = [entry.metadata.access_count for entry in self._entries.values()]
        priorities = [entry.metadata.priority.value for entry in self._entries.values()]
        
        return {
            "total_entries": total_entries,
            "memory_type": self.memory_type.value,
            "agent_id": self.agent_id,
            "avg_access_count": sum(access_counts) / len(access_counts),
            "priority_distribution": {
                priority.name: sum(1 for p in priorities if p == priority.value)
                for priority in MemoryPriority
            },
            "oldest_entry": min(entry.metadata.created_at for entry in self._entries.values()).isoformat(),
            "newest_entry": max(entry.metadata.created_at for entry in self._entries.values()).isoformat()
        }
    
    async def cleanup_expired(self) -> int:
        """Remove expired memory entries"""
        now = datetime.now()
        expired_ids = [
            memory_id for memory_id, entry in self._entries.items()
            if entry.metadata.expires_at and entry.metadata.expires_at < now
        ]
        
        for memory_id in expired_ids:
            await self.delete(memory_id)
        
        return len(expired_ids)
    
    async def get_memories_by_priority(self, priority: MemoryPriority) -> List[MemoryEntry]:
        """Get all memories with a specific priority"""
        return [
            entry for entry in self._entries.values()
            if entry.metadata.priority == priority
        ]


class MemoryManager:
    """Central memory manager for coordinating memory across agents"""
    
    def __init__(self):
        self._memory_instances: Dict[str, BaseMemory] = {}
        self._shared_memories: Dict[str, MemoryEntry] = {}
        self._memory_pools: Dict[MemoryType, List[BaseMemory]] = {}
    
    def register_memory(self, memory_instance: BaseMemory):
        """Register a memory instance"""
        key = f"{memory_instance.agent_id}_{memory_instance.memory_type.value}"
        self._memory_instances[key] = memory_instance
        
        # Add to memory pools
        if memory_instance.memory_type not in self._memory_pools:
            self._memory_pools[memory_instance.memory_type] = []
        self._memory_pools[memory_instance.memory_type].append(memory_instance)
    
    async def store_shared_memory(self, content: Dict[str, Any], 
                                 tags: List[str] = None,
                                 priority: MemoryPriority = MemoryPriority.MEDIUM) -> str:
        """Store a memory that can be accessed by multiple agents"""
        memory_id = hashlib.md5(json.dumps(content, sort_keys=True, default=str).encode()).hexdigest()
        
        metadata = MemoryMetadata(
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            priority=priority,
            tags=tags or [],
            source_agent="shared"
        )
        
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=MemoryType.SHARED,
            metadata=metadata
        )
        
        self._shared_memories[memory_id] = entry
        return memory_id
    
    async def retrieve_shared_memory(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve shared memories"""
        # Simple text-based search for now
        results = []
        query_lower = query.lower()
        
        for entry in self._shared_memories.values():
            content_str = json.dumps(entry.content).lower()
            if query_lower in content_str or any(query_lower in tag.lower() for tag in entry.metadata.tags):
                results.append(entry)
        
        # Sort by priority and access count
        results.sort(key=lambda x: (x.metadata.priority.value, -x.metadata.access_count))
        return results[:limit]
    
    async def get_system_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        stats = {
            "total_memory_instances": len(self._memory_instances),
            "shared_memories": len(self._shared_memories),
            "memory_pools": {
                memory_type.value: len(pool) 
                for memory_type, pool in self._memory_pools.items()
            }
        }
        
        # Get stats from each memory instance
        instance_stats = {}
        for key, memory_instance in self._memory_instances.items():
            instance_stats[key] = await memory_instance.get_memory_stats()
        
        stats["instance_stats"] = instance_stats
        return stats
    
    async def cleanup_all_expired(self) -> Dict[str, int]:
        """Clean up expired memories across all instances"""
        cleanup_results = {}
        
        for key, memory_instance in self._memory_instances.items():
            cleaned = await memory_instance.cleanup_expired()
            cleanup_results[key] = cleaned
        
        # Clean up shared memories
        now = datetime.now()
        expired_shared = [
            memory_id for memory_id, entry in self._shared_memories.items()
            if entry.metadata.expires_at and entry.metadata.expires_at < now
        ]
        
        for memory_id in expired_shared:
            del self._shared_memories[memory_id]
        
        cleanup_results["shared"] = len(expired_shared)
        return cleanup_results


# Global memory manager instance
memory_manager = MemoryManager()
