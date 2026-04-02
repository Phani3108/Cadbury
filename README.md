# 🧠 Personal Delegates Network

A consumer-facing AI layer where specialized delegates handle distinct slices of your life — with strict boundaries on what they can decide, act on, and spend.

---

## 🤔 Why not just a personal assistant?

Generic assistants are forgettable. Delegates with **strict roles** are easier to trust.

**The difference:**
- ✅ Each delegate has a defined scope — it doesn't drift
- ✅ You control autonomy per domain via a policy (not a prompt)
- ✅ Every AI decision is logged, explained, and searchable
- ✅ Trust builds over time — delegates learn your patterns
- ✅ Policy Simulator lets you test changes on historical data before committing

---

## 🤖 The Delegates

| Delegate | Status | What it handles |
|----------|--------|-----------------|
| 🔍 **Recruiter** | `Active` | Screens inbound recruiter emails, scores against your goals, drafts replies, auto-declines low matches |
| 📅 **Calendar** | `Active` | Manages scheduling, interview holds, conflict checking, slot proposals |
| 💰 **Finance** | `Coming Soon` | Expense tracking, subscription monitoring |
| 💬 **Comms** | `Coming Soon` | Filters inbound messages, drafts routine replies |

---

## 🔁 Recruiter Delegate — How it works

```
Email arrives
  ↓ Stage 1: Ingest — fetch + identify recruiter signals + thread tracking
  ↓ Stage 2: Extract — LLM parses company, role, comp, location (with thread dedup)
  ↓ Stage 3: Score — comp (32%) + role (27%) + location (18%) + criteria (13%) + company (10%)
  ↓ Stage 4: Policy — check against delegation policy YAML + auto-decline threshold
  ↓ Stage 5: Draft — generate engage / hold / decline reply (uses full JD text)
  ↓ Stage 6: Act — auto-decline low scores OR create ApprovalItem → you approve/edit/reject
```

**Key features:**
- Dealbreakers are hard blocks — score = 0.0 regardless of other dimensions
- Auto-decline for very low scores (< 0.25) — sends polite decline without requiring approval
- Thread tracking — follow-up emails update existing opportunities instead of creating duplicates
- Company scoring — checks avoid list, matches company stage and industry preferences
- High-match opportunities (≥ 0.80) automatically request calendar pre-blocks for interviews

---

## 📅 Calendar Delegate — How it works

```
Calendar request received (from recruiter delegate or manual)
  ↓ Stage 1: Parse — extract scheduling requirements and preferences
  ↓ Stage 2: Find Slots — check availability, skip conflicts, respect working hours
  ↓ Stage 3: Propose — generate time slot proposals
  ↓ Stage 4: Act — create approval item or auto-book based on policy
```

---

## 🧪 Policy Simulator

Inspired by sandbox testing approaches — replay historical data through hypothetical policy thresholds before committing changes.

- **Interactive sliders** for engagement threshold, auto-decline floor, and auto-decline threshold
- **Before/After comparison** showing how each opportunity would be classified differently
- **Impact metrics** — time saved, approval reduction percentage, changed outcomes
- **Debounced live preview** as you adjust sliders (~500ms)

Access at `/delegates/recruiter/policy/simulator`

---

## 🔔 Notification System

- **In-app bell** with unread count badge in the topbar
- **Real-time push** via Server-Sent Events (SSE)
- **Notification types**: new approvals, high-match opportunities, auto-actions, digest ready
- Notifications created automatically during pipeline processing

---

## 📊 Daily/Weekly Digest

- **Summary generation** from pipeline activity, approvals, and opportunity data
- **Highlights** — key actions taken, notable opportunities
- **Action items** — pending reviews, expiring approvals
- **Stats dashboard** — processed count, auto-decline rate, average scores, time saved

Access at `/digest`

---

## 🧠 Learning System

The delegate gets smarter over time by detecting patterns in your decisions:

| Pattern | What it detects | Suggested action |
|---------|----------------|------------------|
| **Sector rejection** | >80% reject rate for a keyword across ≥5 opportunities | Add to dealbreakers |
| **Comp drift** | Approved opportunities consistently above min comp floor by 25%+ | Raise minimum compensation |
| **Recruiter quality** | 100% rejection rate for a recruiter across ≥3 opportunities | Add company to avoid list |
| **Score calibration** | 30%+ of approved opportunities scored below engagement threshold | Lower engagement threshold |
| **Approval backlog** | Growing queue of pending decisions | Enable auto-decline for low scores |

