# Architecture — Cadbury Personal Delegates Network

> Single source of truth for how the system is built. Update this file with every structural change.

---

## Overview

Cadbury is a **policy-driven AI delegate network** where specialized agents handle distinct slices of your life — with strict, auditable boundaries on what they can decide, act on, and spend.

```
┌──────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14 / App Router / Zustand / SSE)              │
│  ├─ Approval Queue (approve / edit / reject)                     │
│  ├─ Scoring Dashboard (5-factor breakdown)                       │
│  ├─ Policy Simulator (test changes on historical data)           │
│  ├─ Cross-Delegate Digest (unified view across all 7 delegates) │
│  └─ Real-time SSE timeline                                       │
├──────────────────────────────────────────────────────────────────┤
│  API Layer (FastAPI / Bearer Auth)                                │
│  ├─ /v1/approvals, /v1/events, /v1/settings, /v1/goals ...      │
│  ├─ /v1/comms, /v1/finance, /v1/shopping, /v1/learning, /v1/health│
│  ├─ /v1/observability (system health, metrics)                   │
│  └─ Global auth middleware (require_auth)                         │
├──────────────────────────────────────────────────────────────────┤
│  DelegateRuntime            │  Event Bus (in-memory pub/sub)     │
│  ├─ Flexible scheduler      │  └─ SSE broadcast to frontend     │
│  ├─ Per-delegate intervals   │                                    │
│  └─ One-shot tasks           │  Coordinator (cross-delegate)     │
│                              │  └─ 3 event handlers (dispatch)   │
├──────────────────────────────────────────────────────────────────┤
│  Delegates (7 pipeline-based agents)                             │
│  ├─ Recruiter: ingest → extract → score → policy → draft → act  │
│  ├─ Calendar:  parse → find-slots → propose → act               │
│  ├─ Comms:     ingest → classify → prioritize → route → draft → act│
│  ├─ Finance:   discover → track → alert → recommend → act       │
│  ├─ Shopping:  watch → compare → alert → recommend → act        │
│  ├─ Learning:  assess → plan → track → nudge → report           │
│  └─ Health:    schedule → track → remind → alert → act          │
├──────────────────────────────────────────────────────────────────┤
│  Skills Layer                │  Policy Engine                     │
│  ├─ LLM Client (tiered)     │  ├─ YAML trust zones (7 policies) │
│  ├─ Email (MS Graph / mock) │  ├─ Allowlist (SQLite-backed)      │
│  ├─ Multi-channel notifs     │  └─ Simulator (test before commit) │
│  │  (Telegram, WhatsApp,     │                                    │
│  │   Slack, SMS)             │  Observability                     │
│  ├─ Company enricher        │  ├─ In-memory metrics (p50/p95)    │
│  └─ Context compaction      │  └─ Per-delegate health tracking   │
├──────────────────────────────────────────────────────────────────┤
│  Memory (SQLite via aiosqlite)                                   │
│  ├─ Tier 1: Memories (always in LLM context)                    │
│  ├─ Tier 2: Scratchpad (titles in context, body on-demand)      │
│  └─ Tier 3: Database (structured — 20+ domain tables)           │
└──────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
backend/
├── main.py                     # FastAPI app, lifespan, CORS
├── config/
│   ├── settings.py             # Pydantic settings from .env
│   └── delegate_policies/      # YAML trust zone definitions (7 policies)
│       ├── recruiter.yaml
│       ├── calendar.yaml
│       ├── comms.yaml
│       ├── finance.yaml
│       ├── shopping.yaml
│       ├── learning.yaml
│       └── health.yaml
├── middleware/
│   └── auth.py                 # Bearer token auth (global dependency)
├── api/routes/                 # All REST endpoints
├── delegates/
│   ├── recruiter/              # 6-stage pipeline
│   │   ├── pipeline.py         # PipelineContext + stage orchestration
│   │   ├── scorer.py           # Deterministic 5-factor scoring
│   │   ├── drafter.py          # LLM-powered reply drafting
│   │   ├── pattern_detector.py # 5 pattern detectors (staffing agency, etc.)
│   │   └── trust_scorer.py     # Feedback-based trust adjustment
│   ├── calendar/               # Calendar delegate
│   │   ├── pipeline.py
│   │   └── conflict_checker.py
│   ├── comms/                  # Communications delegate
│   │   └── pipeline.py         # 6-stage: ingest → classify → prioritize → route → draft → act
│   ├── finance/                # Finance delegate
│   │   └── pipeline.py         # 5-stage: discover → track → alert → recommend → act
│   ├── shopping/               # Shopping delegate
│   │   └── pipeline.py         # 5-stage: watch → compare → alert → recommend → act
│   ├── learning/               # Learning delegate
│   │   └── pipeline.py         # 5-stage: assess → plan → track → nudge → report
│   └── health/                 # Health delegate
│       └── pipeline.py         # 5-stage: schedule → track → remind → alert → act
├── memory/
│   ├── graph.py                # Three-tier knowledge (memories, scratchpad, database)
│   └── models.py               # Pydantic models for memory entities
├── policy/
│   ├── engine.py               # PolicyEngine (check, can_auto_act, should_block)
│   ├── models.py               # TrustZone, DelegationPolicy, ActionPermission
│   ├── loader.py               # Load YAML policies
│   ├── simulator.py            # Test policy changes on historical data
│   ├── allowlist.py            # Sender allowlist (SQLite-backed, env-seeded)
│   └── budget.py               # Per-delegate LLM budget enforcement
├── runtime/
│   ├── kernel.py               # DelegateRuntime: scheduler, pause/resume, one-shot
│   ├── event_bus.py            # In-memory pub/sub with SSE broadcast
│   └── coordinator.py          # Cross-delegate event routing (3 handlers)
├── skills/
│   ├── llm_client.py           # Tiered LLM (cheap/heavy) with usage tracking + budget gating
│   ├── email/                  # Email ingestion (MS Graph delegated + client-creds + mock)
│   ├── calendar/               # Calendar provider abstraction
│   │   ├── provider.py         # CalendarProvider ABC
│   │   ├── mock.py             # Mock for development
│   │   ├── google.py           # Google Calendar (OAuth2 delegated)
│   │   ├── msgraph.py          # MS Graph Calendar (OAuth2 delegated)
│   │   └── multi.py            # Multi-provider merger (combines all connected providers)
│   ├── company/enricher.py     # 3-tier: JD parsing → Wikipedia → Apollo
│   ├── auth/                   # OAuth2 token management
│   │   └── token_store.py      # Encrypted at-rest token storage (Fernet + SQLite)
│   ├── actions/                # Post-approval action executors
│   │   └── __init__.py         # execute_send_email (picks provider, sends, updates status)
│   ├── channels/               # Multi-channel messaging
│   │   └── providers.py        # Telegram, WhatsApp, Slack, SMS providers
│   ├── context_compaction.py   # LLM context window management (checkpoint/compact/restore)
│   └── notifications/
│       ├── digest_sender.py    # Daily/weekly/cross-delegate digest
│       └── telegram.py         # Telegram Bot API notifications
├── observability/
│   └── metrics.py              # In-memory metrics, pipeline timers, delegate health
└── tests/

frontend/
├── src/
│   ├── app/                    # Next.js 14 App Router pages
│   │   ├── approvals/          # Approval queue UI
│   │   ├── calendar/           # Calendar view
│   │   ├── delegates/          # Delegate management
│   │   ├── digest/             # Daily digest
│   │   ├── goals/              # Career goals editor
│   │   ├── settings/           # Policy / settings UI
│   │   └── opportunities/      # Opportunity explorer
│   ├── components/             # Shared UI components
│   ├── hooks/                  # use-auto-save, use-event-stream, etc.
│   ├── lib/                    # API clients, utilities
│   └── stores/                 # Zustand state stores
```

