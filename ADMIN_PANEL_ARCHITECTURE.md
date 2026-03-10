# FarmXpert — God Mode Admin Panel Architecture (Production Blueprint)

## 1) Executive Summary
FarmXpert’s admin panel should be a **separate, RBAC-protected control plane** under `/admin` (frontend) backed by an `/api/admin/*` namespace (backend). It must support:

- **User & Farm Management** (identity, onboarding, multi-tenant farm mapping, suspensions)
- **IoT Fleet Monitoring** (live + historical 9-metric telemetry, device uptime, gaps)
- **AI Economics & Agent Tracking** (token + cost per user/farm/agent, rate-limit events, full interaction review)
- **System Health & Database** (latency/error monitoring, table sizes/retention, ingestion backlogs)
- **Dynamic Controls** (sensor overrides, manual alerts, prompt/agent behavior tweaks without redeploy)

Key design principle: **everything “God Mode” does must be auditable** (who did what, when, why, what changed).

### 1.1 Finalized MVP Decisions (Locked)
- **Identity**: Consolidate into a single canonical `users` table.
- **Farms**: Assume **One User = One Farm** for MVP (enforce with a unique constraint).
- **Telemetry retention**: Retain raw `sensor_readings` for **30 days**.
- **Telemetry cadence**: Expected device publish interval is **every 15 minutes**.
- **LLM providers**: Use **Gemini via LiteLLM** now; design must be **OpenAI-ready**.
- **Deletes**: Prefer **soft deletes** (`is_active = false` / `deleted_at`) over hard deletes.

---

## 2) Current-State Analysis (Grounded in Repository)

### 2.1 Identity & Multi-Tenancy (Current)
You currently have **two user tables**:

- `users` (`farmxpert/models/user_models.py`)
  - Fields: `id`, `username`, `email`, `is_active`, `is_verified`, `onboarding_completed`, etc.
  - Used by `interfaces/api/routes/auth_routes.py` and `services/auth_service.py`.

- `auth_users` (`farmxpert/models/user_models.py`)
  - Fields: `id`, `farmer_id`, `email`, `username`, `role`, etc.
  - `farms.user_id` references `auth_users.id`.

Also:

- `farm_profiles.user_id` is an `Integer` and is **not a foreign key**.
- Many routes resolve `Farm` using `db.query(Farm).first()` (non-tenant-safe).

**Implication:** Admin panel must reconcile identity. For production, you need a **single authoritative identity model** or a well-defined mapping between `users` and `auth_users`.

### 2.2 Farm Data Models (Current)
- `Farm` table (`farm_models.py`) is multi-tenant (via `user_id -> auth_users.id`), with:
  - `farm_name`, `state`, `district`, `village`, `lat/long`, `soil_type`
- `FarmProfile` (`farm_profile_models.py`) stores onboarding survey-style data, keyed by `user_id` (int).

**Implication:** “locked-in farm data” exists in two places (`Farm` + `FarmProfile`) with different shapes and tenancy keys.

### 2.3 IoT / Sensor Data (Current)
You have:

- `blynk_devices` (`BlynkDevice`)
  - `farm_id` is a logical reference (no FK), `status`, `last_seen_at`, `last_error`, `is_active`

- `sensor_readings` (`SensorReading`)
  - High-volume telemetry with `recorded_at` and 9 metrics.
  - Notes indicate **partitioning constraints** (no FK for older PostgreSQL).

Endpoints:
- `/api/blynk/*` includes ingest + reads (`/readings`, `/latest`) but currently supports optional `farm_id` and lacks admin-grade filtering (user/farm/device ranges, downsampling, gap detection).
- `/api/iot/inject` exists to inject readings.

**Implication:** Admin panel should treat sensor telemetry as a **time-series subsystem** with retention, downsampling, and anomaly/gap detection.

### 2.4 AI / Agent Tracking (Current)
You have:

- `agent_interactions` (`AgentInteraction` in `farm_models.py`)
  - `farm_id`, `agent_name`, `query`, `response`, `context_data`, `response_time_ms`, `tokens_used`, `success`, `created_at`
  - Core agent writes `AgentInteraction` when `user_id` is provided and can resolve a farm.

LLM usage:
- `interfaces/api/routes/llm_usage_routes.py` returns summary/recent from `services/gemini_service.py`.
- `GeminiService` tracks usage **in-memory** (`_usage_events`) and does not persist token/cost to DB.
- Repository contains `litellm` references (requirements + usage in `core_agent_updated.py`), but production-grade cost tracking is not yet implemented in DB.

