-- ============================================================
-- FarmXpert AI Agriculture Intelligence Platform
-- Production PostgreSQL Database Schema — Enterprise Edition
-- ============================================================
-- PostgreSQL 16+ with pgvector extension required
-- Optimized for HIGH-WRITE workloads
-- BIGSERIAL primary keys for horizontal scaling
-- RANGE partitioning on time-series tables
-- Multi-tenant RLS ready (see row_level_security.sql)
-- Infinite chat retention — NO DELETION POLICY
-- ============================================================

-- ============================================================
-- EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;          -- pgvector for semantic memory
CREATE EXTENSION IF NOT EXISTS pg_trgm;         -- trigram indexing (future text search)

-- ============================================================
-- 1) AUTHENTICATION
-- ============================================================

CREATE TABLE auth_users (
    id              BIGSERIAL       PRIMARY KEY,
    farmer_id       VARCHAR(50)     UNIQUE NOT NULL,
    email           VARCHAR(255)    UNIQUE NOT NULL,
    username        VARCHAR(50)     UNIQUE NOT NULL,
    name            VARCHAR(100),
    phone           VARCHAR(20)     UNIQUE,
    password_hash   TEXT            NOT NULL,
    role            VARCHAR(20)     DEFAULT 'farmer',
    created_at      TIMESTAMP       DEFAULT NOW(),
    updated_at      TIMESTAMP
);

CREATE INDEX idx_auth_users_email       ON auth_users (email);
CREATE INDEX idx_auth_users_username    ON auth_users (username);
CREATE INDEX idx_auth_users_farmer_id   ON auth_users (farmer_id);

-- ============================================================
-- 2) FARM MANAGEMENT
-- ============================================================

CREATE TABLE farms (
    id              BIGSERIAL       PRIMARY KEY,
    user_id         BIGINT          NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    farm_name       VARCHAR(255),
    crop_type       VARCHAR(100),
    state           VARCHAR(100),
    district        VARCHAR(100),
    village         VARCHAR(100),
    latitude        DECIMAL(10, 7),
    longitude       DECIMAL(10, 7),
    soil_type       VARCHAR(100),
    created_at      TIMESTAMP       DEFAULT NOW(),
    updated_at      TIMESTAMP
);

CREATE INDEX idx_farms_user_id ON farms (user_id);

-- ============================================================
-- 3) SENSOR DEVICE MANAGEMENT
-- ============================================================

CREATE TABLE sensors (
    id              BIGSERIAL       PRIMARY KEY,
    farm_id         BIGINT          NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    device_name     VARCHAR(255),
    blynk_device_id VARCHAR(100),
    api_key         VARCHAR(255),
    status          VARCHAR(20)     DEFAULT 'active',
    installed_at    TIMESTAMP
);

CREATE INDEX idx_sensors_farm_id ON sensors (farm_id);

-- ============================================================
-- 4) SENSOR DATA — HIGH-SCALE TIME SERIES (PARTITIONED)
-- ============================================================
-- Partitioned by RANGE on recorded_at (monthly partitions).
-- Child partitions must be created separately — see create_partitions.sql

CREATE TABLE farm_sensor_data (
    id              BIGSERIAL,
    sensor_id       BIGINT          NOT NULL,
    temperature     NUMERIC(7, 2),
    humidity        NUMERIC(7, 2),
    soil_moisture   NUMERIC(7, 2),
    ph              NUMERIC(5, 2),
    nitrogen        NUMERIC(7, 2),
    phosphorus      NUMERIC(7, 2),
    potassium       NUMERIC(7, 2),
    light_intensity NUMERIC(10, 2),
    rainfall        NUMERIC(7, 2),
    recorded_at     TIMESTAMP       NOT NULL,

    PRIMARY KEY (id, recorded_at)
) PARTITION BY RANGE (recorded_at);

-- NOTE: Foreign key constraints are NOT supported on partitioned tables
-- in PostgreSQL < 17. Enforce sensor_id integrity at the application layer
-- or via triggers if needed.

CREATE INDEX idx_sensor_data_sensor_id   ON farm_sensor_data (sensor_id);
CREATE INDEX idx_sensor_data_recorded_at ON farm_sensor_data (recorded_at);

-- ============================================================
-- 5) AGENT CATEGORIES
-- ============================================================

CREATE TABLE agent_categories (
    id              BIGSERIAL       PRIMARY KEY,
    category_name   VARCHAR(255)    UNIQUE NOT NULL,
    description     TEXT,
    created_at      TIMESTAMP       DEFAULT NOW()
);

