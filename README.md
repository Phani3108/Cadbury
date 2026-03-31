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

---

## 🤖 The Delegates

| Delegate | Status | What it handles |
|----------|--------|-----------------|
| 🔍 **Recruiter** | `MVP` | Screens inbound recruiter emails, scores against your goals, drafts replies |
| 📅 **Calendar** | `Phase 2` | Manages scheduling, hold blocks, prep time |
| 💰 **Finance** | `Phase 2` | Expense tracking, subscription monitoring |
| 💬 **Comms** | `Phase 2` | Filters inbound messages, drafts routine replies |
| ✈️ **Travel** | `Phase 2` | Research, booking, itinerary |
| 🛍️ **Shopping** | `Phase 2` | Price tracking, reorder decisions |

---

## 🔁 Recruiter Delegate — How it works

```
Email arrives
  ↓ Stage 1: Ingest — fetch + identify recruiter signals
  ↓ Stage 2: Extract — LLM parses company, role, comp, location
  ↓ Stage 3: Score — pure Python: comp (35%) + role (30%) + location (20%) + criteria (15%)
  ↓ Stage 4: Policy — check against your delegation policy YAML
  ↓ Stage 5: Draft — generate engage / hold / decline reply
  ↓ Stage 6: Act — create ApprovalItem → you approve/edit/reject in inbox
```

**Key rule:** Dealbreakers are hard blocks — score = 0.0 regardless of other dimensions.

---

## 🏗️ Architecture

```
Redis Streams (event log)
    ↓
DelegateRuntime (asyncio event loop)
    ↓
RecruiterPipeline (6-stage)
    ↓
PolicyEngine ← recruiter.yaml
MemoryGraph ← SQLite (CareerGoals, Opportunities, DecisionLog)
    ↓
ApprovalQueue → FastAPI + SSE → Next.js frontend
```

**Stack:**
- 🐍 Backend: FastAPI, aiosqlite, OpenAI SDK, Pydantic v2
- ⚛️ Frontend: Next.js 16, TypeScript, Tailwind, Zustand, Radix UI
- 🗄️ DB: SQLite (MVP) → PostgreSQL + pgvector (Phase 2)
- 📡 Real-time: Server-Sent Events (SSE) with exponential backoff reconnect

---

## 📁 Project Structure

```
personal-delegates/
├── backend/
│   ├── delegates/recruiter/
│   │   ├── pipeline.py        # 6-stage pipeline
│   │   ├── scorer.py          # Pure Python opportunity scorer
│   │   └── prompts/           # LLM prompts (extract, score, draft)
│   ├── policy/
│   │   ├── engine.py          # PolicyEngine → TrustZone (auto/review/block)
│   │   └── loader.py          # YAML → DelegationPolicy
│   ├── config/delegate_policies/
│   │   └── recruiter.yaml     # The actual delegation boundaries
│   ├── skills/
│   │   ├── llm_client.py      # Tiered model routing (cheap/heavy)
│   │   └── email/             # EmailProvider ABC + MockEmailProvider
│   ├── memory/
│   │   ├── models.py          # CareerGoals, JobOpportunity, DecisionLog...
│   │   └── graph.py           # SQLite persistence + MemoryGraph class
│   ├── api/routes/            # FastAPI routes (goals, approvals, delegates, events)
│   └── runtime/               # Event bus (SSE pub/sub), delegate kernel
│
├── frontend/
│   ├── src/app/               # Next.js App Router pages
│   │   ├── page.tsx           # Dashboard
│   │   ├── goals/             # Goals Editor (fully wired)
│   │   ├── approvals/         # Approval Inbox (stub → Week 3)
│   │   └── delegates/[id]/    # Delegate detail + policy view
│   ├── src/components/
│   │   ├── goals/             # GoalSection, TagInput, GoalsSidebar
│   │   ├── layout/            # AppShell, Sidebar, Topbar
│   │   └── scoring/           # ScoreBadge, MatchBreakdown
│   └── src/stores/            # Zustand: events, approvals, goals, UI
│
├── docker-compose.yml          # Redis + backend + frontend
└── PLAN.md                     # Full architecture + UI/UX spec
```

---

## 🚀 Run locally

**Prerequisites:** Python 3.12+, Node 22+, Docker (for Redis)

```bash
# Backend
cd personal-delegates/backend
pip install -e ".[dev]"
docker run -d -p 6379:6379 redis:7-alpine
uvicorn main:app --reload

# Frontend (separate terminal)
cd personal-delegates/frontend
npm install
npm run dev
```

**Trigger the recruiter pipeline (no OpenAI key needed):**
```bash
curl -X POST http://localhost:8000/v1/delegates/recruiter/run
# → processes 3 mock recruiter emails, scores them, stores results

curl http://localhost:8000/v1/memory/opportunities  # scored opportunities
curl http://localhost:8000/v1/events                # full event trace
```

**Set your career goals:**
- Open `http://localhost:3000/goals`
- Fill in roles, comp, location, dealbreakers
- Auto-saves with 500ms debounce
- Right panel shows "what your delegate sees" in real time

---

## 🧱 The Moat

This is not a chat interface. The moat compounds over time:

- **Behavior data** — every approve/reject/edit teaches the delegate what "right" looks like for *you*
- **Policy layer** — delegation boundaries persist and sharpen across sessions
- **Decision memory** — every AI decision is logged, explained, searchable via `Cmd+K`
- **Trust Thermostat** — drag a slider to control AI autonomy, see real-time impact (no YAML editing)
- **Pattern learning** — delegate surfaces detected behavioral patterns with confidence scores

---

## 📋 Build Progress

| Week | Status | Scope |
|------|--------|-------|
| 1 | ✅ Done | Scaffold: FastAPI, Next.js, SQLite, SSE, Zustand stores, all route stubs |
| 2 | ✅ Done | Recruiter pipeline Stages 1–3, scorer, policy engine, Goals Editor UI |
| 3 | 🔲 Next | Stages 4–6 (Policy gate, Draft, Act), Approval Inbox UI |
| 4 | 🔲 | ApprovalCard, DraftEditor, keyboard shortcuts, optimistic updates |
| 5 | 🔲 | Dashboard, Delegate Detail, PipelineVisualizer, Trust Thermostat |
| 6 | 🔲 | Docker e2e, MS Graph email integration, decision memory search |

---

## 🔑 Environment variables

Copy `backend/.env.example` → `backend/.env`:

```
OPENAI_API_KEY=sk-...          # Required for LLM stages (pipeline works without it in mock mode)
OPENAI_MODEL_CHEAP=gpt-4o-mini
OPENAI_MODEL_HEAVY=gpt-4o
DATABASE_URL=sqlite+aiosqlite:///./data/delegates.db
REDIS_URL=redis://localhost:6379

# Optional — MS Graph for real email
MSGRAPH_TENANT_ID=
MSGRAPH_CLIENT_ID=
MSGRAPH_CLIENT_SECRET=
MSGRAPH_USER_EMAIL=
```