**Implication:** Admin panel needs a **durable usage ledger** (DB tables) fed by LiteLLM callbacks/middleware.

### 2.5 System Health (Current)
- `RequestLoggingMiddleware` logs request duration to app logger.
- `app/routers/system.py` contains placeholder “realtime status”.

**Implication:** For admin-grade health, you need:
- persistent API error/latency summaries (or integrate Prometheus/OpenTelemetry)
- DB size metrics
- ingest backlog metrics

---

## 3) Target Architecture (High-Level)

### 3.1 Admin Access & RBAC
**Backend must enforce admin security**, not just the frontend.

- Add `role`/`is_admin` to the authoritative user table (or consolidate identity).
- Use JWT claims with `role` and enforce via dependencies:
  - `require_admin()`
  - `require_admin_or_support()`

**Strong recommendation:** Separate privilege levels:
- `admin` (full God Mode)
- `support` (read-only + limited actions like messaging)
- `auditor` (read-only, can export logs)

### 3.2 Auditability
Every write in admin must create an **immutable audit event** capturing:
- actor (admin user)
- target (user/farm/device/agent)
- action type
- before/after JSON diff
- reason/comment
- request correlation (`request_id`, IP, user-agent)

### 3.3 Multi-Tenant Correctness
Admin needs global visibility; farmer-facing endpoints need tenant scoping.

- Introduce a consistent `tenant_key` concept:
  - **Final (MVP)**: `users.id` is canonical and `farms.user_id` references `users.id`.

During migration from `auth_users`, keep a temporary bridge path for read-only admin lookups if needed, but all new admin and product features should be implemented against `users`.

### 3.4 Observability
Admin panel should not query raw logs from files. Instead:
- Persist request metrics in DB (lightweight) or
- Expose Prometheus metrics to a monitoring stack

For a production SaaS, recommended path:
- **OpenTelemetry for traces**
- **Prometheus for metrics**
- **Loki/ELK for logs**

Admin UI can consume aggregated metrics via backend endpoints.

---

## 4) Proposed React Admin App Structure (`/admin`)

### 4.1 Sidebar Navigation (Top-Level)
- **Dashboard**
- **Users**
  - User List
  - User Detail
  - Sessions
- **Farms**
  - Farm List
  - Farm Detail
- **IoT Fleet**
  - Fleet Overview
  - Devices
  - Telemetry Explorer
  - Uptime & Gaps
- **AI / Agents**
  - Usage Overview
  - Agent Interactions
  - Chat Sessions (Super Agent)
  - Rate Limits / Errors
- **System Health**
  - API Latency & Errors
  - DB Tables & Storage
  - Background Jobs / Ingestion
- **Dynamic Controls**
  - Sensor Overrides
  - Alerts / Broadcast
  - Prompt & Config Registry
  - Feature Flags
- **Audit Log**

### 4.2 Component Tree (Conceptual)
```
/admin
  AdminAppShell
    AdminTopBar
      EnvironmentBadge
      GlobalSearch (users/farms/devices)
      AdminUserMenu
    AdminSidebar
      NavSection(Dashboard)
      NavSection(Users)
      NavSection(Farms)
      NavSection(IoT Fleet)
      NavSection(AI / Agents)
      NavSection(System Health)
      NavSection(Dynamic Controls)
      NavSection(Audit Log)
    AdminMain
      <Routes>
        /admin/dashboard
          AdminDashboardPage
            KPIGrid
            TimeSeriesPanels
            RecentIncidents
        /admin/users
          UsersListPage
            UsersTable (filters, bulk actions)
        /admin/users/:userId
          UserDetailPage
            UserHeader (status, role, suspend)
            UserTabs
              OverviewTab
              FarmsTab
              IoTTab
              AITab
              SessionsTab
              AuditTrailTab
        /admin/farms
          FarmsListPage
        /admin/farms/:farmId
          FarmDetailPage
            FarmOverview
            TelemetryMiniPanels
            AgentInteractionsMiniPanels
        /admin/iot
          IoTFleetOverviewPage
            FleetKPIs
            OfflineDevicesTable
            IngestionHealth
        /admin/iot/devices
          DevicesPage
        /admin/iot/telemetry
          TelemetryExplorerPage
            FarmPicker + DevicePicker
            MetricMultiChart (9 metrics)
            DownsampleControls
            ExportCSVButton
        /admin/ai
          AIUsageOverviewPage
        /admin/ai/interactions
          AgentInteractionsPage
            Filters(user/farm/agent/success/date)
            InteractionDetailDrawer
        /admin/system
          SystemHealthPage
        /admin/controls
          DynamicControlsHome
        /admin/controls/sensor-overrides
          SensorOverridesPage
        /admin/controls/alerts
          AlertsPage
        /admin/controls/prompts
          PromptRegistryPage
        /admin/audit
          AuditLogPage
      </Routes>
```

