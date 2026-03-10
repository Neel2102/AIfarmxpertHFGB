-- ============================================================
-- FarmXpert — Row Level Security (Multi-Tenant Isolation)
-- ============================================================
-- Enforces tenant isolation: users can only access their own data.
-- Requires: SET app.current_user_id = '<user_id>' before queries.
-- ============================================================

-- ──────────────────────────────────────────────────────────────
-- 1) Create application role for RLS enforcement
-- ──────────────────────────────────────────────────────────────

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user LOGIN;
    END IF;
END $$;

-- Grant baseline permissions
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- ──────────────────────────────────────────────────────────────
-- 2) Enable RLS on tenant-scoped tables
-- ──────────────────────────────────────────────────────────────

-- conversations (partitioned — RLS applies to parent)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations FORCE ROW LEVEL SECURITY;

CREATE POLICY conversations_tenant_isolation ON conversations
    FOR ALL
    TO app_user
    USING (user_id = current_setting('app.current_user_id')::BIGINT)
    WITH CHECK (user_id = current_setting('app.current_user_id')::BIGINT);

-- messages (partitioned — RLS via conversation ownership)
-- Messages are accessed through conversations, so we enforce
-- that the conversation belongs to the current user.
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages FORCE ROW LEVEL SECURITY;

CREATE POLICY messages_tenant_isolation ON messages
    FOR ALL
    TO app_user
    USING (
        conversation_id IN (
            SELECT id FROM conversations
            WHERE user_id = current_setting('app.current_user_id')::BIGINT
        )
    );

-- farms
ALTER TABLE farms ENABLE ROW LEVEL SECURITY;
ALTER TABLE farms FORCE ROW LEVEL SECURITY;

CREATE POLICY farms_tenant_isolation ON farms
    FOR ALL
    TO app_user
    USING (user_id = current_setting('app.current_user_id')::BIGINT)
    WITH CHECK (user_id = current_setting('app.current_user_id')::BIGINT);

-- farm_sensor_data (via sensor → farm → user ownership chain)
ALTER TABLE farm_sensor_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE farm_sensor_data FORCE ROW LEVEL SECURITY;

CREATE POLICY sensor_data_tenant_isolation ON farm_sensor_data
    FOR ALL
    TO app_user
    USING (
        sensor_id IN (
            SELECT s.id FROM sensors s
            JOIN farms f ON s.farm_id = f.id
            WHERE f.user_id = current_setting('app.current_user_id')::BIGINT
        )
    );

-- sensors (via farm ownership)
ALTER TABLE sensors ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensors FORCE ROW LEVEL SECURITY;

CREATE POLICY sensors_tenant_isolation ON sensors
    FOR ALL
    TO app_user
    USING (
        farm_id IN (
            SELECT id FROM farms
            WHERE user_id = current_setting('app.current_user_id')::BIGINT
        )
    );

-- crop_images (via conversation ownership)
ALTER TABLE crop_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE crop_images FORCE ROW LEVEL SECURITY;

CREATE POLICY crop_images_tenant_isolation ON crop_images
    FOR ALL
    TO app_user
    USING (
        conversation_id IN (
            SELECT id FROM conversations
            WHERE user_id = current_setting('app.current_user_id')::BIGINT
        )
    );

-- message_embeddings (direct user_id column)
ALTER TABLE message_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_embeddings FORCE ROW LEVEL SECURITY;

CREATE POLICY embeddings_tenant_isolation ON message_embeddings
    FOR ALL
    TO app_user
    USING (user_id = current_setting('app.current_user_id')::BIGINT)
    WITH CHECK (user_id = current_setting('app.current_user_id')::BIGINT);

-- conversation_summaries (via conversation ownership)
ALTER TABLE conversation_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_summaries FORCE ROW LEVEL SECURITY;

CREATE POLICY summaries_tenant_isolation ON conversation_summaries
    FOR ALL
    TO app_user
    USING (
        conversation_id IN (
            SELECT id FROM conversations
            WHERE user_id = current_setting('app.current_user_id')::BIGINT
        )
    );

-- ──────────────────────────────────────────────────────────────
-- 3) Superuser / admin bypass
-- ──────────────────────────────────────────────────────────────
-- The database owner (farmxpert) and superusers bypass RLS by default.
-- For admin users, create a separate role:
--
--   CREATE ROLE app_admin INHERIT;
--   GRANT app_user TO app_admin;
--   ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;  -- already done
--   CREATE POLICY admin_full_access ON conversations
--       FOR ALL TO app_admin USING (true) WITH CHECK (true);

-- ──────────────────────────────────────────────────────────────
-- USAGE IN APPLICATION CODE
-- ──────────────────────────────────────────────────────────────
-- Before running any query as a tenant user, set the session variable:
--
--   SET LOCAL app.current_user_id = '42';
--   SELECT * FROM conversations;  -- only sees user 42's conversations
--
-- In connection pooling (PgBouncer transaction mode), use SET LOCAL
-- so the setting is scoped to the current transaction only.
-- ============================================================
