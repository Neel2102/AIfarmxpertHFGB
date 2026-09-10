"""
Standardized Output Schema for FarmXpert Agents
Defines standardized data classes and helper methods for agent outputs.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


def calculate_confidence_level(confidence: float) -> str:
    """Classify numeric confidence into low, medium, high."""
    if confidence >= 0.8:
        return "high"
    elif confidence >= 0.5:
        return "medium"
    return "low"


@dataclass
class AgentDecision:
    action: Optional[str] = None
    summary: Optional[str] = None
    details: Optional[str] = None
    confidence: float = 0.5
    confidence_level: str = "medium"
    reasoning: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructuredRecommendation:
    category: Optional[str] = None
    action: Optional[str] = None
    priority: str = "medium"
    timing: Optional[str] = None
    details: Optional[str] = None
    impact: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructuredWarning:
    issue: Optional[str] = None
    severity: str = "medium"
    impact: Optional[str] = None
    mitigation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StandardizedAgentOutput:
    agent: str
    success: bool = True
    decision: Optional[Union[AgentDecision, Dict[str, Any]]] = None
    recommendations: List[Any] = field(default_factory=list)
    warnings: List[Any] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "agent": self.agent,
            "success": self.success,
            "decision": self.decision.to_dict() if hasattr(self.decision, "to_dict") else self.decision,
            "recommendations": [
                r.to_dict() if hasattr(r, "to_dict") else r for r in self.recommendations
            ],
            "warnings": [
                w.to_dict() if hasattr(w, "to_dict") else w for w in self.warnings
            ],
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }
        return result


def create_agent_decision(
    summary: str = "",
    details: str = "",
    confidence: float = 0.5,
    action: Optional[str] = None,
    reasoning: Optional[List[str]] = None,
    alternatives: Optional[List[Dict[str, Any]]] = None,
) -> AgentDecision:
    return AgentDecision(
        action=action,
        summary=summary,
        details=details,
        confidence=confidence,
        confidence_level=calculate_confidence_level(confidence),
        reasoning=reasoning or [],
        alternatives=alternatives or [],
    )


def create_structured_recommendation(
    category: str = "",
    action: str = "",
    priority: str = "medium",
    timing: str = "",
    details: str = "",
    impact: str = "",
) -> StructuredRecommendation:
    return StructuredRecommendation(
        category=category,
        action=action,
        priority=priority,
        timing=timing,
        details=details,
        impact=impact,
    )


def create_structured_warning(
    issue: str = "",
    severity: str = "medium",
    impact: str = "",
    mitigation: str = "",
) -> StructuredWarning:
    return StructuredWarning(
        issue=issue,
        severity=severity,
        impact=impact,
        mitigation=mitigation,
    )


def format_legacy_response(
    agent_name: str,
    success: bool = True,
    response_text: str = "",
    confidence: float = 0.5,
    recommendations: Optional[List[Any]] = None,
    warnings: Optional[List[Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> StandardizedAgentOutput:
    decision = create_agent_decision(
        summary=response_text[:200] if response_text else "",
        details=response_text,
        confidence=confidence,
    )
    return StandardizedAgentOutput(
        agent=agent_name,
        success=success,
        decision=decision,
        recommendations=recommendations or [],
        warnings=warnings or [],
        data=data or {},
        metadata=metadata or {},
    )
