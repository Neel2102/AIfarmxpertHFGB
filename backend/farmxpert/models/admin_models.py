from __future__ import annotations

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from farmxpert.models.database import Base


class AdminAuditEvent(Base):
    __tablename__ = "admin_audit_events"

    id = Column(BigInteger, primary_key=True, index=True)
    actor_user_id = Column(Integer, nullable=False, index=True)

    action_type = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)
    target_id = Column(String(128), nullable=False, index=True)

    reason = Column(Text, nullable=True)
    before_json = Column(JSONB, nullable=True)
    after_json = Column(JSONB, nullable=True)

    request_id = Column(String(128), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LLMUsageEvent(Base):
    __tablename__ = "llm_usage_events"

    id = Column(BigInteger, primary_key=True, index=True)
    ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    provider = Column(String(50), nullable=True, index=True)
    model = Column(String(100), nullable=True, index=True)

    user_id = Column(Integer, nullable=True, index=True)
    farm_id = Column(BigInteger, nullable=True, index=True)

    agent_name = Column(String(100), nullable=True, index=True)
    session_id = Column(String(128), nullable=True, index=True)

    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    cost_usd = Column(Numeric(12, 6), nullable=True)
    latency_ms = Column(Integer, nullable=True)

    status = Column(String(20), nullable=True, index=True)
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    request_id = Column(String(128), nullable=True, index=True)
    trace_id = Column(String(128), nullable=True, index=True)


class SensorOverride(Base):
    __tablename__ = "sensor_overrides"

    id = Column(BigInteger, primary_key=True, index=True)

    farm_id = Column(BigInteger, nullable=False, index=True)
    device_id = Column(BigInteger, nullable=True, index=True)

    metric = Column(String(50), nullable=False, index=True)
    value = Column(Numeric(14, 6), nullable=False)

    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)

    reason = Column(Text, nullable=True)
    created_by_admin_id = Column(Integer, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