-- ============================================================
-- 6) AGENT REGISTRY (22 AGENTS)
-- ============================================================

CREATE TABLE agent_registry (
    id                      BIGSERIAL       PRIMARY KEY,
    category_id             BIGINT          REFERENCES agent_categories(id),
    agent_name              VARCHAR(255)    UNIQUE NOT NULL,
    agent_type              VARCHAR(50),        -- analysis / vision / api / monitoring
    requires_image          BOOLEAN         DEFAULT FALSE,
    requires_sensor_data    BOOLEAN         DEFAULT FALSE,
    requires_external_api   BOOLEAN         DEFAULT FALSE,
    uses_memory             BOOLEAN         DEFAULT FALSE,
    is_active               BOOLEAN         DEFAULT TRUE,
    created_at              TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_agent_registry_category_id ON agent_registry (category_id);
CREATE INDEX idx_agent_registry_agent_type  ON agent_registry (agent_type);

-- ============================================================
-- 7) AGENT CAPABILITIES
-- ============================================================

CREATE TABLE agent_capabilities (
    id              BIGSERIAL       PRIMARY KEY,
    agent_id        BIGINT          NOT NULL REFERENCES agent_registry(id) ON DELETE CASCADE,
    capability_name VARCHAR(255),
    description     TEXT,
    created_at      TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_agent_capabilities_agent_id ON agent_capabilities (agent_id);

-- ============================================================
-- 8) ORCHESTRATOR SUPPORT KEYWORDS
-- ============================================================

CREATE TABLE agent_keywords (
    id              BIGSERIAL       PRIMARY KEY,
    agent_id        BIGINT          NOT NULL REFERENCES agent_registry(id) ON DELETE CASCADE,
    keyword         VARCHAR(100)
);

CREATE INDEX idx_agent_keywords_keyword ON agent_keywords (keyword);

-- ============================================================
-- 9) CONVERSATIONS (PARTITIONED — Infinite Retention)
-- ============================================================
-- Partitioned by RANGE on started_at (monthly partitions).
-- Supports infinite chat retention: older partitions are moved
-- to cold_storage tablespace — never deleted.

CREATE TABLE conversations (
    id              BIGSERIAL,
    user_id         BIGINT,
    farm_id         BIGINT,
    mode            VARCHAR(30),        -- orchestrator / direct_agent / voice
    session_id      VARCHAR(255),
    started_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMP,

    PRIMARY KEY (id, started_at)
) PARTITION BY RANGE (started_at);

CREATE INDEX idx_conversations_user_id     ON conversations (user_id);
CREATE INDEX idx_conversations_farm_id     ON conversations (farm_id);
CREATE INDEX idx_conversations_started_at  ON conversations (started_at);

-- ============================================================
-- 10) MESSAGES — HIGH-SCALE (PARTITIONED)
-- ============================================================
-- Partitioned by RANGE on created_at (monthly partitions).

CREATE TABLE messages (
    id                  BIGSERIAL,
    conversation_id     BIGINT          NOT NULL,
    agent_id            BIGINT,
    role                VARCHAR(20),        -- user / agent / system
    message_text        TEXT,
    input_type          VARCHAR(20),        -- text / voice / image
    audio_url           TEXT,
    routing_source      VARCHAR(30),        -- orchestrator / user_selected
    created_at          TIMESTAMP       NOT NULL,

    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

CREATE INDEX idx_messages_conversation_id ON messages (conversation_id);
CREATE INDEX idx_messages_agent_id        ON messages (agent_id);
CREATE INDEX idx_messages_created_at      ON messages (created_at);

-- ============================================================
-- 11) VECTOR MEMORY (pgvector)
-- ============================================================
-- Stores OpenAI-compatible 1536-dimensional embeddings
-- for semantic similarity search across conversations.

CREATE TABLE message_embeddings (
    id              BIGSERIAL       PRIMARY KEY,
    message_id      BIGINT,             -- logical FK to messages(id)
    user_id         BIGINT,
    conversation_id BIGINT,
    embedding       VECTOR(1536)    NOT NULL,
    created_at      TIMESTAMP       DEFAULT NOW()
);

-- IVFFlat index for approximate nearest-neighbor cosine similarity
-- NOTE: This index requires at least ~100 rows to build.
-- For initial bootstrapping, consider creating this index AFTER
-- a baseline amount of data has been inserted.
CREATE INDEX idx_message_embeddings_vector
    ON message_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ============================================================
-- 12) CROP IMAGES (FOR VISION AGENTS)
-- ============================================================