---

## Core Concepts

### Deterministic Scoring (Cadbury's Moat)

Every recruiter email gets a reproducible numeric score — no LLM involved:

| Factor | Weight | Source |
|--------|--------|--------|
| Compensation | 32% | Extracted from email vs. user target |
| Role fit | 27% | Title/seniority match against goals |
| Location | 18% | Remote preference, geo match |
| Criteria match | 13% | Specific skills, technologies, dealbreakers |
| Company | 10% | Stage, industry, avoid-list check |

**Dealbreakers** are hard blocks: if triggered, score = 0.0 regardless of other dimensions.

### Policy-as-Code

Delegation policies are YAML files with trust zones:

```yaml
trust_zones:
  auto:    # Act without human approval
    - score >= 0.80 AND action == "pre-block calendar"
  review:  # Create approval item for human
    - action == "send email"
  block:   # Never allow
    - action == "commit to salary"
```

The Policy Simulator lets you test changes on historical data before committing.

### Three-Tier Knowledge

| Tier | Storage | In LLM Context | Example |
|------|---------|-----------------|---------|
| **Memories** | `memories` table | Always (full text) | Career goals, dealbreakers, preferences |
| **Scratchpad** | `scratchpad` table | Titles only (body on-demand) | Recruiter interaction history, company notes |
| **Database** | Domain tables | Never (queried explicitly) | Opportunities, scores, decision logs |