### 4.3 Data Fetching Strategy
- Use a query client (React Query) with:
  - server-side pagination for tables
  - caching + stale times
  - polling for live widgets (5s–15s)
  - SSE/WebSocket for true live telemetry (optional phase 2)

Given the 15-minute sensor publish interval:
- Admin “live” telemetry widgets should poll `latest` at **60s–120s** (not 5s).
- Fleet uptime pages can poll device `last_seen_at` at **60s–180s**.

### 4.4 Visualization
Telemetry Explorer should support:
- 9 metrics as toggles (Air/Soil Temp, Humidity, Moisture, EC, pH, N, P, K)
- multiple y-axes or normalized chart mode
- downsampling (1m/5m/15m/1h)
- missing data shading and “gap detection” overlays

---

## 5) Backend API: Required New Admin Endpoints
All routes below should be under `prefix=/api/admin` and protected by `require_admin()`.

### 5.1 Auth / Admin Identity
- `GET /api/admin/me`
  - return admin identity, role, permissions

### 5.2 Users & Accounts
- `GET /api/admin/users`
  - Query params: `q`, `status`, `role`, `onboarding`, `page`, `page_size`, `sort`
- `GET /api/admin/users/{user_id}`
- `PUT /api/admin/users/{user_id}`
  - update profile fields (email/phone/name) and role
- `POST /api/admin/users/{user_id}/suspend`
  - body: `reason`, `until?`
- `POST /api/admin/users/{user_id}/unsuspend`
- `POST /api/admin/users/{user_id}/verify`
- `GET /api/admin/users/{user_id}/sessions`
  - return active sessions, last login, IP/user-agent
- `DELETE /api/admin/users/{user_id}/sessions/{session_id}`

Soft-delete conventions (MVP):
- Avoid hard deletes for users; use `is_active = false` and suspension fields.
- If a destructive action is required (e.g., removing a device), prefer `is_active = false` + audit event.

### 5.3 Farms
- `GET /api/admin/farms`
  - filters: `user_id`, `state`, `district`, `q`, `page`...
- `GET /api/admin/farms/{farm_id}`
- `PUT /api/admin/farms/{farm_id}`
  - edit locked-in metadata (size/location/soil_type) with audit
- `GET /api/admin/farms/{farm_id}/profile`
  - returns `FarmProfile` + `Farm` merged view

### 5.4 IoT Fleet: Devices
- `GET /api/admin/iot/devices`
  - filters: `farm_id`, `status`, `is_active`, `last_seen_before`, `page`
- `GET /api/admin/iot/devices/{device_id}`
- `PUT /api/admin/iot/devices/{device_id}`
  - set `status`, deactivate/reactivate, rename
- `GET /api/admin/iot/devices/{device_id}/uptime`
  - returns uptime %, last_seen, gap summary over a window

### 5.5 IoT Fleet: Telemetry
- `GET /api/admin/iot/telemetry`
  - query params: `farm_id`, `device_id?`, `from`, `to`, `metrics`, `downsample`
  - returns time-series points with consistent schema
- `GET /api/admin/iot/telemetry/latest`
  - query: `farm_id` or `device_id`
- `GET /api/admin/iot/telemetry/gaps`
  - query: `farm_id`/`device_id`, `from`, `to`, `expected_interval_s`

### 5.6 AI Economics & Agent Tracking
#### Usage (durable)
- `GET /api/admin/ai/usage/overview`
  - totals, last 24h, last 7d, cost estimates
- `GET /api/admin/ai/usage/by-user`
- `GET /api/admin/ai/usage/by-farm`
- `GET /api/admin/ai/usage/by-agent`
- `GET /api/admin/ai/usage/timeseries`
  - params: `from`, `to`, `group_by=hour|day`, `filters`

#### Interactions (quality control)
- `GET /api/admin/ai/interactions`
  - filters: `user_id`, `farm_id`, `agent_name`, `success`, `q`, `from`, `to`, `page`
