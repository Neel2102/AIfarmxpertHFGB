-- ============================================================
-- FarmXpert — Cold Storage & Partition Lifecycle Management
-- ============================================================
-- Implements infinite chat retention via tiered storage:
--   HOT  = last 6 months on fast SSD (default tablespace)
--   COLD = older partitions on cheaper disk (cold_storage)
--
-- NO DATA IS EVER DELETED.
-- ============================================================

-- ──────────────────────────────────────────────────────────────
-- 1) Create cold storage tablespace
-- ──────────────────────────────────────────────────────────────
-- IMPORTANT: The directory must exist on the server and be
-- owned by the postgres OS user BEFORE running this.
--
-- On the Docker container:
--   mkdir -p /var/lib/postgresql/cold_data
--   chown postgres:postgres /var/lib/postgresql/cold_data

CREATE TABLESPACE cold_storage
    OWNER farmxpert
    LOCATION '/var/lib/postgresql/cold_data';

COMMENT ON TABLESPACE cold_storage IS
    'Cold tier for archived partitions (>6 months old). Cheaper disk, full query access preserved.';

-- ──────────────────────────────────────────────────────────────
-- 2) Migrate old partitions to cold storage
-- ──────────────────────────────────────────────────────────────
-- This procedure moves all partitions older than @months_ago
-- to the cold_storage tablespace and disables autovacuum
-- (since the data is frozen / append-only).
--
-- Run monthly via pg_cron or external scheduler.

CREATE OR REPLACE PROCEDURE migrate_partitions_to_cold(
    months_ago INTEGER DEFAULT 6
)
LANGUAGE plpgsql
AS $$
DECLARE
    cutoff_suffix   TEXT;
    rec             RECORD;
    partition_date  DATE;
    sql_stmt        TEXT;
BEGIN
    cutoff_suffix := to_char(NOW() - (months_ago || ' months')::INTERVAL, 'YYYY_MM');

    RAISE NOTICE 'Migrating partitions older than % to cold_storage...', cutoff_suffix;

    -- Find all child partitions across the 4 partitioned tables
    FOR rec IN
        SELECT
            c.relname AS partition_name,
            p.relname AS parent_name,
            ts.spcname AS current_tablespace
        FROM pg_inherits i
        JOIN pg_class c ON c.oid = i.inhrelid
        JOIN pg_class p ON p.oid = i.inhparent
        LEFT JOIN pg_tablespace ts ON ts.oid = c.reltablespace
        WHERE p.relname IN ('farm_sensor_data', 'messages', 'agent_executions', 'conversations')
        ORDER BY c.relname
    LOOP
        -- Extract YYYY_MM suffix from partition name
        -- Partition names follow: <parent>_YYYY_MM
        DECLARE
            name_suffix TEXT;
        BEGIN
            name_suffix := regexp_replace(rec.partition_name, '^.*_(\d{4}_\d{2})$', '\1');

            -- Skip if not a valid date suffix
            IF name_suffix !~ '^\d{4}_\d{2}$' THEN
                CONTINUE;
            END IF;

            -- Skip if partition is newer than cutoff
            IF name_suffix >= cutoff_suffix THEN
                CONTINUE;
            END IF;

            -- Skip if already on cold_storage
            IF rec.current_tablespace = 'cold_storage' THEN
                CONTINUE;
            END IF;

            -- Move to cold storage
            sql_stmt := format('ALTER TABLE %I SET TABLESPACE cold_storage', rec.partition_name);
            EXECUTE sql_stmt;

            -- Disable autovacuum on frozen partition
            sql_stmt := format('ALTER TABLE %I SET (autovacuum_enabled = false)', rec.partition_name);
            EXECUTE sql_stmt;

            RAISE NOTICE 'Migrated % to cold_storage', rec.partition_name;
        END;
    END LOOP;

    RAISE NOTICE 'Cold storage migration complete.';
END $$;

-- ──────────────────────────────────────────────────────────────
-- 3) Run the migration (default: partitions > 6 months old)
-- ──────────────────────────────────────────────────────────────
-- Uncomment to run immediately:
-- CALL migrate_partitions_to_cold(6);

-- ──────────────────────────────────────────────────────────────
-- 4) Scheduled execution (requires pg_cron extension)
-- ──────────────────────────────────────────────────────────────
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
--
-- SELECT cron.schedule(
--     'monthly_cold_migration',
--     '0 2 1 * *',                              -- 2 AM on the 1st of every month
--     $$CALL migrate_partitions_to_cold(6)$$
-- );

-- ──────────────────────────────────────────────────────────────
-- 5) Verify partition distribution
-- ──────────────────────────────────────────────────────────────
-- Check which partitions are hot vs cold:
--
--   SELECT
--       p.relname AS parent_table,
--       c.relname AS partition,
--       COALESCE(ts.spcname, 'pg_default') AS tablespace,
--       CASE
--          WHEN ts.spcname = 'cold_storage' THEN 'COLD'
--          ELSE 'HOT'
--       END AS tier,
--       pg_size_pretty(pg_relation_size(c.oid)) AS size
--   FROM pg_inherits i
--   JOIN pg_class c ON c.oid = i.inhrelid
--   JOIN pg_class p ON p.oid = i.inhparent
--   LEFT JOIN pg_tablespace ts ON ts.oid = c.reltablespace
--   WHERE p.relname IN ('farm_sensor_data', 'messages', 'agent_executions', 'conversations')
--   ORDER BY p.relname, c.relname;

-- ──────────────────────────────────────────────────────────────
-- 6) Future partition auto-creation
-- ──────────────────────────────────────────────────────────────
-- To automatically create next month's partitions:
--
-- CREATE OR REPLACE PROCEDURE create_next_month_partitions()
-- LANGUAGE plpgsql AS $$
-- DECLARE
--     next_start DATE := date_trunc('month', NOW() + INTERVAL '1 month');
--     next_end   DATE := next_start + INTERVAL '1 month';
--     suffix     TEXT := to_char(next_start, 'YYYY_MM');
-- BEGIN
--     EXECUTE format('CREATE TABLE IF NOT EXISTS farm_sensor_data_%s PARTITION OF farm_sensor_data FOR VALUES FROM (%L) TO (%L)', suffix, next_start, next_end);
--     EXECUTE format('CREATE TABLE IF NOT EXISTS messages_%s PARTITION OF messages FOR VALUES FROM (%L) TO (%L)', suffix, next_start, next_end);
--     EXECUTE format('CREATE TABLE IF NOT EXISTS agent_executions_%s PARTITION OF agent_executions FOR VALUES FROM (%L) TO (%L)', suffix, next_start, next_end);
--     EXECUTE format('CREATE TABLE IF NOT EXISTS conversations_%s PARTITION OF conversations FOR VALUES FROM (%L) TO (%L)', suffix, next_start, next_end);
--     RAISE NOTICE 'Created partitions for %', suffix;
-- END $$;
--
-- Schedule with pg_cron:
-- SELECT cron.schedule('monthly_partition_creation', '0 0 25 * *',
--     $$CALL create_next_month_partitions()$$);
-- ============================================================