This prevents context blowout as data accumulates while keeping critical knowledge always available.

### DelegateRuntime (Scheduler)

The runtime manages background task execution:

- **Recurring jobs**: Per-delegate configurable intervals (default: 15 min for recruiter email poll)
- **One-shot tasks**: Schedule future actions (e.g., "follow up on this opportunity in 3 days")
- **Pause/resume**: Per-delegate control without stopping the whole system
- **Status API**: Monitor active jobs, paused delegates, pending one-shots

### Event Bus (SSE)

All pipeline stages emit `DelegateEvent` objects into an in-memory event bus. The frontend subscribes via SSE (`/v1/events/stream`) for real-time updates. Events are also persisted to the `delegate_events` table for replay/audit.

---

## Security Model

| Layer | Mechanism |
|-------|-----------|
| **API Auth** | Bearer token (`API_KEY` env var). All endpoints require auth except `/health`, `/docs`, SSE stream, OAuth callbacks. Dev mode passthrough when unset. |
| **OAuth2** | PKCE authorization code flow for Microsoft (email + calendar) and Google (calendar). Tokens encrypted at rest via Fernet (derived from `SECRET_KEY`). |
| **Allowlist** | SQLite-backed sender allowlist. Seeded from `ALLOWLIST` env var. LLM cannot modify. |
| **Policy Engine** | Trust zones gate what delegates can auto-act on. `block` zone is absolute. |
| **Budget Enforcement** | Per-delegate daily token/cost limits. LLM calls blocked when over budget. Auto-pause delegate. Daily reset at midnight UTC. |
| **LLM Isolation** | API keys and secrets never in LLM context. Tiered model routing (cheap for extraction, heavy for drafting). |
| **Audit Trail** | Every delegate action emits a `DelegateEvent`. Every human decision logged in `decision_log`. Full replay capability. |

---

## Database Schema (SQLite)

Primary tables in `data/delegates.db`:

| Table | Purpose |
|-------|---------|
| `career_goals` | User's target role, comp, location, dealbreakers |
| `recruiter_contacts` | Known recruiter profiles and history |
| `job_opportunities` | Extracted + scored opportunities |
| `approval_items` | Pending human approval queue |
| `delegate_events` | Immutable audit trail of all pipeline events |
| `decision_log` | Human approve/reject/edit decisions with context |
| `calendar_events` | Calendar holds and scheduled events |
| `notifications` | Notification queue |
| `policy_overrides` | Per-opportunity policy exceptions |
| `memories` | Tier 1 knowledge — always in LLM context |
| `scratchpad` | Tier 2 knowledge — titles in context, body on-demand |
| `allowlist` | Approved senders/identifiers by service |
| `oauth_tokens` | Encrypted OAuth2 tokens per provider |
| `delegate_budgets` | Per-delegate daily token/cost limits and usage |
| `comms_messages` | Triaged messages across all channels |
| `transactions` | Financial transactions (income, expense, recurring) |
| `subscriptions` | Tracked subscriptions with renewal/cancellation status |
| `watch_items` | Shopping price-watch list with target prices |
| `learning_paths` | Structured learning paths toward career goals |
| `health_routines` | Daily/weekly health routines with streak tracking |
| `health_appointments` | Scheduled and overdue health appointments |