- `GET /api/admin/ai/interactions/{interaction_id}`
- `POST /api/admin/ai/interactions/{interaction_id}/labels`
  - label quality issues, toxicity flags, etc.

#### Super Agent chat sessions
- `GET /api/admin/ai/chat/sessions`
- `GET /api/admin/ai/chat/sessions/{session_id}/history`
- `DELETE /api/admin/ai/chat/sessions/{session_id}`

#### Rate limits / errors
- `GET /api/admin/ai/events`
  - filters: `provider`, `event_type=rate_limit|error`, `from`, `to`

### 5.7 System Health & Database
- `GET /api/admin/system/health`
  - aggregate status: DB connectivity, Redis availability, ingestion status
- `GET /api/admin/system/api/latency`
  - p50/p95/p99, grouped by route
- `GET /api/admin/system/api/errors`
  - grouped by route/status code
- `GET /api/admin/system/db/tables`
  - row counts + estimated size
- `GET /api/admin/system/db/retention`
  - retention policy status (sensor readings partitions, pruning)

### 5.8 Dynamic Controls (Manipulations)
#### Sensor overrides
- `POST /api/admin/controls/sensors/override`
  - body: `farm_id`, `device_id?`, `metric`, `value`, `effective_from`, `effective_to`, `reason`
- `GET /api/admin/controls/sensors/overrides`
  - filters + pagination
- `DELETE /api/admin/controls/sensors/overrides/{override_id}`

#### Manual alerts
- `POST /api/admin/controls/alerts/send`
  - body: `target=users|farms|broadcast`, ids, `channel=sms|push|email|in_app`, `message`, `severity`
- `GET /api/admin/controls/alerts/history`

#### Prompt/agent configuration
- `GET /api/admin/controls/prompts`
- `POST /api/admin/controls/prompts`
- `PUT /api/admin/controls/prompts/{prompt_id}`
- `POST /api/admin/controls/prompts/{prompt_id}/publish`
- `POST /api/admin/controls/agents/{agent_name}/config`
  - e.g., temperature/max_tokens/tools enabled; stored in DB

#### Feature flags
- `GET /api/admin/controls/flags`
- `PUT /api/admin/controls/flags/{flag_key}`

### 5.9 Audit Log
- `GET /api/admin/audit/events`
  - filters: actor, target, action_type, date range
- `GET /api/admin/audit/events/{event_id}`

---

## 6) Database Additions / Changes Needed

### 6.1 Identity Consolidation / Mapping
Final decision: **Consolidate into a single canonical `users` table**.

Migration requirements:
- Update `farms.user_id` to FK -> `users.id`.
- Deprecate `auth_users` for application logic.

Optional temporary bridge (only during migration):
- `user_identity_map` (`user_id (users.id)` <-> `auth_user_id (auth_users.id)`)

### 6.2 Admin Roles & Permissions
If `users` is canonical:
- add `role` (enum: farmer/support/admin/auditor)
- add `suspended_at`, `suspended_until`, `suspend_reason`

Soft delete conventions (MVP standard):
- **Disable / suspend semantics** (preferred for accounts/devices): `is_active = false` plus `suspended_*` fields where applicable.
- **Logical delete semantics** (preferred for admin-created control-plane objects): add `deleted_at` (timestamp) + `deleted_by_admin_id`.
- Never hard-delete records that are relevant to security, billing, or investigations (audit events, LLM usage events).

### 6.3 Audit Logging (Mandatory)
**New table:** `admin_audit_events`
- `id`
- `actor_user_id`
- `action_type` (string)
- `target_type` (user/farm/device/prompt/...)
- `target_id` (string)
- `reason` (text)
- `before_json` (jsonb)
- `after_json` (jsonb)
- `request_id`, `ip_address`, `user_agent`
- `created_at`

### 6.4 IoT Monitoring Enhancements
**New table:** `device_heartbeat_events` (optional if last_seen is enough)
- `device_id`, `ts`, `status`, `latency_ms?`, `raw_payload?`

**New table:** `sensor_overrides`
- `id`, `farm_id`, `device_id?`, `metric`, `value`
- `effective_from`, `effective_to`
- `created_by_admin_id`, `reason`
- `created_at`

**Indexing:**
- `sensor_readings (farm_id, recorded_at desc)`
- `sensor_readings (device_id, recorded_at desc)`

Telemetry retention (MVP):
- Raw `sensor_readings` retention is **30 days**.
- For dashboards beyond 30 days, use rollups (e.g., `sensor_daily_summary`) and/or add hourly summaries.

