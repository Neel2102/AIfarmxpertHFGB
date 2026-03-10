"""Admin foundations and user role

Revision ID: 003
Revises: 002
Create Date: 2026-03-09

"""

from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("suspended_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("suspended_until", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("suspend_reason", sa.Text(), nullable=True))
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "admin_audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("before_json", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_json", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_admin_audit_events_actor_user_id", "admin_audit_events", ["actor_user_id"], unique=False)
    op.create_index("ix_admin_audit_events_action_type", "admin_audit_events", ["action_type"], unique=False)
    op.create_index("ix_admin_audit_events_target_type", "admin_audit_events", ["target_type"], unique=False)
    op.create_index("ix_admin_audit_events_target_id", "admin_audit_events", ["target_id"], unique=False)
    op.create_index("ix_admin_audit_events_request_id", "admin_audit_events", ["request_id"], unique=False)

    op.create_table(
        "llm_usage_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("farm_id", sa.BigInteger(), nullable=True),
        sa.Column("agent_name", sa.String(length=100), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("error_type", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
    )
    op.create_index("ix_llm_usage_events_ts", "llm_usage_events", ["ts"], unique=False)
    op.create_index("ix_llm_usage_events_provider", "llm_usage_events", ["provider"], unique=False)
    op.create_index("ix_llm_usage_events_model", "llm_usage_events", ["model"], unique=False)
    op.create_index("ix_llm_usage_events_user_id", "llm_usage_events", ["user_id"], unique=False)
    op.create_index("ix_llm_usage_events_farm_id", "llm_usage_events", ["farm_id"], unique=False)
    op.create_index("ix_llm_usage_events_agent_name", "llm_usage_events", ["agent_name"], unique=False)
    op.create_index("ix_llm_usage_events_session_id", "llm_usage_events", ["session_id"], unique=False)
    op.create_index("ix_llm_usage_events_status", "llm_usage_events", ["status"], unique=False)
    op.create_index("ix_llm_usage_events_request_id", "llm_usage_events", ["request_id"], unique=False)
    op.create_index("ix_llm_usage_events_trace_id", "llm_usage_events", ["trace_id"], unique=False)

    op.create_table(
        "sensor_overrides",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("farm_id", sa.BigInteger(), nullable=False),
        sa.Column("device_id", sa.BigInteger(), nullable=True),
        sa.Column("metric", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Numeric(14, 6), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by_admin_id", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_sensor_overrides_farm_id", "sensor_overrides", ["farm_id"], unique=False)
    op.create_index("ix_sensor_overrides_device_id", "sensor_overrides", ["device_id"], unique=False)
    op.create_index("ix_sensor_overrides_metric", "sensor_overrides", ["metric"], unique=False)
    op.create_index("ix_sensor_overrides_created_by_admin_id", "sensor_overrides", ["created_by_admin_id"], unique=False)
    op.create_index("ix_sensor_overrides_deleted_at", "sensor_overrides", ["deleted_at"], unique=False)

    op.execute("UPDATE users SET role = 'farmer' WHERE role IS NULL")


def downgrade() -> None:
    op.drop_index("ix_sensor_overrides_deleted_at", table_name="sensor_overrides")
    op.drop_index("ix_sensor_overrides_created_by_admin_id", table_name="sensor_overrides")
    op.drop_index("ix_sensor_overrides_metric", table_name="sensor_overrides")
    op.drop_index("ix_sensor_overrides_device_id", table_name="sensor_overrides")
    op.drop_index("ix_sensor_overrides_farm_id", table_name="sensor_overrides")
    op.drop_table("sensor_overrides")

    op.drop_index("ix_llm_usage_events_trace_id", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_request_id", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_status", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_session_id", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_agent_name", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_farm_id", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_user_id", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_model", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_provider", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_ts", table_name="llm_usage_events")
    op.drop_table("llm_usage_events")

    op.drop_index("ix_admin_audit_events_request_id", table_name="admin_audit_events")
    op.drop_index("ix_admin_audit_events_target_id", table_name="admin_audit_events")
    op.drop_index("ix_admin_audit_events_target_type", table_name="admin_audit_events")
    op.drop_index("ix_admin_audit_events_action_type", table_name="admin_audit_events")
    op.drop_index("ix_admin_audit_events_actor_user_id", table_name="admin_audit_events")
    op.drop_table("admin_audit_events")

    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_column("users", "suspend_reason")
    op.drop_column("users", "suspended_until")
    op.drop_column("users", "suspended_at")
    op.drop_column("users", "role")