---

## Delegates

### Recruiter
6-stage pipeline: **Ingest → Extract → Score → Policy → Draft → Act**
- Deterministic 5-factor scoring (comp, role fit, location, criteria, company)
- Pattern detection (staffing agencies, mass campaigns, etc.)
- LLM drafts replies; sends require human approval

### Calendar
4-stage pipeline: **Parse → Find-Slots → Propose → Act**
- Multi-provider: Google Calendar + Outlook via OAuth2
- Conflict checking across merged calendars
- Pre-blocks interview slots for high-match opportunities

### Comms (Phase 3)
6-stage pipeline: **Ingest → Classify → Prioritize → Route → Draft → Act**
- Deterministic classification via keyword/pattern matching (importance, spam signals)
- Priority routing: archive spam, batch low-priority, surface + draft for urgent
- LLM-optional reply drafting; all sends gated by approval

### Finance (Phase 3)
5-stage pipeline: **Discover → Track → Alert → Recommend → Act**
- Auto-categorization via keyword matching (groceries, rent, utilities, etc.)
- Recurring charge detection with interval analysis
- Spending spike alerts (3× rolling average)
- Subscription audit: flags unused subscriptions (>60 days inactive)

### Shopping (Phase 4)
5-stage pipeline: **Watch → Compare → Alert → Recommend → Act**
- Price history tracking with drop detection (≥10%)
- Target price matching and below-average buy recommendations
- **Never auto-purchases** — all buy actions require explicit approval

### Learning (Phase 4)
5-stage pipeline: **Assess → Plan → Track → Nudge → Report**
- Deterministic skill gap detection via `SKILL_CLUSTERS` matched against career goals
- LLM-optional resource suggestions for learning paths
- Progress tracking with stale-path nudges (3+ days inactive)

### Health (Phase 4)
5-stage pipeline: **Schedule → Track → Remind → Alert → Act**
- Routine streak tracking with frequency-based reminders (daily/weekly)
- Overdue appointment detection and missed-routine alerts (3+ days)
- **Never auto-books** — appointment scheduling requires approval

---

## Context Compaction

`skills/context_compaction.py` manages LLM context window limits:

1. **`should_compact()`** — estimates token count and returns `True` when budget is 80% consumed
2. **`checkpoint_messages()`** — saves full conversation to SQLite for crash recovery
3. **`compact_messages()`** — splits messages into system / middle / recent, uses LLM to summarize the middle section, preserves the last 3 messages intact

This prevents context blowout for long-running delegate conversations while maintaining critical recent context.

---

## Observability

`observability/metrics.py` provides in-memory system monitoring:

| Feature | Detail |
|---------|--------|
| **Timing metrics** | `record_timing()` with p50/p95/p99 summaries |
| **Counters** | `increment_counter()` for event/error counts |
| **PipelineTimer** | Context manager auto-records stage durations |
| **Delegate health** | Per-delegate status (healthy/degraded/unhealthy), error rates, last-active times |
| **System health API** | `/v1/observability/health` returns all delegates, budgets, pipeline durations |

---

## Cross-Delegate Coordination

Events from one delegate can trigger actions in another via `runtime/coordinator.py`. The coordinator uses a dispatch table pattern, listening to all events on the bus:

