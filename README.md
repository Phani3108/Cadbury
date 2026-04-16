# 🧠 Cadbury — Personal Delegates Network

A consumer-facing AI layer where specialized delegates handle distinct slices of your life — with strict boundaries on what they can decide, act on, and spend. Now with **voice chat** (Rose-inspired STT/TTS pipeline).

---

## 🤔 Why not just a personal assistant?

Generic assistants are forgettable. Delegates with **strict roles** are easier to trust.

- ✅ Each delegate has a defined scope — it doesn't drift
- ✅ You control autonomy per domain via a policy (not a prompt)
- ✅ Every AI decision is logged, explained, and searchable
- ✅ Trust builds over time — delegates learn your patterns
- ✅ Policy Simulator lets you test changes on historical data before committing
- ✅ **Voice + text chat** with any delegate, with end-to-end per-stage latency instrumentation

---

## 🤖 The Delegates

| Delegate | Status | What it handles |
|----------|--------|-----------------|
| 🔍 **Recruiter** | `Active` | Screens inbound recruiter emails, scores against your goals, drafts replies, auto-declines low matches |
| 📅 **Calendar** | `Active` | Multi-provider scheduling (Google + MS Graph), interview holds, conflict checking, slot proposals |
| 💬 **Comms** | `Active` | Triages messages across email / Slack / SMS / Telegram / WhatsApp, drafts replies |
| 💰 **Finance** | `Active` | Transaction tracking, recurring-charge detection, spending-spike alerts, subscription audits |
| 🛒 **Shopping** | `Active` | Price-watch list, deal detection (never auto-purchases — always asks) |
| 📚 **Learning** | `Active` | Skill-gap detection against career goals, learning-path creation, streaks + stale-path nudges |
| ❤️ **Health** | `Active` | Routine streak tracking, appointment reminders, overdue alerts (never auto-books) |

Every delegate is policy-gated: actions either run automatically, land in your approval queue, or are blocked outright based on a trust zone defined in YAML per delegate.

---

## 🎙️ Chat + Voice

A **per-delegate chat interface** with optional voice — accessible at `/chat`.

- Text + voice in the same thread, switch freely
- Voice pipeline: **Groq Whisper** STT → delegate-aware LLM → **ElevenLabs** TTS, cached
- Rose-inspired VAD (asymmetric thresholds, frame hysteresis, 30s max capture)
- Circuit breakers on Groq + ElevenLabs — graceful fallback to text if TTS is unavailable
- `Ctrl+Shift+D` toggles a dev panel showing per-stage latency: `STT / LLM / TTS / total`
- The LLM injects your career goals + recent memories + a delegate persona prompt
- Budget-enforced: chat turns count against the same daily LLM token/cost ceiling as pipelines

Digests and approvals can be **read aloud** via the same TTS skill (button on `/digest`).

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

- Dealbreakers are hard blocks — score = 0.0 regardless of other dimensions
- Auto-decline for very low scores (< 0.25) — polite decline without requiring approval
- Thread tracking deduplicates follow-ups onto the same opportunity
- High-match opportunities (≥ 0.80) automatically request calendar pre-blocks for interviews

---

## 🧪 Policy Simulator

Replay historical events through hypothetical policy thresholds **before** committing changes.

- Interactive sliders for engagement threshold, auto-decline floor, pre-block threshold
- Before/after comparison per opportunity
- Impact metrics — time saved, approval reduction, changed outcomes
- Debounced live preview (~500ms)

At `/delegates/recruiter/policy/simulator`.

---

## 🧠 Learning System

Delegates get smarter by detecting patterns in your decisions:

| Pattern | What it detects | Suggested action |
|---------|----------------|------------------|
| **Sector rejection** | >80% reject rate for a keyword across ≥5 opportunities | Add to dealbreakers |
| **Comp drift** | Approved opportunities consistently above min comp floor by 25%+ | Raise minimum compensation |
| **Recruiter quality** | 100% rejection rate for a recruiter across ≥3 opportunities | Add company to avoid list |
| **Score calibration** | 30%+ of approved opportunities scored below engagement threshold | Lower engagement threshold |
| **Approval backlog** | Growing queue of pending decisions | Enable auto-decline for low scores |

One-click apply — updates career goals or policy overrides automatically.

---

## 📊 Daily / Weekly Digest

- Summary + highlights + action items generated from pipeline activity
- Stats dashboard — processed count, auto-decline rate, average scores, time saved
- **"Listen"** button on `/digest` synthesizes a spoken version via ElevenLabs

---