Suggestions can be applied with one click — updating your career goals or policy overrides automatically.

---

## 🏗️ Architecture

```
Redis Streams (event log)
    ↓
DelegateRuntime (asyncio event loop)
    ↓
┌─ RecruiterPipeline (6-stage) ──→ TrustScorer, PatternDetector, CompanyEnricher
└─ CalendarPipeline (4-stage)  ──→ ConflictChecker, SlotFinder
    ↓
PolicyEngine ← recruiter.yaml / calendar.yaml + policy_overrides DB
PolicySimulator ← replay historical data through hypothetical thresholds
MemoryGraph ← SQLite (CareerGoals, Opportunities, DecisionLog, Calendar, Notifications)
    ↓
ApprovalQueue → FastAPI + SSE (typed events) → Next.js frontend
    ↓
NotificationSystem → In-app bell + SSE push
DigestSender → Daily/weekly summaries
```

**Stack:**
- 🐍 Backend: FastAPI, aiosqlite, OpenAI SDK, Pydantic v2
- ⚛️ Frontend: Next.js 16, TypeScript, Tailwind, Zustand, Radix UI
- 🗄️ DB: SQLite with migration-safe schema evolution
- 📡 Real-time: Server-Sent Events (SSE) with typed event envelopes and exponential backoff

---

## 📁 Project Structure

```
├── backend/
│   ├── delegates/
│   │   ├── recruiter/
│   │   │   ├── pipeline.py           # 6-stage pipeline with auto-decline + thread tracking
│   │   │   ├── scorer.py             # 5-dimension opportunity scorer (comp, role, location, criteria, company)
│   │   │   ├── drafter.py            # Response drafter (engage/hold/decline)
│   │   │   ├── trust_scorer.py       # Recruiter trust scoring (match quality, comp disclosure, approval rate)
│   │   │   ├── pattern_detector.py   # Decision pattern detection with actionable suggestions
│   │   │   └── prompts/              # LLM prompts (extract, score, draft)
│   │   └── calendar/
│   │       ├── pipeline.py           # 4-stage calendar pipeline
│   │       └── conflict_checker.py   # Slot finding and conflict resolution
│   ├── policy/
│   │   ├── engine.py                 # PolicyEngine → TrustZone (auto/review/block) + auto-decline
│   │   ├── simulator.py             # Historical replay through hypothetical thresholds
│   │   └── loader.py                # YAML → DelegationPolicy
│   ├── config/delegate_policies/
│   │   ├── recruiter.yaml           # Recruiter delegation boundaries
│   │   └── calendar.yaml            # Calendar delegation boundaries
│   ├── skills/
│   │   ├── llm_client.py            # Tiered model routing (cheap/heavy)
│   │   ├── email/                   # EmailProvider ABC + Mock + MS Graph OAuth2
│   │   ├── calendar/                # CalendarProvider ABC + Mock
│   │   ├── company/                 # Company enrichment (JD parsing, Wikipedia, Apollo)
│   │   └── notifications/           # Digest generation and delivery
│   ├── memory/
│   │   ├── models.py                # All data models (Opportunities, Calendar, Notifications, etc.)
│   │   └── graph.py                 # SQLite persistence + MemoryGraph class
│   ├── api/routes/                  # FastAPI routes (delegates, approvals, calendar, digest, notifications, contacts, events, goals, memory)
│   └── runtime/                     # Asyncio scheduler, typed event bus (SSE), delegate kernel
│
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                 # Dashboard
│   │   ├── goals/                   # Goals Editor (auto-save, real-time preview)
│   │   ├── approvals/               # Approval Inbox (keyboard shortcuts, optimistic updates)
│   │   ├── opportunities/           # Opportunity list + detail with match breakdown
│   │   ├── calendar/                # Calendar management (events, slots, booking)
│   │   ├── digest/                  # Daily/weekly digest view
│   │   └── delegates/[id]/
│   │       ├── page.tsx             # Delegate detail (pipeline, timeline, learning)
│   │       ├── policy/              # Policy editor (TrustThermostat, RuleCards)
│   │       └── policy/simulator/    # Policy simulator (interactive sliders, before/after)
│   ├── src/components/
│   │   ├── approvals/               # ApprovalCard, ApprovalDetail, DraftEditor, ApprovalActions
│   │   ├── goals/                   # GoalSection, TagInput, GoalsSidebar
│   │   ├── layout/                  # AppShell, Sidebar, Topbar
│   │   ├── scoring/                 # ScoreBadge, MatchBreakdown
│   │   └── shared/                  # CommandPalette, ConnectionBanner, NotificationBell, EmptyState
│   └── src/stores/                  # Zustand: events, approvals, goals, notifications, UI
│
├── docker-compose.yml               # Redis + backend + frontend
└── README.md
```

