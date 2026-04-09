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
│  └─ Real-time SSE timeline                                       │
├──────────────────────────────────────────────────────────────────┤
│  API Layer (FastAPI / Bearer Auth)                                │
│  ├─ /v1/approvals, /v1/events, /v1/settings, /v1/goals ...      │
│  └─ Global auth middleware (require_auth)                         │
├──────────────────────────────────────────────────────────────────┤
│  DelegateRuntime            │  Event Bus (in-memory pub/sub)     │
│  ├─ Flexible scheduler      │  └─ SSE broadcast to frontend     │
│  ├─ Per-delegate intervals   │                                    │
│  └─ One-shot tasks           │                                    │
├──────────────────────────────────────────────────────────────────┤
│  Delegates (pipeline stages)                                     │
│  ├─ Recruiter: ingest → extract → score → policy → draft → act  │
│  └─ Calendar: parse → find-slots → propose → act                │
├──────────────────────────────────────────────────────────────────┤
│  Skills Layer                │  Policy Engine                     │
│  ├─ LLM Client (tiered)     │  ├─ YAML trust zones               │
│  ├─ Email (MS Graph / mock) │  ├─ Allowlist (SQLite-backed)      │
│  ├─ Telegram notifications  │  └─ Simulator (test before commit) │
│  └─ Company enricher        │                                    │
├──────────────────────────────────────────────────────────────────┤
│  Memory (SQLite via aiosqlite)                                   │
│  ├─ Tier 1: Memories (always in LLM context)                    │
│  ├─ Tier 2: Scratchpad (titles in context, body on-demand)      │
│  └─ Tier 3: Database (structured — opportunities, scores, logs) │
└──────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
backend/
├── main.py                     # FastAPI app, lifespan, CORS
├── config/
│   ├── settings.py             # Pydantic settings from .env
│   └── delegate_policies/      # YAML trust zone definitions
│       ├── recruiter.yaml
│       └── calendar.yaml
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
│   └── calendar/               # Calendar delegate
│       ├── pipeline.py
│       └── conflict_checker.py
├── memory/
│   ├── graph.py                # Three-tier knowledge (memories, scratchpad, database)
│   └── models.py               # Pydantic models for memory entities
├── policy/
│   ├── engine.py               # PolicyEngine (check, can_auto_act, should_block)
│   ├── models.py               # TrustZone, DelegationPolicy, ActionPermission
│   ├── loader.py               # Load YAML policies
│   ├── simulator.py            # Test policy changes on historical data
│   └── allowlist.py            # Sender allowlist (SQLite-backed, env-seeded)
├── runtime/
│   ├── kernel.py               # DelegateRuntime: scheduler, pause/resume, one-shot
│   └── event_bus.py            # In-memory pub/sub with SSE broadcast
├── skills/
│   ├── llm_client.py           # Tiered LLM (cheap/heavy) with usage tracking
│   ├── email/                  # Email ingestion (MS Graph + mock)
│   ├── calendar/               # Calendar provider abstraction
│   ├── company/enricher.py     # 3-tier: JD parsing → Wikipedia → Apollo
│   └── notifications/
│       ├── digest_sender.py    # Daily/weekly digest
│       └── telegram.py         # Telegram Bot API notifications
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
| **API Auth** | Bearer token (`API_KEY` env var). All endpoints require auth except `/health`, `/docs`, SSE stream. Dev mode passthrough when unset. |
| **Allowlist** | SQLite-backed sender allowlist. Seeded from `ALLOWLIST` env var. LLM cannot modify. |
| **Policy Engine** | Trust zones gate what delegates can auto-act on. `block` zone is absolute. |
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

---

## Notifications

| Channel | When | Implementation |
|---------|------|----------------|
| **SSE** | Every pipeline event | `event_bus.py` → frontend `use-event-stream` hook |
| **Telegram** | New approvals, high matches (≥0.80), auto-declines, daily digest | `skills/notifications/telegram.py` via Bot API |
| **Email digest** | Daily/weekly summary | `skills/notifications/digest_sender.py` |

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
OPENAI_API_KEY=sk-...
API_KEY=your-bearer-token          # Optional in dev
TELEGRAM_BOT_TOKEN=123:ABC...      # Optional
TELEGRAM_CHAT_ID=123456789         # Optional
ALLOWLIST=recruiter@example.com,trusted@corp.com  # Optional, comma-separated
```