## 🛡️ Governance & Observability

- **Trust zones** per delegate: auto / review / block — defined in YAML, editable via UI
- **Per-delegate budgets** — daily token + cost ceilings, auto-pause on breach, editable at `/admin/budgets`
- **Allowlist** — SQLite-backed set of identifiers permitted to trigger actions, managed at `/admin/allowlist`. The LLM cannot modify it.
- **OAuth connections** — Google + MS Graph token status + disconnect, at `/admin/connections`
- **System health** — live delegate status, p50/p95/p99 pipeline latency, budget bars, LLM totals (15s auto-refresh), at `/admin/health`
- **Full audit trail** — 40+ typed event types, decision log, pipeline-run history — browsable at `/delegates/[id]/history`

---

## 🏗️ Architecture

```
Next.js 16 frontend ──► FastAPI backend ──► SQLite/PostgreSQL (Alembic)
        │                    │
        ├ TanStack Query     ├ DelegateRuntime (asyncio scheduler, per-delegate pause/resume)
        ├ Zustand stores     ├ 7 pipeline-based delegates
        ├ SSE + WebSocket    ├ PolicyEngine + Simulator + Budget enforcement
        └ Voice hook (VAD)   ├ Three-tier memory (Memories → Scratchpad → Database)
                             ├ Skills: LLM router, OAuth, email, calendar, channels, speech
                             └ Observability metrics + circuit breakers
```