---

## 🚀 Run locally

**Prerequisites:** Python 3.11+, Node 22+, Docker (for Redis)

```bash
# Backend
cd backend
pip install -e ".[dev]"
docker run -d -p 6379:6379 redis:7-alpine
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

**Trigger the recruiter pipeline (no OpenAI key needed):**
```bash
curl -X POST http://localhost:8000/v1/delegates/recruiter/run
# → processes 3 mock recruiter emails, scores them, auto-declines low matches, creates approval items

curl http://localhost:8000/v1/approvals              # pending approval items
curl http://localhost:8000/v1/memory/opportunities   # scored opportunities
curl http://localhost:8000/v1/events                 # full event trace
curl http://localhost:8000/v1/notifications          # notifications from pipeline
curl http://localhost:8000/v1/digest?period=daily    # daily digest report
curl http://localhost:8000/v1/calendar/events        # calendar events
curl http://localhost:8000/v1/contacts               # recruiter contacts
```

The background scheduler also runs the pipeline automatically every 15 minutes (configurable via `EMAIL_POLL_INTERVAL_SECONDS` in `.env`).

---

## 🖥️ Frontend Pages

| Page | URL | Description |
|------|-----|-------------|
| **Dashboard** | `/` | Overview with live delegate stats |
| **Approval Inbox** | `/approvals` | Split view, keyboard shortcuts (`j`/`k`/`a`/`r`/`e`/`s`), optimistic updates, undo toasts |
| **Goals Editor** | `/goals` | Set roles, comp, location, dealbreakers — auto-saves with 500ms debounce |
| **Opportunities** | `/opportunities` | All scored opportunities with match breakdowns |
| **Calendar** | `/calendar` | View events, find available slots, book/cancel meetings |
| **Digest** | `/digest` | Daily/weekly summary with stats, highlights, and action items |
| **Delegate Detail** | `/delegates/recruiter` | PipelineVisualizer, Timeline, LearningPanel with pattern suggestions |
| **Policy Editor** | `/delegates/recruiter/policy` | TrustThermostat + RuleCards + PolicyImpact |
| **Policy Simulator** | `/delegates/recruiter/policy/simulator` | Interactive what-if analysis with historical replay |
| **Command Palette** | `Cmd+K` | Navigate, search pending approvals, search decision memory |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/delegates` | List all delegates with live stats |
| `GET` | `/v1/delegates/{id}` | Get delegate details |
| `POST` | `/v1/delegates/{id}/pause` | Pause a delegate |
| `POST` | `/v1/delegates/{id}/resume` | Resume a delegate |
| `POST` | `/v1/delegates/recruiter/run` | Manually trigger recruiter pipeline |
| `GET` | `/v1/approvals` | List approval items (filter by status) |
| `POST` | `/v1/approvals/{id}/approve` | Approve an item (optionally with edited draft) |
| `POST` | `/v1/approvals/{id}/reject` | Reject an item |
| `GET` | `/v1/memory/opportunities` | List all opportunities |
| `GET` | `/v1/memory/opportunities/batch` | Batch fetch opportunities by IDs |
| `GET` | `/v1/user/goals` | Get career goals |
| `PUT` | `/v1/user/goals` | Update career goals |
| `GET` | `/v1/delegates/{id}/policy` | Get delegation policy |
| `POST` | `/v1/delegates/{id}/policy/simulate` | Simulate policy changes on historical data |
| `GET` | `/v1/delegates/{id}/learning/patterns` | Get detected behavioral patterns |
| `POST` | `/v1/delegates/{id}/learning/apply-suggestion` | Apply a learning suggestion |
| `GET` | `/v1/calendar/slots` | Find available time slots |
| `POST` | `/v1/calendar/book` | Book a calendar event |
| `GET` | `/v1/calendar/events` | List calendar events |
| `POST` | `/v1/calendar/events/{id}/cancel` | Cancel a calendar event |
| `GET` | `/v1/notifications` | List notifications |
| `POST` | `/v1/notifications/{id}/read` | Mark notification as read |
| `POST` | `/v1/notifications/read-all` | Mark all notifications as read |
| `GET` | `/v1/contacts` | List recruiter contacts |
| `GET` | `/v1/digest` | Get daily/weekly digest report |
| `GET` | `/v1/events/stream` | SSE stream (typed events: delegate.event, approval.new, approval.resolved, notification.new) |

