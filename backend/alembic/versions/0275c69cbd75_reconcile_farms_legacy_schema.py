"""Reconcile the legacy farms schema with the canonical model shape

Databases created by migration 001 have `farms.name NOT NULL`,
`farms.location NOT NULL`, `farms.size_acres NOT NULL`,
`farms.farmer_name NOT NULL` and no `farms.user_id`.

The ORM writes `farm_name` / `user_id` and never writes `name`, so every farm
INSERT fails with NotNullViolation and every farm SELECT that touches a newer
column fails with UndefinedColumn. That is the HTTP 500 on
/api/auth/farm-profile and /api/tasks/farms-and-crops.

This migration converges the table without dropping columns or rows. It shares
its implementation with farmxpert.services.schema_guard, which performs the
same reconciliation at application startup so that deployments which never run
alembic still converge.

Revision ID: 0275c69cbd75
Revises: 0275c69cbd74
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

from farmxpert.services.schema_guard import _add_missing_columns, _reconcile_farms, FARM_PROFILE_CANONICAL_COLUMNS

# revision identifiers, used by Alembic.
revision: str = '0275c69cbd75'
down_revision: Union[str, None] = '0275c69cbd74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    for change in _reconcile_farms(conn):
        print("farms:", change)
    for change in _add_missing_columns(conn, "farm_profiles", FARM_PROFILE_CANONICAL_COLUMNS):
        print("farm_profiles:", change)


def downgrade() -> None:
    # Purely additive / constraint-relaxing. Reversing it would re-break the
    # application and could fail on rows the ORM has since written, so this
    # migration is intentionally not reversible.
    pass