| Trigger | Source → Target | Action |
|---------|-----------------|--------|
| `CALENDAR_PREBLOCK_REQUESTED` | Recruiter → Calendar | Auto-run calendar pipeline to find interview slots |
| `SUBSCRIPTION_FLAGGED` | Finance → Comms | Draft cancellation email for flagged subscription |
| `HEALTH_APPOINTMENT` | Health → Calendar | Block time on calendar for the appointment |

---

## Notifications & Multi-Channel Messaging

All outbound messaging flows through `skills/channels/providers.py`, which provides a unified `ChannelProvider` ABC.

| Channel | Provider | Configuration | Implementation |
|---------|----------|---------------|----------------|
| **SSE** | Built-in | Always on | `event_bus.py` → frontend `use-event-stream` hook |
| **Telegram** | Bot API | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | `skills/notifications/telegram.py` + `channels/providers.py` |
| **WhatsApp** | Meta Cloud API v18.0 | `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | `channels/providers.py` |
| **Slack** | Web API (chat.postMessage) | `SLACK_BOT_TOKEN`, `SLACK_DEFAULT_CHANNEL` | `channels/providers.py` |
| **SMS** | Twilio REST API | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` | `channels/providers.py` |
| **Email digest** | Per-delegate or cross-delegate | Always on | `skills/notifications/digest_sender.py` |

`send_to_all_configured_channels()` broadcasts to every channel with valid credentials.

---

## LLM Usage

| Tier | Model | Used For | Cost |
|------|-------|----------|------|
| **Cheap** | gpt-4o-mini | JSON extraction, classification, pattern detection | ~$0.15/1M tokens |
| **Heavy** | gpt-4o | Reply drafting, complex analysis | ~$5/1M tokens |

Usage is tracked per-call with `_UsageStats` (total tokens, calls by tier). Accessible via `get_usage_stats()`.

---

## Running

```bash
# Development
docker compose up

# Or directly:
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
```

Environment variables (`.env`):
```
# Core
OPENAI_API_KEY=sk-...
SECRET_KEY=change-me-in-production     # Used for token encryption
API_KEY=your-bearer-token              # Optional in dev

# Microsoft Graph (email + calendar)
MSGRAPH_CLIENT_ID=...
MSGRAPH_CLIENT_SECRET=...              # Optional for PKCE-only flow
MSGRAPH_TENANT_ID=...                  # Or "common" for multi-tenant

# Google Calendar
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Notifications — Telegram
TELEGRAM_BOT_TOKEN=123:ABC...          # Optional
TELEGRAM_CHAT_ID=123456789             # Optional

# Notifications — WhatsApp (Meta Cloud API)
WHATSAPP_ACCESS_TOKEN=...              # Optional
WHATSAPP_PHONE_NUMBER_ID=...           # Optional
WHATSAPP_DEFAULT_TO=...                # Optional

# Notifications — Slack
SLACK_BOT_TOKEN=xoxb-...               # Optional
SLACK_DEFAULT_CHANNEL=#general         # Optional

# Notifications — SMS (Twilio)
TWILIO_ACCOUNT_SID=AC...               # Optional
TWILIO_AUTH_TOKEN=...                   # Optional
TWILIO_FROM_NUMBER=+1...               # Optional
SMS_DEFAULT_TO=+1...                    # Optional

# Security
ALLOWLIST=recruiter@example.com,trusted@corp.com  # Optional, comma-separated
```

---

## Production Deployment

### Docker Compose (Production)

```bash
docker compose -f docker-compose.prod.yml up --build
```

`docker-compose.prod.yml` uses:
- Multi-stage frontend build (`frontend/Dockerfile.prod`) with Next.js `standalone` output
- No volume mounts (immutable containers)
- Environment variables from `.env` file

### CI/CD

`.github/workflows/ci.yml` runs on every push/PR:
1. **Lint** — Ruff check on backend Python
2. **Test** — pytest on backend tests
3. **Type-check** — `tsc --noEmit` on frontend
4. **Docker build** — validates both images build successfully