**Stack:**
- 🐍 Backend: FastAPI, SQLAlchemy 2.0 + Alembic, aiosqlite/asyncpg, OpenAI SDK, Pydantic v2
- 🎙️ Voice: Groq Whisper (STT), ElevenLabs (TTS), SHA256 audio cache, circuit breakers
- ⚛️ Frontend: Next.js 16, TypeScript, Tailwind, Zustand, Radix UI, TanStack Query
- 🗄️ DB: SQLite (dev) / PostgreSQL 17 (prod) with Alembic migrations
- 📡 Real-time: Server-Sent Events (typed envelopes, exponential-backoff reconnect) + optional WebSocket

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py                       # FastAPI entrypoint, lifespan, router wiring
│   ├── config/
│   │   ├── settings.py               # Pydantic Settings (env-backed)
│   │   └── delegate_policies/*.yaml  # One policy YAML per delegate
│   ├── delegates/                    # 7 pipeline-based delegates
│   ├── runtime/                      # DelegateRuntime, event bus, cross-delegate coordinator
│   ├── policy/                       # Engine, simulator, allowlist, budget store
│   ├── skills/
│   │   ├── llm_client.py             # Tiered model routing (cheap/heavy) + usage tracking
│   │   ├── email/                    # EmailProvider ABC + Mock + MS Graph OAuth2
│   │   ├── calendar/                 # CalendarProvider ABC + Mock + Google + MS Graph + Multi
│   │   ├── channels/                 # Telegram, WhatsApp, Slack, SMS, email digest
│   │   ├── auth/token_store.py       # Fernet-encrypted OAuth token storage
│   │   ├── company/enricher.py       # 3-tier enrichment (JD → Wikipedia → Apollo)
│   │   └── speech/                   # Rose-inspired STT (Groq) + TTS (ElevenLabs) + CircuitBreaker
│   ├── memory/                       # Three-tier memory (Memories, Scratchpad, Database)
│   ├── observability/metrics.py      # In-memory timings + counters + per-delegate health
│   ├── api/routes/
│   │   ├── chat.py                   # Per-delegate chat sessions, wired to LLM
│   │   ├── voice.py                  # /v1/voice/transcribe|synthesize|audio|chat
│   │   ├── allowlist.py              # Allowlist admin CRUD
│   │   ├── budgets.py                # GET/PUT per-delegate budgets
│   │   ├── oauth.py                  # OAuth2 PKCE for MS Graph + Google
│   │   ├── settings.py               # Integration credentials + test endpoints
│   │   ├── observability.py          # /v1/observability/health + metrics
│   │   ├── pipeline_runs.py          # Pipeline run inspector
│   │   └── ...                       # delegates, approvals, events, memory, digest, notifications
│   ├── migrations/                   # Alembic (auto-runs on startup)
│   └── tests/                        # pytest + pytest-asyncio
│
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                  # Dashboard
│   │   ├── chat/                     # Text + voice chat with any delegate
│   │   ├── approvals/                # Keyboard-driven approval inbox
│   │   ├── goals/                    # Goals editor (auto-save)
│   │   ├── opportunities/            # Scored opportunities + detail
│   │   ├── calendar/                 # Multi-calendar view + booking
│   │   ├── digest/                   # Daily/weekly summary with "Listen" button
│   │   ├── settings/                 # Integration credentials + quick-links
│   │   ├── admin/
│   │   │   ├── connections/          # OAuth provider connect/disconnect
│   │   │   ├── budgets/              # Editable per-delegate token/cost limits
│   │   │   ├── allowlist/            # Trusted identifiers admin
│   │   │   └── health/               # Live system health dashboard
│   │   └── delegates/[id]/
│   │       ├── page.tsx              # Delegate detail (pipeline, timeline, learning)
│   │       ├── history/              # Events / Runs / Decisions tabs
│   │       ├── policy/               # TrustThermostat + RuleCards
│   │       └── policy/simulator/     # Policy simulator
│   ├── src/components/
│   │   ├── chat/                     # ChatWindow, VoiceButton
│   │   ├── approvals/                # ApprovalCard, ApprovalDetail, DraftEditor
│   │   ├── goals/                    # GoalSection, TagInput, GoalsSidebar
│   │   ├── layout/                   # AppShell, Sidebar, Topbar, PageHeader
│   │   ├── scoring/                  # ScoreBadge, MatchBreakdown
│   │   └── shared/                   # CommandPalette, NotificationBell, EmptyState
│   ├── src/hooks/
│   │   ├── use-voice-session.ts      # VAD + recording lifecycle (Rose-style hysteresis)
│   │   └── use-event-stream.ts       # SSE with exponential backoff
│   ├── src/stores/                   # Zustand: events, approvals, goals, notifications, UI
│   └── src/lib/api.ts                # Typed API client (chat, voice, allowlist, …)
│
├── docker-compose.yml                # Dev: postgres + backend + frontend
├── docker-compose.prod.yml           # Production setup
└── README.md
```

---

## 🚀 Run locally

**Prerequisites:** Python 3.11+, Node 22+, Docker (optional — used for the PostgreSQL dev compose)

```bash
# Backend
cd backend
pip install -e ".[dev]"
uvicorn main:app --reload  # Alembic migrations auto-run on startup

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                # http://localhost:3000
```

**Trigger the recruiter pipeline (no OpenAI key needed — uses mock email source):**
```bash
curl -X POST http://localhost:8000/v1/delegates/recruiter/run
curl http://localhost:8000/v1/approvals              # pending approvals
curl http://localhost:8000/v1/memory/opportunities   # scored opportunities
curl http://localhost:8000/v1/events                 # full event trace
curl http://localhost:8000/v1/digest?period=daily    # daily digest
curl http://localhost:8000/v1/observability/health   # system health
```

The background scheduler runs enabled delegates automatically every 15 minutes (configurable via `EMAIL_POLL_INTERVAL_SECONDS`).

**Try voice:**
1. Add `GROQ_API_KEY` and `ELEVENLABS_API_KEY` at Settings → Voice (or in `backend/.env`)
2. Go to `/chat`, pick a delegate, tap the 🎤 button, speak, tap to stop
3. Reply audio autoplays. `Ctrl+Shift+D` toggles the per-stage latency panel

---

## 🖥️ Frontend Pages

| Page | URL | Description |
|------|-----|-------------|
| **Dashboard** | `/` | Overview with live delegate stats |
| **Chat** | `/chat` | Text + voice chat per-delegate |
| **Approval Inbox** | `/approvals` | Split view, keyboard shortcuts (`j`/`k`/`a`/`r`/`e`/`s`), optimistic updates |
| **Goals Editor** | `/goals` | Roles, comp, location, dealbreakers — auto-saves with 500ms debounce |
| **Opportunities** | `/opportunities` | All scored opportunities with match breakdowns |
| **Calendar** | `/calendar` | Multi-provider events, slot finding, booking |
| **Digest** | `/digest` | Daily/weekly summary with stats + "Listen" button |
| **Delegate Detail** | `/delegates/[id]` | PipelineVisualizer, Timeline, LearningPanel |
| **Delegate History** | `/delegates/[id]/history` | Events / Runs / Decisions tabs |
| **Policy Editor** | `/delegates/[id]/policy` | TrustThermostat + RuleCards + PolicyImpact |
| **Policy Simulator** | `/delegates/[id]/policy/simulator` | Historical replay with interactive sliders |
| **Settings** | `/settings` | Integration credentials (OpenAI, Groq, ElevenLabs, MS Graph, Apollo, …) |
| **Connections** | `/admin/connections` | OAuth provider connect/disconnect |
| **Budgets** | `/admin/budgets` | Per-delegate daily token + cost limits |
| **Allowlist** | `/admin/allowlist` | Trusted identifiers (env-seeded + user-added) |
| **System Health** | `/admin/health` | Live delegate status, pipeline latency, budget bars |
| **Command Palette** | `Cmd+K` | Navigate + full-text search across entities |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/delegates` | List all delegates with live stats |
| `GET` | `/v1/delegates/{id}` | Get delegate details |
| `POST` | `/v1/delegates/{id}/pause` \| `/resume` | Pause / resume a delegate |
| `POST` | `/v1/delegates/recruiter/run` | Manually trigger recruiter pipeline |
| `GET` | `/v1/approvals` | List approval items (filter by status) |
| `POST` | `/v1/approvals/{id}/approve` \| `/reject` | Act on approval item |
| `GET`/`PUT` | `/v1/user/goals` | Read / update career goals |
| `GET` | `/v1/memory/opportunities` | All scored opportunities |
| `GET` | `/v1/delegates/{id}/policy` | Delegation policy |
| `POST` | `/v1/delegates/{id}/policy/simulate` | Historical replay with hypothetical thresholds |
| `GET` | `/v1/delegates/{id}/learning/patterns` | Detected behavioral patterns |
| `POST` | `/v1/delegates/{id}/learning/apply-suggestion` | Apply a pattern's suggestion |
| `GET` | `/v1/calendar/events` \| `/slots` | List events / find available slots |
| `POST` | `/v1/calendar/book` | Book a calendar event |
| `GET` | `/v1/comms/messages` | Triaged messages |
| `GET` | `/v1/finance/transactions` \| `/subscriptions` \| `/alerts` | Finance views |
| `GET` \| `POST` | `/v1/shopping/watchlist` | Watch-list management |
| `GET` \| `POST` | `/v1/learning/paths` | Learning paths |
| `GET` \| `POST` | `/v1/health/routines` \| `/appointments` | Health tracking |
| `GET` \| `POST` | `/v1/chat/sessions` | Chat sessions (per-delegate) |
| `POST` | `/v1/chat/sessions/{id}/messages` | Send text, get LLM reply |
| `POST` | `/v1/voice/transcribe` | Audio blob → transcript |
| `POST` | `/v1/voice/synthesize` | Text → audio URL |
| `POST` | `/v1/voice/chat` | End-to-end voice turn (audio → STT → LLM → TTS + timings) |
| `GET` | `/v1/voice/audio/{id}` | Fetch synthesized audio (1h TTL) |
| `GET` | `/v1/budgets` \| `/{id}` | Per-delegate budget status |
| `PUT` | `/v1/budgets/{id}` | Update daily limits |
| `GET` \| `POST` \| `DELETE` | `/v1/allowlist` | Allowlist admin |
| `GET` | `/v1/auth/status` | OAuth provider connection status |
| `GET` | `/v1/auth/{provider}/login` | Begin OAuth2 PKCE flow |
| `POST` | `/v1/auth/{provider}/disconnect` | Remove stored tokens |
| `GET` | `/v1/settings` \| `PUT` \| `DELETE` | Integration credentials |
| `POST` | `/v1/settings/test/{key}` | Probe a connection (OpenAI, MS Graph, Apollo, …) |
| `GET` | `/v1/notifications` | In-app notifications |
| `GET` | `/v1/digest?period=daily\|weekly` | Digest report |
| `GET` | `/v1/pipeline-runs` \| `/{id}` | Pipeline run history + detail |
| `GET` | `/v1/observability/health` \| `/metrics` | System health + raw metrics |
| `GET` | `/v1/search?q=...` | Full-text search across 14 entity types |
| `GET` | `/v1/events/stream` | SSE (typed events: `delegate.event`, `approval.new`, `notification.new`, …) |

Full OpenAPI is served at `/docs` when the backend is running.

---

## 🧱 The Moat

This is not a chat interface. The moat compounds over time.

- **Behavior data** — every approve/reject/edit teaches the delegate what "right" looks like for *you*
- **Policy layer** — delegation boundaries persist and sharpen across sessions
- **Decision memory** — every AI decision is logged, explained, searchable
- **Trust Thermostat** — slider + rules + simulator controls AI autonomy per delegate
- **Pattern learning** — 5 detectors mine decision history into one-click-applicable suggestions
- **Budgets** — hard daily ceilings with auto-pause on breach
- **Cross-delegate coordination** — e.g. recruiter high-match → calendar pre-block, finance subscription flag → comms draft cancellation
- **Voice interface** — Rose-inspired STT/TTS pipeline with per-stage latency transparency
- **Deterministic scoring** — 5-factor weighted scorecards instead of opaque LLM judgments

---

## 🔑 Environment variables

Copy `backend/.env.example` → `backend/.env`:

```
# App
APP_ENV=development
SECRET_KEY=change-me-in-production
API_KEY=                                   # If empty, auth is disabled (dev only)

# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL_CHEAP=gpt-4o-mini
OPENAI_MODEL_HEAVY=gpt-4o

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/delegates.db    # dev
# DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/delegates   # prod

# MS Graph (email + calendar)
MSGRAPH_TENANT_ID=
MSGRAPH_CLIENT_ID=
MSGRAPH_CLIENT_SECRET=
MSGRAPH_USER_EMAIL=

# Google (calendar)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Company enrichment
APOLLO_API_KEY=

# Voice (Rose-inspired)
GROQ_API_KEY=                              # Whisper-large-v3 for STT
ELEVENLABS_API_KEY=                        # TTS
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM   # "Rachel" default
TTS_CACHE_TTL_SECONDS=86400
STT_MAX_AUDIO_MB=25

# Notification channels (all optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SLACK_BOT_TOKEN=
SLACK_DEFAULT_CHANNEL=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_DEFAULT_TO=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
SMS_DEFAULT_TO=

# Allowlist — comma-separated identifiers permitted to trigger delegate actions
ALLOWLIST=

# Tuning
CALENDAR_PREBLOCK_THRESHOLD=0.80
EMAIL_POLL_INTERVAL_SECONDS=900
FRONTEND_URL=http://localhost:3000
```

Integration credentials can also be saved + tested live in Settings → AI Engine / Voice / Email Integration.

---

## 📋 Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| 7 delegates (Recruiter, Calendar, Comms, Finance, Shopping, Learning, Health) | ✅ | All with pipeline-based implementations |
| Policy engine + trust zones + YAML per delegate | ✅ | auto / review / block |
| Policy Simulator | ✅ | Historical replay with before/after diffs |
| Pattern learning | ✅ | 5 detectors, one-click apply |
| Three-tier memory | ✅ | Memories / Scratchpad / Database |
| Per-delegate budgets + auto-pause | ✅ | Editable via UI |
| Allowlist admin UI | ✅ | |
| OAuth2 PKCE (MS Graph + Google) with encrypted tokens | ✅ | |
| Multi-channel notifications (Telegram / WhatsApp / Slack / SMS / email) | ✅ | |
| Chat UI + LLM wiring | ✅ | Per-delegate personas, memory + goals injection |
| Voice pipeline (STT + TTS + circuit breakers) | ✅ | Rose-inspired VAD + per-stage latency |
| "Read aloud" on digest | ✅ | |
| Observability dashboard | ✅ | Live health, p50/p95/p99, budget bars |
| Decision log + pipeline runs browser | ✅ | Per-delegate `/history` tabs |
| SQLAlchemy + Alembic, SQLite/PostgreSQL | ✅ | Auto-migrates on startup |
| Webhooks for real-time email | ⏳ | MS Graph change notifications |
| Semantic search (pgvector) | ⏳ | Currently keyword-only |
| Rate limiting | ⏳ | |
| Error tracking (Sentry) | ⏳ | |
| Onboarding flow | ⏳ | |
| E2E tests (Playwright) | ⏳ | |

---

## 🗺️ Roadmap

| Phase | Scope |
|-------|-------|
| **Semantic memory** | pgvector embeddings to replace keyword search; "find similar to approved opportunities" |
| **Webhooks** | MS Graph change notifications for real-time email ingestion |
| **Auth** | JWT middleware (Auth0/Clerk) replacing the dev-mode bearer token |
| **Resilience** | Wrap remaining external calls (MS Graph, Google, Apollo) in circuit breakers; add SlowAPI rate limiting; Sentry |
| **Onboarding** | Guided goals wizard + policy tour + notification opt-in |
| **Streaming TTS** | Chunk audio responses in real-time instead of synthesize-then-play |

---

## 🙏 Credits

Voice architecture patterns (fire-and-forget extraction, asymmetric-threshold VAD, circuit breakers, per-stage `PipelineTimings`) adapted from [Alexi5000/Rose](https://github.com/Alexi5000/Rose), a voice-first wellness companion. Cadbury applies the same latency-minded pipeline design to a multi-delegate governance system.