CREATE TABLE crop_images (
    id                  BIGSERIAL       PRIMARY KEY,
    conversation_id     BIGINT          REFERENCES conversations(id) ON DELETE CASCADE,
    image_url           TEXT,
    image_type          VARCHAR(30),        -- leaf / stem / fruit
    analysis_status     VARCHAR(20)     DEFAULT 'pending',   -- pending / processed
    created_at          TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_crop_images_conversation_id ON crop_images (conversation_id);

-- ============================================================
-- 12b) CONVERSATION SUMMARIES (Token Optimization)
-- ============================================================
-- Stores rolling summaries of conversations to reduce LLM
-- token usage. Instead of loading 500 old messages, load
-- the summary + the most recent 10 messages.

CREATE TABLE conversation_summaries (
    id                  BIGSERIAL       PRIMARY KEY,
    conversation_id     BIGINT          NOT NULL,           -- logical FK to conversations
    summary_text        TEXT            NOT NULL,
    last_message_id     BIGINT,                             -- logical FK to messages
    token_count         INTEGER,                            -- approx token count of summary
    updated_at          TIMESTAMP       DEFAULT NOW()
);

CREATE INDEX idx_conversation_summaries_conv_id ON conversation_summaries (conversation_id);

-- ============================================================
-- 13) AGENT EXECUTION LOGS (PARTITIONED)
-- ============================================================
-- Partitioned by RANGE on created_at (monthly partitions).

CREATE TABLE agent_executions (
    id                  BIGSERIAL,
    conversation_id     BIGINT,
    agent_id            BIGINT,
    triggered_by        VARCHAR(30),        -- orchestrator / user_selected
    input_tokens        INTEGER,
    output_tokens       INTEGER,
    execution_time_ms   INTEGER,
    confidence_score    NUMERIC(5, 4),
    status              VARCHAR(20),        -- success / failed
    created_at          TIMESTAMP       NOT NULL,

    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

CREATE INDEX idx_agent_executions_agent_id        ON agent_executions (agent_id);
CREATE INDEX idx_agent_executions_conversation_id ON agent_executions (conversation_id);
CREATE INDEX idx_agent_executions_created_at      ON agent_executions (created_at);

-- ============================================================
-- 14) WEATHER API LOGS
-- ============================================================

CREATE TABLE weather_api_logs (
    id                  BIGSERIAL       PRIMARY KEY,
    farm_id             BIGINT          REFERENCES farms(id),
    temperature         NUMERIC(7, 2),
    humidity            NUMERIC(7, 2),
    rain_prediction     VARCHAR(100),
    api_response_json   JSONB,
    fetched_at          TIMESTAMP       NOT NULL
);

CREATE INDEX idx_weather_api_logs_farm_id    ON weather_api_logs (farm_id);
CREATE INDEX idx_weather_api_logs_fetched_at ON weather_api_logs (fetched_at);

-- ============================================================
-- 15) MARKET PRICE API LOGS
-- ============================================================

CREATE TABLE market_price_logs (
    id                  BIGSERIAL       PRIMARY KEY,
    crop_type           VARCHAR(100),
    market_name         VARCHAR(255),
    price_per_quintal   NUMERIC(10, 2),
    api_response_json   JSONB,
    fetched_at          TIMESTAMP       NOT NULL
);

CREATE INDEX idx_market_price_logs_fetched_at ON market_price_logs (fetched_at);

-- ============================================================
-- 16) SYSTEM METRICS (Observability)
-- ============================================================
-- Stores latency and performance metrics for monitoring dashboards.
-- metric_type: db_latency | api_latency | vector_latency | agent_latency
--              | sensor_ingestion | orchestrator_routing

CREATE TABLE system_metrics (
    id              BIGSERIAL       PRIMARY KEY,
    metric_type     VARCHAR(50)     NOT NULL,
    metric_value    NUMERIC(12, 4)  NOT NULL,
    agent_id        BIGINT,                             -- optional, for agent-specific metrics
    metadata        JSONB,                              -- flexible extra context
    recorded_at     TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_system_metrics_type        ON system_metrics (metric_type);
CREATE INDEX idx_system_metrics_recorded_at ON system_metrics (recorded_at);

-- ============================================================
-- END OF SCHEMA
-- ============================================================
-- Next steps:
--   1. Run database/create_partitions.sql to create monthly partitions
--   2. Run database/seed_agents.sql to populate agent categories & registry
--   3. Run database/row_level_security.sql to enable multi-tenant RLS
--   4. Run database/cold_storage_management.sql for partition lifecycle
-- ============================================================
