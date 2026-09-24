"""
Schema Guard — idempotent, data-preserving reconciliation of the physical
PostgreSQL schema with the SQLAlchemy models.

Why this exists
---------------
The `farms` table was originally created by migration 001 with a legacy shape
(`name NOT NULL`, `location NOT NULL`, `size_acres NOT NULL`, `farmer_name
NOT NULL`, and no `user_id`). The ORM model was later changed to the canonical
shape (`farm_name`, plus `user_id`, `crop_type`, `state`, `district`,
`village`, `latitude`, `longitude`, `soil_type`).

`Base.metadata.create_all()` only creates *missing tables* — it never alters an
existing one. So on any deployment whose database predates the model change,
every INSERT/SELECT against `farms` raises one of

    psycopg2.errors.UndefinedColumn:  column "farm_name" does not exist
    psycopg2.errors.UndefinedColumn:  column farms.name does not exist
    psycopg2.errors.NotNullViolation: null value in column "name"

which surfaces as HTTP 500 on /api/auth/farm-profile and
/api/tasks/farms-and-crops.

This module runs at startup, inspects the *actual* columns, and converges the
table to the canonical shape without destroying data:
  * adds any missing canonical column,
  * copies legacy `name` -> `farm_name` where farm_name is still empty,
  * relaxes legacy NOT NULL constraints the ORM no longer populates, after
    backfilling so no existing row is left invalid.

Every statement is guarded by an existence check, so running it repeatedly is a
no-op. It never drops a column and never deletes a row.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# column name -> DDL type used when the column has to be added
FARM_CANONICAL_COLUMNS: Dict[str, str] = {
    "user_id": "BIGINT",
    "farm_name": "VARCHAR(255)",
    "location": "VARCHAR(255)",
    "size_acres": "DOUBLE PRECISION",
    "farmer_name": "VARCHAR(255)",
    "farmer_phone": "VARCHAR(50)",
    "farmer_email": "VARCHAR(255)",
    "crop_type": "VARCHAR(100)",
    "state": "VARCHAR(100)",
    "district": "VARCHAR(100)",
    "village": "VARCHAR(100)",
    "latitude": "NUMERIC(10,7)",
    "longitude": "NUMERIC(10,7)",
    "soil_type": "VARCHAR(100)",
    "created_at": "TIMESTAMP",
    "updated_at": "TIMESTAMP",
}

# Legacy columns the ORM no longer writes. If they still exist and are NOT NULL,
# every ORM insert fails. Relax them (and backfill) instead of dropping them, so
# nothing that still reads the old shape breaks.
FARM_LEGACY_NULLABLE: Dict[str, str] = {
    "name": "'My Farm'",
    "location": "'Unknown'",
    "size_acres": "0",
    "farmer_name": "'Farmer'",
}

FARM_PROFILE_CANONICAL_COLUMNS: Dict[str, str] = {
    "farm_name": "VARCHAR(255)",
    "farm_size": "VARCHAR(100)",
    "farm_size_unit": "VARCHAR(20)",
    "location": "VARCHAR(255)",
    "state": "VARCHAR(100)",
    "district": "VARCHAR(100)",
    "village": "VARCHAR(100)",
    "latitude": "DOUBLE PRECISION",
    "longitude": "DOUBLE PRECISION",
    "soil_type": "VARCHAR(100)",
    "irrigation_method": "VARCHAR(100)",
    "specific_crop": "VARCHAR(255)",
    "farm_polygon": "JSON",
    "farm_layout_data": "JSON",
}


def _columns(conn, table: str) -> Set[str]:
    insp = inspect(conn)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def _not_null_columns(conn, table: str) -> Set[str]:
    insp = inspect(conn)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table) if not c.get("nullable", True)}


def _primary_keys(conn, table: str) -> Set[str]:
    insp = inspect(conn)
    if table not in insp.get_table_names():
        return set()
    return set(insp.get_pk_constraint(table).get("constrained_columns") or [])


def _add_missing_columns(conn, table: str, spec: Dict[str, str]) -> List[str]:
    existing = _columns(conn, table)
    if not existing:
        return []
    applied = []
    for col, ddl_type in spec.items():
        if col in existing:
            continue
        conn.execute(text('ALTER TABLE ' + table + ' ADD COLUMN IF NOT EXISTS "' + col + '" ' + ddl_type))
        applied.append(table + "." + col + " added (" + ddl_type + ")")
    return applied


def _reconcile_farms(conn) -> List[str]:
    existing = _columns(conn, "farms")
    if not existing:
        # Table does not exist yet; create_all() will build the canonical shape.
        return []

    applied = _add_missing_columns(conn, "farms", FARM_CANONICAL_COLUMNS)
    existing = _columns(conn, "farms")

    # Migrate legacy `name` values into `farm_name` where farm_name is still empty.
    if "name" in existing and "farm_name" in existing:
        result = conn.execute(
            text("UPDATE farms SET farm_name = name WHERE farm_name IS NULL AND name IS NOT NULL")
        )
        if result.rowcount:
            applied.append("farms.farm_name backfilled from legacy farms.name (%d rows)" % result.rowcount)

    if "farm_name" in existing:
        result = conn.execute(text("UPDATE farms SET farm_name = 'My Farm' WHERE farm_name IS NULL"))
        if result.rowcount:
            applied.append("farms.farm_name defaulted for %d rows" % result.rowcount)

    # Relax legacy NOT NULL constraints the ORM no longer populates, after
    # backfilling so no existing row is left invalid.
    not_null = _not_null_columns(conn, "farms")
    pks = _primary_keys(conn, "farms")
    for col, default_sql in FARM_LEGACY_NULLABLE.items():
        if col not in existing or col in pks or col not in not_null:
            continue
        conn.execute(text('UPDATE farms SET "' + col + '" = ' + default_sql + ' WHERE "' + col + '" IS NULL'))
        conn.execute(text('ALTER TABLE farms ALTER COLUMN "' + col + '" DROP NOT NULL'))
        applied.append("farms." + col + " NOT NULL relaxed (legacy column no longer written by the ORM)")

    # user_id must be indexed — every tenant-scoped query filters on it.
    if "user_id" in _columns(conn, "farms"):
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_farms_user_id ON farms (user_id)"))

    return applied


def _reconcile_sensor_readings(conn) -> List[str]:
    """
    Give sensor_readings.id a sequence default.

    The column is part of a composite primary key (id, recorded_at) for time
    partitioning. Neither SQLAlchemy nor CREATE TABLE gives such a column an
    identity generator automatically, so every INSERT sent id=NULL and was
    rejected — no telemetry could ever be stored.
    """
    existing = _columns(conn, "sensor_readings")
    if "id" not in existing:
        return []

    row = conn.execute(text(
        "SELECT column_default FROM information_schema.columns "
        "WHERE table_name = 'sensor_readings' AND column_name = 'id'"
    )).fetchone()
    if row and row[0]:
        return []

    conn.execute(text("CREATE SEQUENCE IF NOT EXISTS sensor_readings_id_seq"))
    conn.execute(text(
        "SELECT setval('sensor_readings_id_seq', "
        "GREATEST((SELECT COALESCE(MAX(id), 0) FROM sensor_readings), 1))"
    ))
    conn.execute(text(
        "ALTER TABLE sensor_readings "
        "ALTER COLUMN id SET DEFAULT nextval('sensor_readings_id_seq')"
    ))
    conn.execute(text("ALTER SEQUENCE sensor_readings_id_seq OWNED BY sensor_readings.id"))
    return ["sensor_readings.id given a sequence default (INSERTs were failing on a NULL id)"]


def reconcile_schema(engine: Engine) -> List[str]:
    """
    Bring the physical schema in line with the models. Returns the list of
    changes actually applied (empty when the schema was already correct).
    Safe to call on every startup.
    """
    if engine.dialect.name != "postgresql":
        # SQLite test databases are always created fresh from the models.
        return []

    applied: List[str] = []
    with engine.begin() as conn:
        applied.extend(_reconcile_farms(conn))
        applied.extend(_add_missing_columns(conn, "farm_profiles", FARM_PROFILE_CANONICAL_COLUMNS))
        applied.extend(_reconcile_sensor_readings(conn))

    for change in applied:
        logger.warning("Schema guard applied: %s", change)
    if not applied:
        logger.info("Schema guard: physical schema already matches the models.")
    return applied
