"""Consolidate schema (models as source of truth)

Revision ID: 004
Revises: 003
Create Date: 2026-03-10

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def _drop_all_tables_except_alembic_version() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = inspector.get_table_names(schema="public")
    tables = [t for t in tables if t != "alembic_version"]

    # Drop in reverse dependency order (CASCADE handles FKs).
    for table_name in tables:
        op.execute(sa.text(f'DROP TABLE IF EXISTS public."{table_name}" CASCADE'))


def upgrade() -> None:
    # Destructive consolidation: drop all existing tables, then recreate from current models.
    _drop_all_tables_except_alembic_version()

    # Import models so Base.metadata is fully populated.
    from farmxpert.models.database import Base  # noqa: WPS433
    import farmxpert.models.user_models  # noqa: F401, WPS433
    import farmxpert.models.farm_models  # noqa: F401, WPS433
    import farmxpert.models.admin_models  # noqa: F401, WPS433
    import farmxpert.models.blynk_models  # noqa: F401, WPS433
    import farmxpert.models.farm_profile_models  # noqa: F401, WPS433

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    # Best-effort destructive downgrade: drop everything except alembic_version.
    _drop_all_tables_except_alembic_version()