Gap detection defaults (based on 15-minute cadence):
- `expected_interval_s`: **900**
- “warning” if no data for **> 2 intervals (~30 min)**
- “critical/offline” if no data for **> 6 intervals (~90 min)**

### 6.5 AI Usage Ledger (Durable LiteLLM-Compatible)
**New table:** `llm_usage_events`
- `id`
- `ts`
- `provider` (openai/gemini/anthropic/...)
- `model`
- `user_id?`, `farm_id?`
- `agent_name?`, `session_id?`
- `prompt_tokens`, `completion_tokens`, `total_tokens`
- `cost_usd` (numeric)
- `latency_ms`
- `status` (success/error)
- `error_type?`, `error_message?`
- `request_id` / `trace_id`

**Why separate from `agent_interactions`:**
- one agent interaction may do multiple LLM calls
- LiteLLM provides granular usage per call

### 6.6 Agent Interaction Labeling
**New table:** `agent_interaction_labels`
- `id`, `interaction_id`, `label`, `notes`, `created_by_admin_id`, `created_at`

### 6.7 System Metrics (if not using external monitoring)
**New table:** `api_request_metrics` (aggregated or raw)
- `id`, `ts`, `method`, `path_template`, `status_code`, `duration_ms`, `request_id`

If you adopt Prometheus/Otel, keep DB minimal and consume metrics externally.

---

## 7) Edge Cases & Decisions You Must Make Before Coding

### 7.1 Canonical Identity (Resolved)
- Canonical identity is `users`.
- `farms.user_id` must reference `users.id`.

### 7.2 “Locked-in” Farm Data
- Which fields are editable by admin vs immutable?
- Do edits create a new version (recommended) or overwrite?

### 7.3 IoT Data Integrity
- When admin overrides a metric, do you:
  - write a synthetic reading into `sensor_readings`, or
  - overlay via `sensor_overrides` at query time (recommended), or
  - store both and expose “effective value” + “raw value”?

### 7.4 Time-Series Scale
- Expected telemetry volume per farm/device?
- Retention window for raw readings is **30 days**.
- Do you need rollups (hourly/daily summaries) for long-range charts?

Downsampling defaults (based on 15-minute cadence):
- `downsample=15m` for 24h–7d views
- `downsample=1h` for 7d–30d views
- rollups required beyond 30d (raw data not available)

### 7.5 AI Costing
- Providers/models will be used via LiteLLM (Gemini now), and must support OpenAI.
- Do you require **exact billing** (provider pricing tables) or estimates?
- How to attribute cost: per user, per farm, per agent, per session?

### 7.6 Privacy & Compliance
- Should admins be able to view full user prompts/responses always?
- Do you need redaction of PII or secrets in logs?

### 7.7 Operations: Messaging/Alerts
- Which channels exist today (SMS provider, email, push)?
- Do you need templates, localization, scheduling, acknowledgements?

### 7.8 Safety Controls
- Require 2-person approval for destructive actions (delete user/data)?
- Require “break-glass” mode to override critical settings?

---

## 8) Recommended Implementation Phases

### Phase 1 (MVP Admin: Read-Only + Safe Actions)
- Users/farms list & detail
- IoT device status + latest reading
- Agent interactions list (from `agent_interactions`)
- Basic admin auth + audit log

### Phase 2 (Economics + Telemetry Explorer)
- Durable `llm_usage_events`
- Telemetry time-range explorer with downsampling
- Uptime/gap detection endpoints

### Phase 3 (Dynamic Controls)
- Sensor overrides overlay
- Prompt registry + publish workflow
- Manual alerts with delivery receipts

---

## 9) Non-Negotiable Production Requirements
- **Server-side RBAC** for all `/api/admin/*`
- **Immutable audit log** for every admin write
- **Pagination everywhere**
- **Consistent tenant identifiers** (resolve `user_id`/`farm_id` properly)
- **Performance controls** for telemetry queries (downsampling + indexes + retention)

---

## 10) Open Questions (Answer These Before We Start Coding)
- Confirm that **One User = One Farm** is enforced for MVP (unique constraint + service assumptions).
- Should support staff have partial access (and what must be masked/redacted in prompts/responses)?
- For AI economics: do you want **exact provider pricing** (by model + date) or a stable estimate table?
- For “dynamic controls”: do prompt/config changes require versioning + approval workflow, or can admins publish instantly?
