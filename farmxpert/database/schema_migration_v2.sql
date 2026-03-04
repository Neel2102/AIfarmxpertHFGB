-- ============================================================
-- FarmXpert — Schema Migration V2
-- Chat History Enhancements + Blynk Sensor Data Storage
-- ============================================================
-- Run AFTER schema.sql and create_partitions.sql
-- Safe to re-run: uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS
-- ============================================================

-- ============================================================
-- A) CUSTOM ENUM TYPES
-- ============================================================

DO $$ BEGIN
    CREATE TYPE session_type_enum AS ENUM ('chat', 'voice');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE conversation_status_enum AS ENUM ('active', 'closed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE sender_type_enum AS ENUM ('user', 'agent', 'system');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE message_type_enum AS ENUM ('text', 'image', 'voice_transcript', 'api_response');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE device_status_enum AS ENUM ('active', 'offline', 'invalid_token');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- B) UPGRADE conversations TABLE
-- ============================================================

ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS session_type  session_type_enum DEFAULT 'chat',
    ADD COLUMN IF NOT EXISTS status        conversation_status_enum DEFAULT 'active';

-- ============================================================
-- C) UPGRADE messages TABLE
-- ============================================================

ALTER TABLE messages
    ADD COLUMN IF NOT EXISTS user_id       BIGINT,
    ADD COLUMN IF NOT EXISTS sender_type   sender_type_enum DEFAULT 'user',
    ADD COLUMN IF NOT EXISTS message_type  message_type_enum DEFAULT 'text',
    ADD COLUMN IF NOT EXISTS token_count   INTEGER;

CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages (user_id);

-- ============================================================
-- D) blynk_devices TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS blynk_devices (
    id              BIGSERIAL       PRIMARY KEY,
    farm_id         BIGINT          REFERENCES farms(id) ON DELETE SET NULL,
    device_name     VARCHAR(255)    DEFAULT 'My Blynk Device',
    blynk_device_id VARCHAR(100)    UNIQUE,
    auth_token      TEXT            NOT NULL,       -- stored encrypted
    is_active       BOOLEAN         DEFAULT TRUE,
    status          device_status_enum DEFAULT 'active',
    last_seen_at    TIMESTAMPTZ,
    last_error      TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blynk_devices_farm_id ON blynk_devices (farm_id);
CREATE INDEX IF NOT EXISTS idx_blynk_devices_device_id ON blynk_devices (blynk_device_id);

-- ============================================================
-- E) sensor_readings TABLE (Partitioned — High Volume)
-- ============================================================
-- 9 Blynk parameters + raw JSONB payload
-- Partitioned by RANGE on recorded_at (monthly)

CREATE TABLE IF NOT EXISTS sensor_readings (
    id                  BIGSERIAL,
    device_id           BIGINT          NOT NULL,
    farm_id             BIGINT          NOT NULL,

    -- 9 Blynk sensor parameters
    air_temperature     NUMERIC(7, 2),
    air_humidity        NUMERIC(7, 2),
    soil_moisture       NUMERIC(7, 2),
    soil_temperature    NUMERIC(7, 2),
    soil_ec             NUMERIC(7, 2),
    soil_ph             NUMERIC(5, 2),
    nitrogen            NUMERIC(7, 2),
    phosphorus          NUMERIC(7, 2),
    potassium           NUMERIC(7, 2),

    -- Metadata
    raw_payload         JSONB,
    recorded_at         TIMESTAMPTZ     NOT NULL,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),

    PRIMARY KEY (id, recorded_at)
) PARTITION BY RANGE (recorded_at);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_device_id   ON sensor_readings (device_id);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_farm_id     ON sensor_readings (farm_id);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_recorded_at ON sensor_readings (recorded_at);

-- ============================================================
-- F) sensor_daily_summary TABLE (Analytics Pre-Aggregation)
-- ============================================================

CREATE TABLE IF NOT EXISTS sensor_daily_summary (
    id                  BIGSERIAL       PRIMARY KEY,
    farm_id             BIGINT          NOT NULL REFERENCES farms(id),
    device_id           BIGINT,
    summary_date        DATE            NOT NULL,

    -- Averages
    avg_air_temperature NUMERIC(7, 2),
    avg_air_humidity    NUMERIC(7, 2),
    avg_soil_moisture   NUMERIC(7, 2),
    avg_soil_temperature NUMERIC(7, 2),
    avg_soil_ec         NUMERIC(7, 2),
    avg_soil_ph         NUMERIC(5, 2),
    avg_nitrogen        NUMERIC(7, 2),
    avg_phosphorus      NUMERIC(7, 2),
    avg_potassium       NUMERIC(7, 2),

    -- Min / Max
    min_air_temperature NUMERIC(7, 2),
    max_air_temperature NUMERIC(7, 2),
    min_soil_moisture   NUMERIC(7, 2),
    max_soil_moisture   NUMERIC(7, 2),

    reading_count       INTEGER         DEFAULT 0,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),

    UNIQUE (farm_id, device_id, summary_date)
);

CREATE INDEX IF NOT EXISTS idx_sensor_daily_summary_farm_date
    ON sensor_daily_summary (farm_id, summary_date);

-- ============================================================
-- G) Create monthly partitions for sensor_readings
-- ============================================================

DO $$
DECLARE
    start_date  DATE := '2025-01-01';
    end_date    DATE := '2028-01-01';
    curr        DATE;
    next_month  DATE;
    suffix      TEXT;
    sql_stmt    TEXT;
BEGIN
    curr := start_date;
    WHILE curr < end_date LOOP
        next_month := curr + INTERVAL '1 month';
        suffix := to_char(curr, 'YYYY_MM');

        sql_stmt := format(
            'CREATE TABLE IF NOT EXISTS sensor_readings_%s PARTITION OF sensor_readings
                FOR VALUES FROM (%L) TO (%L)',
            suffix, curr, next_month
        );
        EXECUTE sql_stmt;

        curr := next_month;
    END LOOP;

    RAISE NOTICE 'sensor_readings partitions created (36 months).';
END $$;

-- ============================================================
-- END OF MIGRATION V2
-- ============================================================