---

## 🧱 The Moat

This is not a chat interface. The moat compounds over time:

- **Behavior data** — every approve/reject/edit teaches the delegate what "right" looks like for *you*
- **Policy layer** — delegation boundaries persist and sharpen across sessions
- **Decision memory** — every AI decision is logged, explained, searchable via `Cmd+K`
- **Trust Thermostat** — drag a slider to control AI autonomy, see real-time impact
- **Pattern learning** — delegate surfaces detected behavioral patterns with confidence scores and one-click actions
- **Policy Simulator** — test threshold changes on historical data before committing (MiroFish-inspired sandbox)
- **Auto-decline** — low-quality opportunities handled automatically, freeing you for high-value decisions
- **Cross-delegate coordination** — recruiter delegate triggers calendar holds for high-match opportunities

---

## 🔑 Environment variables

Copy `backend/.env.example` → `backend/.env`:

```
OPENAI_API_KEY=sk-...          # Required for LLM stages (pipeline works without it in mock mode)
OPENAI_MODEL_CHEAP=gpt-4o-mini
OPENAI_MODEL_HEAVY=gpt-4o
DATABASE_URL=sqlite+aiosqlite:///./data/delegates.db
REDIS_URL=redis://localhost:6379

# Optional — MS Graph for real email integration
MSGRAPH_TENANT_ID=
MSGRAPH_CLIENT_ID=
MSGRAPH_CLIENT_SECRET=
MSGRAPH_USER_EMAIL=

# Optional — Apollo.io for company enrichment
APOLLO_API_KEY=

# Tuning
CALENDAR_PREBLOCK_THRESHOLD=0.80    # Score above which calendar pre-blocks are created
EMAIL_POLL_INTERVAL_SECONDS=900     # Pipeline polling interval (default 15 min)
```

---

## 📋 Build Progress

| Sprint | Status | Scope |
|--------|--------|-------|
| 1 | ✅ Done | Bug fixes: SSE typed events, LLM extraction toggle, batch opportunity fetch, company scoring, learning patterns backend |
| 2 | ✅ Done | Complete recruiter: auto-decline, thread tracking, full JD text, calendar pre-block coordination |
| 3-4 | ✅ Done | Adjacent features: MS Graph email, recruiter trust scoring, company enrichment, notifications, digest, contacts API |
| 5 | ✅ Done | Policy Simulator: backend engine + interactive frontend with sliders and before/after comparison |
| 6 | ✅ Done | Calendar delegate: 4-stage pipeline, conflict checker, mock provider, booking/cancellation UI |
| 7 | ✅ Done | Learning system: pattern detection (5 types), actionable suggestions, apply-to-goals/policy |

---

## 🗺️ Roadmap

| Phase | Scope |
|-------|-------|
| **Infrastructure** | SQLite → PostgreSQL + Alembic migrations |
| **Semantic Search** | pgvector embeddings for "find similar to approved opportunities" |
| **Webhooks** | MS Graph change notifications for real-time email ingestion |
| **Authentication** | JWT middleware (Auth0/Clerk) replacing `user_id = "default"` |
| **Finance Delegate** | Expense tracking, subscription monitoring |
| **Comms Delegate** | Message filtering, routine reply drafting |
