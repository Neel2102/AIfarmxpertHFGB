-- ============================================================
-- FarmXpert — Monthly Partition Generator (Enterprise Edition)
-- ============================================================
-- Creates monthly RANGE partitions for:
--   1. farm_sensor_data  (partitioned on recorded_at)
--   2. messages           (partitioned on created_at)
--   3. agent_executions   (partitioned on created_at)
--   4. conversations      (partitioned on started_at)  ← NEW
--
-- Default range: January 2025 → December 2027 (36 months)
-- Safe to re-run: partitions are created only IF NOT EXISTS.
-- ============================================================

-- ──────────────────────────────────────────────────────────────
-- STEP 1: Create monthly partitions for all partitioned tables
-- ──────────────────────────────────────────────────────────────

DO $$
DECLARE
    start_date  DATE := '2025-01-01';
    end_date    DATE := '2028-01-01';   -- exclusive upper bound
    curr        DATE;
    next_month  DATE;
    suffix      TEXT;
    sql_stmt    TEXT;
BEGIN
    curr := start_date;

    WHILE curr < end_date LOOP
        next_month := curr + INTERVAL '1 month';
        suffix := to_char(curr, 'YYYY_MM');     -- e.g. 2025_01

        -- ── farm_sensor_data partition ──
        sql_stmt := format(
            'CREATE TABLE IF NOT EXISTS farm_sensor_data_%s PARTITION OF farm_sensor_data
                FOR VALUES FROM (%L) TO (%L)',
            suffix, curr, next_month
        );
        EXECUTE sql_stmt;

        -- ── messages partition ──
        sql_stmt := format(
            'CREATE TABLE IF NOT EXISTS messages_%s PARTITION OF messages
                FOR VALUES FROM (%L) TO (%L)',
            suffix, curr, next_month
        );
        EXECUTE sql_stmt;

        -- ── agent_executions partition ──
        sql_stmt := format(
            'CREATE TABLE IF NOT EXISTS agent_executions_%s PARTITION OF agent_executions
                FOR VALUES FROM (%L) TO (%L)',
            suffix, curr, next_month
        );
        EXECUTE sql_stmt;

        -- ── conversations partition ──
        sql_stmt := format(
            'CREATE TABLE IF NOT EXISTS conversations_%s PARTITION OF conversations
                FOR VALUES FROM (%L) TO (%L)',
            suffix, curr, next_month
        );
        EXECUTE sql_stmt;

        RAISE NOTICE 'Created partitions for %', suffix;

        curr := next_month;
    END LOOP;

    RAISE NOTICE 'All partitions created successfully (4 tables × 36 months = 144 partitions).';
END $$;

-- ============================================================
-- STEP 2: Mark old partitions as READ ONLY (cold tier)
-- ============================================================
-- Run this periodically (e.g. monthly cron) to freeze partitions
-- that are older than 6 months. Read-only partitions have lower
-- WAL overhead and can be moved to cold storage.
--
-- Example (manual):
--   ALTER TABLE messages_2025_01 SET (autovacuum_enabled = false);
--   ALTER TABLE messages_2025_01 SET TABLESPACE cold_storage;
--
-- See cold_storage_management.sql for automated scripts.
-- ============================================================

-- ============================================================
-- Verify partitions
-- ============================================================
-- Run these queries to verify partitions were created:
--
--   SELECT inhrelid::regclass AS partition_name
--   FROM pg_inherits
--   WHERE inhparent = 'farm_sensor_data'::regclass
--   ORDER BY inhrelid::regclass::text;
--
--   SELECT inhrelid::regclass AS partition_name
--   FROM pg_inherits
--   WHERE inhparent = 'messages'::regclass
--   ORDER BY inhrelid::regclass::text;
--
--   SELECT inhrelid::regclass AS partition_name
--   FROM pg_inherits
--   WHERE inhparent = 'agent_executions'::regclass
--   ORDER BY inhrelid::regclass::text;
--
--   SELECT inhrelid::regclass AS partition_name
--   FROM pg_inherits
--   WHERE inhparent = 'conversations'::regclass
--   ORDER BY inhrelid::regclass::text;
-- ============================================================
