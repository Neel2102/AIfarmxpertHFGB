# FarmXpert — Enterprise Database Operations Guide

> Complete operational reference for the FarmXpert PostgreSQL infrastructure.
> Covers all 14 enterprise requirements: infinite retention, cold storage,
> vector search, hybrid memory, RLS, read replicas, connection pooling,
> backup/WAL, conversation summaries, orchestrator routing,
> monitoring, performance rules, scaling targets, and storage estimation.

---

## Table of Contents

1. [Infinite Chat Retention Strategy](#1-infinite-chat-retention-strategy)
2. [Cold Storage Management](#2-cold-storage-management)
3. [Vector Search Production Tuning](#3-vector-search-production-tuning)
4. [Hybrid Memory Strategy](#4-hybrid-memory-strategy)
5. [Row Level Security](#5-row-level-security)
6. [Read Replica Strategy](#6-read-replica-strategy)
7. [Connection Pooling](#7-connection-pooling)
8. [Backup & WAL Archiving](#8-backup--wal-archiving)
9. [Conversation Summaries](#9-conversation-summaries)
10. [Orchestrator Routing Logic](#10-orchestrator-routing-logic)
11. [Monitoring Metrics](#11-monitoring-metrics)
12. [Performance Safety Rules](#12-performance-safety-rules)
13. [Scaling Targets](#13-scaling-targets)
14. [Storage Estimation](#14-storage-estimation)

---

## 1. Infinite Chat Retention Strategy

**Policy: NO DATA IS EVER DELETED.**

### Tiered Architecture

| Tier | Data Age | Tablespace | Storage | Access |
|------|----------|------------|---------|--------|
| **HOT** | 0–6 months | `pg_default` (SSD) | Fast NVMe | Read/Write |
| **COLD** | 6+ months | `cold_storage` (HDD) | Cheap HDD | Read-Only |

### Partitioned Tables (4 total)

| Table | Partition Key | Retention |
|-------|--------------|-----------|
| `messages` | `created_at` | ♾ Infinite |
| `conversations` | `started_at` | ♾ Infinite |
| `agent_executions` | `created_at` | ♾ Infinite |
| `farm_sensor_data` | `recorded_at` | ♾ Infinite |

### Lifecycle

```
New data → HOT partition (SSD)
    ↓ (after 6 months)
Cold migration → COLD partition (HDD)
    ↓ (autovacuum disabled, read-only)
Stays forever → Full query access preserved
```

### Monthly Automation

```sql
-- Run on 1st of every month at 2 AM
CALL migrate_partitions_to_cold(6);
```

See: [cold_storage_management.sql](file:///d:/AI/AIfarmxpertIITGN/farmxpert/database/cold_storage_management.sql)

---

## 2. Cold Storage Management

### Setup

```sql
-- Create tablespace (directory must exist and be owned by postgres)
CREATE TABLESPACE cold_storage LOCATION '/var/lib/postgresql/cold_data';
```

### Manual Migration

```sql
-- Move a specific partition
ALTER TABLE messages_2025_01 SET TABLESPACE cold_storage;
ALTER TABLE messages_2025_01 SET (autovacuum_enabled = false);
```

### Automated Migration

```sql
-- Migrate all partitions > 6 months old
CALL migrate_partitions_to_cold(6);
```

### Verify Distribution

```sql
SELECT
    p.relname AS parent_table,
    c.relname AS partition,
    COALESCE(ts.spcname, 'pg_default') AS tablespace,
    CASE WHEN ts.spcname = 'cold_storage' THEN 'COLD' ELSE 'HOT' END AS tier,
    pg_size_pretty(pg_relation_size(c.oid)) AS size
FROM pg_inherits i
JOIN pg_class c ON c.oid = i.inhrelid
JOIN pg_class p ON p.oid = i.inhparent
LEFT JOIN pg_tablespace ts ON ts.oid = c.reltablespace
WHERE p.relname IN ('farm_sensor_data', 'messages', 'agent_executions', 'conversations')
ORDER BY p.relname, c.relname;
```

---

## 3. Vector Search Production Tuning

### IVFFlat Index Configuration

```sql
-- Index with dynamic lists count: lists ≈ sqrt(total_rows)
-- For 10M embeddings: sqrt(10,000,000) ≈ 3162 → use lists = 3000
CREATE INDEX idx_message_embeddings_vector
    ON message_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);     -- start with 100, increase as data grows
```

### Runtime Tuning

```sql
-- Increase probes for better recall (at cost of speed)
-- Default: 1 probe. Recommended: 10–20 for production.
SET ivfflat.probes = 10;

-- For high-accuracy searches:
SET ivfflat.probes = 20;
```

### Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| `ANALYZE message_embeddings` | Weekly | Run via pg_cron |
| Reindex IVFFlat | Every 5M new rows | `REINDEX INDEX CONCURRENTLY idx_message_embeddings_vector;` |
| Verify index health | Monthly | `SELECT * FROM pg_stat_user_indexes WHERE indexrelname LIKE '%embedding%';` |

### Reindex Procedure

```sql
-- Non-blocking reindex (PG 12+)
REINDEX INDEX CONCURRENTLY idx_message_embeddings_vector;

-- If data exceeds 10M rows, increase lists count:
DROP INDEX idx_message_embeddings_vector;
CREATE INDEX idx_message_embeddings_vector
    ON message_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 3000);
```

---

## 4. Hybrid Memory Strategy

For every agent request, the system combines **short-term** and **long-term** memory:

```
┌─────────────────────────────────────────┐
│           AGENT REQUEST                 │
├─────────────────────────────────────────┤
│                                         │
│  Step 1: Fetch last 5 recent messages   │
│          (chronological order)          │
│                    ↓                    │
│  Step 2: Fetch top 5 semantically       │
│          similar messages (pgvector)    │
│                    ↓                    │
│  Step 3: Merge + deduplicate            │
│          (by message_id)                │
│                    ↓                    │
│  Step 4: Send combined context to LLM   │
│                                         │
└─────────────────────────────────────────┘
```

### SQL Implementation

```sql
-- Step 1: Recent messages (short-term memory)
SELECT id, message_text, created_at
FROM messages
WHERE conversation_id = :conv_id
ORDER BY created_at DESC
LIMIT 5;

-- Step 2: Semantic similarity (long-term memory)
SET ivfflat.probes = 10;
SELECT me.message_id, m.message_text, me.embedding <=> :query_embedding AS distance
FROM message_embeddings me
JOIN messages m ON m.id = me.message_id
WHERE me.user_id = :user_id
ORDER BY me.embedding <=> :query_embedding
LIMIT 5;

-- Step 3: Merge + dedup in application layer
-- Combine both result sets, deduplicate by message_id
-- Sort by relevance (semantic distance) then recency

-- Step 4: Send to LLM as context window
```

### Fallback: Use Conversation Summary

```sql
-- If conversation has 500+ messages, use summary instead
SELECT summary_text FROM conversation_summaries
WHERE conversation_id = :conv_id
ORDER BY updated_at DESC LIMIT 1;
-- Then append recent 10 messages on top
```

---

## 5. Row Level Security

**Multi-tenant isolation ensures farmers can ONLY access their own data.**

### Protected Tables

| Table | Isolation Strategy |
|-------|-------------------|
| `conversations` | Direct `user_id` match |
| `messages` | Via `conversation_id` → `conversations.user_id` |
| `farms` | Direct `user_id` match |
| `sensors` | Via `farm_id` → `farms.user_id` |
| `farm_sensor_data` | Via `sensor_id` → `sensors.farm_id` → `farms.user_id` |
| `crop_images` | Via `conversation_id` → `conversations.user_id` |
| `message_embeddings` | Direct `user_id` match |

### Application Usage

```sql
-- Set tenant context before any query
SET LOCAL app.current_user_id = '42';

-- Now all queries are auto-filtered
SELECT * FROM conversations;  -- only user 42's data
SELECT * FROM messages WHERE conversation_id = 99; -- RLS enforced
```

### Important: PgBouncer Compatibility

Use `SET LOCAL` (not `SET`) so the variable is scoped to the current transaction only. This is required for PgBouncer transaction pooling mode.

See: [row_level_security.sql](file:///d:/AI/AIfarmxpertIITGN/farmxpert/database/row_level_security.sql)

---

## 6. Read Replica Strategy

### Architecture

```
┌──────────────────┐       ┌──────────────────┐
│  PRIMARY (Write)  │──────▶│  REPLICA (Read)   │
│                   │  WAL  │                   │
│  • Agent logging  │ stream│  • Chat history   │
│  • Sensor ingest  │       │  • Dashboard      │
│  • Conversations  │       │  • Vector search  │
│  • Writes only    │       │  • Analytics      │
└──────────────────┘       └──────────────────┘
     ↑  port 5433               ↑  port 5434
     │                          │
 PgBouncer (6432)          PgBouncer-RO (6433)
     ↑                          ↑
 Application writes         Application reads
```

### Setup Streaming Replication

```bash
# On PRIMARY (already configured in docker-compose.yml):
# wal_level = replica
# max_wal_senders = 5
# hot_standby = on

# On REPLICA server:
pg_basebackup -h primary-host -D /var/lib/postgresql/data -U repl_user -Fp -Xs -R
```

### Connection Strings

```
# Write operations (primary via PgBouncer)
DATABASE_URL_WRITE=postgres://farmxpert:pwd@localhost:6432/farmxpert_db

# Read operations (replica via PgBouncer-RO)
DATABASE_URL_READ=postgres://farmxpert:pwd@localhost:6433/farmxpert_db
```

### Application Routing Rules

| Operation | Target |
|-----------|--------|
| INSERT, UPDATE, DELETE | PRIMARY |
| Agent execution logging | PRIMARY |
| Sensor data ingestion | PRIMARY |
| Chat history reads | REPLICA |
| Dashboard analytics | REPLICA |
| Vector similarity search | REPLICA |
| Conversation summaries | REPLICA |

---

## 7. Connection Pooling

### PgBouncer Configuration (Transaction Mode)

| Setting | Value | Rationale |
|---------|-------|-----------|
| `POOL_MODE` | `transaction` | Each transaction gets a connection |
| `MAX_CLIENT_CONN` | 1000 | Supports thousands of concurrent farmers |
| `DEFAULT_POOL_SIZE` | 50 | Actual PG connections per pool |
| `MIN_POOL_SIZE` | 10 | Minimum warm connections |
| `RESERVE_POOL_SIZE` | 10 | Emergency overflow pool |
| `MAX_DB_CONNECTIONS` | 100 | Hard cap on PG connections |

### Connection Path

```
Farmer App → PgBouncer (port 6432) → PostgreSQL (port 5432)
                1000 clients             50 connections
```

### Important Constraints in Transaction Mode

1. **Use `SET LOCAL`** instead of `SET` for session variables (RLS)
2. **No prepared statements** across transactions
3. **No `LISTEN/NOTIFY`** — use separate direct connections
4. **No session-level temp tables** — use CTEs instead

---

## 8. Backup & WAL Archiving

### WAL Configuration (in docker-compose.yml)

```
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
max_wal_senders = 5
wal_keep_size = 1GB
```

### Backup Strategy

| Type | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| **Full backup** | Daily at 3 AM | 7 days hot, 30 days cold | `pg_basebackup` |
| **WAL archiving** | Continuous | 7 days | `archive_command` |
| **Point-in-time recovery** | On demand | Up to 7 days | WAL replay |

### Backup Script

```bash
#!/bin/bash
# Daily full backup
BACKUP_DIR="/backups/farmxpert/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

pg_basebackup \
    -h localhost -p 5433 \
    -U farmxpert \
    -D "$BACKUP_DIR" \
    -Ft -z -Xs \
    --checkpoint=fast

# Cleanup backups older than 30 days
find /backups/farmxpert/ -type d -mtime +30 -exec rm -rf {} +
```

### Point-in-Time Recovery

```bash
# Restore to specific timestamp
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2026-03-01 14:00:00'
```

### NO DELETION POLICY

> **CRITICAL**: The backup strategy MUST preserve all data indefinitely.
> WAL archives and backups are retention-only — no purging of chat data
> from the primary database. Only WAL files and backup snapshots are rotated.

---

## 9. Conversation Summaries

### Purpose

Reduce LLM token usage by summarizing long conversations instead of loading hundreds of messages.

### Table

```sql
conversation_summaries (
    id                  BIGSERIAL PRIMARY KEY,
    conversation_id     BIGINT NOT NULL,
    summary_text        TEXT NOT NULL,
    last_message_id     BIGINT,
    token_count         INTEGER,
    updated_at          TIMESTAMP DEFAULT NOW()
)
```

### Strategy

```
If conversation has < 20 messages → load all messages
If conversation has 20–100 messages → load summary + last 10 messages
If conversation has 100+ messages → load summary + last 5 messages + top 3 semantic matches
```

### Summary Generation (Background Worker)

```python
# Pseudo-code for background worker
def update_conversation_summary(conversation_id):
    messages = fetch_all_messages(conversation_id)
    if len(messages) >= 20:
        summary = llm.summarize(messages)
        upsert_summary(conversation_id, summary, messages[-1].id)
```

### Trigger: Generate/update summary every 20 new messages.

---

## 10. Orchestrator Routing Logic

### Decision Flow

```
User Query Received
       │
       ▼
┌──────────────────┐
│ Image Attached?   │──YES──▶ Pest & Disease Detector / Crop Health Vision
└──────────────────┘
       │ NO
       ▼
┌──────────────────┐
│ Keyword Match?    │──YES──▶ Route to matched agent (agent_keywords table)
└──────────────────┘
       │ NO
       ▼
┌──────────────────┐
│ Weather Intent?   │──YES──▶ Weather Watcher
└──────────────────┘
       │ NO
       ▼
┌──────────────────┐
│ Price Intent?     │──YES──▶ Market Intelligence / Mandi Price Predictor
└──────────────────┘
       │ NO
       ▼
┌──────────────────┐
│ Crop Health?      │──YES──▶ Growth Stage Monitor / Soil Health Analyzer
└──────────────────┘
       │ NO
       ▼
   Farm Coach (default fallback)
```

### Logging Requirements

Every orchestrator decision MUST be logged in `agent_executions`:

| Field | Value |
|-------|-------|
| `triggered_by` | `'orchestrator'` |
| `confidence_score` | 0.0–1.0 (keyword match strength) |
| `execution_time_ms` | Time to make routing decision |
| `status` | `'success'` or `'failed'` |

### Fallback Agent

When no keyword matches with confidence > 0.5, route to **Farm Coach** as the default advisory agent.

---

## 11. Monitoring Metrics

### `system_metrics` Table

```sql
metric_type options:
    'db_latency'            -- database query latency
    'api_latency'           -- external API call latency
    'vector_latency'        -- pgvector similarity search latency
    'agent_latency'         -- agent execution latency
    'sensor_ingestion'      -- sensor data write latency
    'orchestrator_routing'  -- routing decision latency
```

### Example Inserts

```sql
INSERT INTO system_metrics (metric_type, metric_value, agent_id, metadata)
VALUES ('agent_latency', 245.5, 3, '{"agent_name": "Crop Selector", "query_tokens": 150}');

INSERT INTO system_metrics (metric_type, metric_value, metadata)
VALUES ('db_latency', 12.3, '{"query": "SELECT messages", "rows": 50}');
```

### Dashboard Queries

```sql
-- Average latency by type (last 24h)
SELECT metric_type, AVG(metric_value) AS avg_ms, MAX(metric_value) AS max_ms
FROM system_metrics
WHERE recorded_at > NOW() - INTERVAL '24 hours'
GROUP BY metric_type;

-- P95 agent latency
SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY metric_value) AS p95_ms
FROM system_metrics
WHERE metric_type = 'agent_latency'
  AND recorded_at > NOW() - INTERVAL '1 hour';
```

---

## 12. Performance Safety Rules

### MANDATORY query rules — enforced at application layer:

| Rule | Rationale |
|------|-----------|
| ❌ Never `SELECT *` without `LIMIT` | Prevents full-table scans on partitioned tables |
| ✅ Always paginate history queries | Use `LIMIT/OFFSET` or keyset pagination |
| ✅ Always filter by `user_id` | RLS enforces this, but explicit filter improves perf |
| ✅ Always use indexes on FK lookups | All FKs are indexed in the schema |
| ❌ Never vector search without `LIMIT` | IVFFlat requires `ORDER BY ... LIMIT N` pattern |
| ✅ Always use `SET ivfflat.probes` before vector queries | Default of 1 probe gives poor recall |
| ❌ Never join across partitioned + non-partitioned tables without date filter | Prevents scanning all partitions |
| ✅ Always include partition key in WHERE clause | Enables partition pruning |

### Example: Good vs Bad Queries

```sql
-- ❌ BAD: Scans all message partitions
SELECT * FROM messages WHERE conversation_id = 42;

-- ✅ GOOD: Partition pruning + limit
SELECT * FROM messages
WHERE conversation_id = 42
  AND created_at >= NOW() - INTERVAL '30 days'
ORDER BY created_at DESC
LIMIT 50;

-- ❌ BAD: Vector search without limit
SELECT * FROM message_embeddings
ORDER BY embedding <=> :query_embedding;

-- ✅ GOOD: Vector search with limit + probes
SET ivfflat.probes = 10;
SELECT message_id, embedding <=> :query_embedding AS distance
FROM message_embeddings
WHERE user_id = :user_id
ORDER BY embedding <=> :query_embedding
LIMIT 5;
```

---

## 13. Scaling Targets

### Production Capacity

| Metric | Target | Strategy |
|--------|--------|----------|
| Farmers | **1M+** | PgBouncer pooling, RLS isolation |
| Messages | **100M+** | Monthly partitioning, cold storage |
| Embeddings | **10M+** | IVFFlat with dynamic lists, periodic reindex |
| Sensor writes/day | **500K** | Partitioned `farm_sensor_data`, batch inserts |
| Read latency | **< 300ms** | Read replicas, connection pooling, partition pruning |

### Horizontal Scaling Path

```
Phase 1 (Current): Single primary + read replica
    ↓
Phase 2: Citus for distributed tables (sensor_data, messages)
    ↓
Phase 3: Dedicated sensor database (TimescaleDB)
    ↓
Phase 4: Separate vector database (Pinecone/Weaviate) for embeddings
```

---

## 14. Storage Estimation

### Per-Row Sizes

| Table | Avg Row Size | Notes |
|-------|-------------|-------|
| `messages` | ~1.5 KB | Text messages + metadata |
| `message_embeddings` | ~6.2 KB | 1536 × 4 bytes + overhead |
| `farm_sensor_data` | ~200 bytes | 9 numeric fields + timestamp |
| `conversations` | ~150 bytes | Metadata only |
| `agent_executions` | ~120 bytes | Counters and scores |

### Projected Storage (1 Year)

| Table | Rows/Year | Size/Year |
|-------|-----------|-----------|
| `messages` | 100M | **~150 GB** |
| `message_embeddings` | 10M | **~62 GB** |
| `farm_sensor_data` | 182M (500K/day) | **~36 GB** |
| `conversations` | 10M | **~1.5 GB** |
| `agent_executions` | 50M | **~6 GB** |
| **Indexes** | — | **~50 GB** |
| **Total Year 1** | — | **~305 GB** |

### Storage Planning

| Year | Cumulative | Recommendation |
|------|-----------|----------------|
| Year 1 | ~305 GB | 500 GB SSD |
| Year 2 | ~610 GB | 1 TB SSD + 500 GB HDD (cold) |
| Year 3 | ~915 GB | 1 TB SSD + 1 TB HDD (cold) |
| Year 5 | ~1.5 TB | Evaluate Citus / separate sensor DB |

### WAL Archive Storage

- WAL generation: ~10–50 GB/day under heavy write load
- 7-day WAL retention: ~350 GB reserved
- Recommend: separate disk/volume for WAL archive

---

## Quick Reference: File Map

| File | Purpose |
|------|---------|
| [schema.sql](file:///d:/AI/AIfarmxpertIITGN/farmxpert/database/schema.sql) | 17 tables + extensions + indexes |
| [seed_agents.sql](file:///d:/AI/AIfarmxpertIITGN/farmxpert/database/seed_agents.sql) | 5 categories + 22 agents |
| [create_partitions.sql](file:///d:/AI/AIfarmxpertIITGN/farmxpert/database/create_partitions.sql) | 144 monthly partitions |
| [row_level_security.sql](file:///d:/AI/AIfarmxpertIITGN/farmxpert/database/row_level_security.sql) | RLS policies on 7 tables |
| [cold_storage_management.sql](file:///d:/AI/AIfarmxpertIITGN/farmxpert/database/cold_storage_management.sql) | Cold tier lifecycle |
| [docker-compose.yml](file:///d:/AI/AIfarmxpertIITGN/farmxpert/docker-compose.yml) | PostgreSQL + PgBouncer + WAL |
