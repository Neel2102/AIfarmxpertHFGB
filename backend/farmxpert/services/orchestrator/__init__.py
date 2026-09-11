"""
FarmXpert Multi-Agent Orchestration Package.
Provides authenticated farm context resolution, deterministic intent routing,
central tool registry, and scope-enforced response generation.
"""

from .farm_context import (
    FarmContext,
    FarmResolutionResult,
    FarmResolutionStatus,
    FarmContextResolver,
)
# Provide a default instance for older imports that expect `farm_context_resolver`
farm_context_resolver = FarmContextResolver()

# Intent router exposes IntentType (enum), RoutedIntent (routing result), and the singleton intent_router
from .intent_router import IntentType, RoutedIntent, intent_router
from .tool_registry import ToolCategory, ToolDefinition, ToolRegistry, tool_registry
from .farmxpert_orchestrator import FarmXpertOrchestrator, farmxpert_orchestrator

__all__ = [
    "FarmContext",
    "FarmResolutionResult",
    "FarmResolutionStatus",
    "farm_context_resolver",
    "IntentType",
    "RoutedIntent",
    "intent_router",
    "ToolCategory",
    "ToolDefinition",
    "ToolRegistry",
    "tool_registry",
    "FarmXpertOrchestrator",
    "farmxpert_orchestrator",
]
