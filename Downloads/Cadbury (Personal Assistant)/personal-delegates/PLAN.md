# Personal Delegates Network — Implementation Plan

## Context

The goal is to build a consumer-facing "Personal Delegates Network" — a system where specialized AI agents handle distinct life domains (comms, scheduling, travel, recruiter, shopping, learning) with strict delegation boundaries. Unlike a generic chat assistant, each delegate has explicit rules about what it can decide autonomously, how much risk/money it can commit, and when it must escalate to the human.

The architecture is inspired by OpenClaw's event-driven model: instead of stateless request/response, delegates are stateful long-lived workers in an event loop, with a personal memory graph, policy layer, and full observability/replay.

**MVP:** Recruiter Delegate — screens inbound recruiter emails, extracts job details, scores against user career goals, drafts responses, and creates calendar holds. All consequential actions require human approval via an inbox UI.

---

## Architecture Overview

```
Redis Streams (per-delegate event log)
        ↓
DelegateRuntime (asyncio event loop)
  ├── RecruiterDelegate Worker (stateful)
  └── [CalendarDelegate, ...] (Phase 2)
        ↓
Tool Graph
  ├── EmailSkill (MS Graph — from RDT 2)
  ├── CalendarSkill (MS Graph — from RDT 6)
  └── LLMClient (OpenAI/Azure)
        ↓
PolicyEngine (YAML-backed DelegationPolicy)
MemoryGraph (SQLite: CareerGoals, JobOpportunity, DecisionLog)
ObservabilityBus (OTel spans — from RDT 6 tracing.py)
        ↓
ApprovalQueue (human inbox — actions pending sign-off)
        ↓
FastAPI + SSE → Next.js frontend
```

---

## Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend | FastAPI (async) | Consistent with all 3 existing systems |
| Event bus | asyncio + Redis Streams | Persistent, replayable; AegisAI job_store already has Redis support |
| LLM | OpenAI / Azure OpenAI | Reuse `AzureOpenAIClient` from RDT 2 |
| Memory | SQLite (MVP) → PostgreSQL + pgvector (Phase 2) | Simplest start; AuditLog pattern from RDT 2 |
| Email | MS Graph (GraphConnector from RDT 2) | Already handles OAuth, token refresh, async |
| Frontend | Next.js 14+ App Router, TypeScript, Tailwind | Better for approval-queue / activity-feed pattern |
| UI Components | shadcn/ui (Radix primitives + Tailwind) | Battle-tested, customizable, not heavyweight |
| Icons | Lucide React | Clean, consistent, 1000+ icons — zero emojis |
| Animations | Framer Motion | Micro-interactions, spring physics for Trust Thermostat |
| Font | Geist (Vercel) | Clean, modern, mono variant for numbers |
| State | Zustand | Lightweight stores for events, approvals, UI state |
| Observability | OTel + Prometheus | Copy `tracing.py` from RDT 6 directly |

---

## Project Structure

```
personal-delegates/
├── backend/
│   ├── main.py
│   ├── config/
│   │   └── delegate_policies/
│   │       ├── recruiter.yaml
│   │       └── base_policy_schema.yaml
│   ├── runtime/
│   │   ├── kernel.py          # DelegateRuntime: event loop + worker registry
│   │   ├── worker.py          # BaseDelegate: stateful lifecycle
│   │   ├── event_bus.py       # Redis Streams wrapper
│   │   ├── event_models.py    # DelegateEvent, EventType enum
│   │   └── scheduler.py       # Polling triggers (15-min email poll)
│   ├── delegates/
│   │   └── recruiter/
│   │       ├── delegate.py    # RecruiterDelegate(AbstractDelegate)
│   │       ├── pipeline.py    # 6-stage pipeline (adapted from RDT 6)
│   │       ├── scorer.py      # JobOpportunityScorer
│   │       ├── drafter.py     # ResponseDrafter (LLM)
│   │       └── prompts/
│   │           ├── extract_jd.txt
│   │           ├── score_opportunity.txt
│   │           └── draft_response.txt
│   ├── memory/
│   │   ├── graph.py           # SQLite ORM
│   │   └── models.py          # CareerGoals, JobOpportunity, DecisionLog, RecruiterContact
│   ├── policy/
│   │   ├── engine.py          # PolicyEngine: YAML load + boundary enforcement
│   │   ├── models.py          # DelegationPolicy, RiskBoundary, ActionPermission
│   │   └── loader.py          # YAML → Pydantic (adapted from AegisAI policy/loader.py)
│   ├── skills/
│   │   ├── email/
│   │   │   ├── provider.py    # EmailProvider ABC
│   │   │   └── msgraph.py     # Adapted from RDT 2 graph_connector.py
│   │   ├── calendar/
│   │   │   ├── provider.py
│   │   │   └── msgraph.py     # Adapted from RDT 6 skills/calendar.py
│   │   └── llm_client.py      # Tiered model routing (from RDT 6 router.py)
│   ├── api/
│   │   └── routes/
│   │       ├── delegates.py
│   │       ├── events.py      # SSE + WebSocket event streams
│   │       ├── approvals.py   # Human approval inbox
│   │       ├── goals.py       # CareerGoals CRUD
│   │       └── jobs.py        # Async job lifecycle (from AegisAI v1_jobs.py)
│   ├── observability/
│   │   ├── tracing.py         # Copy from RDT 6 (zero changes needed)
│   │   └── metrics.py         # Copy from AegisAI metrics.py
│   └── tests/
│       ├── test_recruiter_pipeline.py
│       ├── test_policy_engine.py
│       └── test_memory_graph.py
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx                    # Root: AppShell, fonts, providers
│   │   │   ├── page.tsx                      # Dashboard
│   │   │   ├── approvals/
│   │   │   │   └── page.tsx                  # Approval Inbox (split view)
│   │   │   ├── delegates/
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx              # Delegate detail + timeline
│   │   │   │       └── policy/page.tsx       # Trust Thermostat + policy view
│   │   │   ├── goals/
│   │   │   │   └── page.tsx                  # Career goals editor
│   │   │   └── opportunities/
│   │   │       └── [id]/page.tsx             # Opportunity detail
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── app-shell.tsx             # Sidebar + content
│   │   │   │   ├── sidebar.tsx               # Nav with badges + status dots
│   │   │   │   ├── topbar.tsx                # Breadcrumb + Cmd+K + avatar
│   │   │   │   └── page-header.tsx
│   │   │   ├── approvals/
│   │   │   │   ├── approval-card.tsx         # List item card
│   │   │   │   ├── approval-detail.tsx       # Full detail panel
│   │   │   │   ├── draft-editor.tsx          # Editable response draft
│   │   │   │   └── approval-actions.tsx      # Action buttons + shortcuts
│   │   │   ├── delegates/
│   │   │   │   ├── delegate-card.tsx         # Active delegate card
│   │   │   │   ├── empty-delegate-card.tsx   # "Coming soon" placeholder
│   │   │   │   ├── pipeline-visualizer.tsx   # 6-stage horizontal flow
│   │   │   │   └── learning-panel.tsx        # Pattern detection display
│   │   │   ├── policy/
│   │   │   │   ├── trust-thermostat.tsx      # Hero moat component
│   │   │   │   ├── rule-card.tsx             # Per-zone rule display
│   │   │   │   └── policy-impact.tsx         # "What if" preview
│   │   │   ├── scoring/
│   │   │   │   ├── score-badge.tsx           # SVG ring + number
│   │   │   │   └── match-breakdown.tsx       # Horizontal dimension bars
│   │   │   ├── timeline/
│   │   │   │   ├── timeline.tsx              # Vertical event chain
│   │   │   │   ├── timeline-event.tsx        # Single node
│   │   │   │   └── decision-card.tsx         # Expandable what/why/rules
│   │   │   ├── goals/
│   │   │   │   ├── goal-section.tsx          # Collapsible accordion card
│   │   │   │   └── tag-input.tsx             # Multi-value with colored pills
│   │   │   ├── shared/
│   │   │   │   ├── status-pill.tsx
│   │   │   │   ├── event-card.tsx
│   │   │   │   ├── empty-state.tsx
│   │   │   │   ├── connection-banner.tsx
│   │   │   │   └── command-palette.tsx       # Cmd+K (shadcn command)
│   │   │   └── ui/                           # shadcn/ui primitives
│   │   ├── hooks/
│   │   │   ├── use-event-stream.ts           # SSE connection + reconnect
│   │   │   ├── use-keyboard-shortcuts.ts     # Global + context shortcuts
│   │   │   └── use-auto-save.ts              # Debounced save for goals
│   │   ├── stores/
│   │   │   ├── event-store.ts                # Zustand: events + connection
│   │   │   ├── approval-store.ts             # Zustand: approvals + filter
│   │   │   └── ui-store.ts                   # Zustand: sidebar, page context
│   │   └── lib/
│   │       ├── api.ts                        # API client
│   │       ├── types.ts                      # Shared TypeScript types
│   │       └── utils.ts                      # Helpers
│   ├── tailwind.config.ts                    # Design tokens
│   └── package.json
├── docker-compose.yml
└── pyproject.toml
```

---

## Core Data Models

### DelegationPolicy (YAML + Pydantic)
```python
class ActionPermission(BaseModel):
    action: str
    auto_approve: bool = False
    requires_approval_above: Optional[float] = None  # Risk threshold

class RiskBoundary(BaseModel):
    max_financial_commitment: float = 0.0
    max_calendar_commitment_hours: float = 2.0
    max_autonomy_score: float = 0.6

class DelegationPolicy(BaseModel):
    version: int
    delegate_id: str
    allowed_actions: List[ActionPermission]
    risk_boundary: RiskBoundary
    approval_required_for: List[str]
    thresholds: dict  # min_score_for_engagement, auto_decline_below
```

### Memory Models
```python
class CareerGoals(BaseModel):
    target_roles: List[str]
    min_comp_usd: int
    preferred_locations: List[str]
    must_have_criteria: List[str]
    dealbreakers: List[str]
    open_to_relocation: bool

class JobOpportunity(BaseModel):
    opportunity_id: str
    company: str; role: str
    comp_range_min/max: Optional[int]
    location: str; remote_policy: str
    match_score: float           # 0-1 from scorer
    match_breakdown: dict        # {comp, role, location, criteria}
    status: str                  # received → scored → responded/rejected

class DecisionLog(BaseModel):
    delegate_id: str
    action_taken: str
    reasoning: str               # LLM rationale
    policy_check: dict           # Which rules were evaluated
    human_approved: Optional[bool]
    timestamp: datetime
```

### Runtime Event
```python
class EventType(StrEnum):
    EMAIL_RECEIVED | OPPORTUNITY_EXTRACTED | OPPORTUNITY_SCORED
    DRAFT_CREATED | APPROVAL_REQUESTED | HUMAN_APPROVED | HUMAN_REJECTED
    RESPONSE_SENT | CALENDAR_BOOKED | POLICY_BLOCKED | ERROR

class DelegateEvent(BaseModel):
    event_id: str
    delegate_id: str
    event_type: EventType
    payload: dict
    parent_event_id: Optional[str]  # For replay chains
    trace_id: Optional[str]         # OTel trace
    risk_score: float
    requires_approval: bool
```

---

## Recruiter Delegate: 6-Stage Pipeline

Adapted directly from RDT 6's `PipelineContext` + `@trace_span` pattern:

```
Stage 1 — INGEST
  GraphConnector.list_inbox_messages(filter=recruiter signals)
  → DelegateEvent(EMAIL_RECEIVED)

Stage 2 — EXTRACT
  LLM call with extract_jd.txt prompt
  → JobOpportunity{company, role, comp, location, equity, jd_text}
  → DelegateEvent(OPPORTUNITY_EXTRACTED)

Stage 3 — SCORE
  JobOpportunityScorer.score(opportunity, career_goals)
  Weights: comp(0.35) + role(0.30) + location(0.20) + criteria(0.15)
  → match_score, match_breakdown
  → DelegateEvent(OPPORTUNITY_SCORED)

Stage 4 — POLICY CHECK
  PolicyEngine.evaluate(action, score)
  score < auto_decline_below → polite decline (auto if policy allows)
  score >= engagement_threshold → proceed to draft
  otherwise → request more info
  → gate or continue

Stage 5 — DRAFT
  ResponseDrafter picks template: decline / hold / engage
  For "engage": includes 2-3 calendar slots from CalendarSkill
  → DelegateEvent(DRAFT_CREATED)

Stage 6 — ACT (Human-in-Loop Gate for MVP)
  All actions → ApprovalItem created
  User approves/edits/rejects in inbox
  On approval → GraphConnector.send_reply()
  → DelegateEvent(RESPONSE_SENT or HUMAN_REJECTED)
```

---

## Delegation Policy: recruiter.yaml

```yaml
version: 1
delegate_id: recruiter
risk_boundary:
  max_financial_commitment: 0.0
  max_calendar_commitment_hours: 1.0
  max_autonomy_score: 0.55

allowed_actions:
  - action: read_email
    auto_approve: true
  - action: extract_opportunity
    auto_approve: true
  - action: score_opportunity
    auto_approve: true
  - action: send_polite_decline    # MVP: false; Phase 2: true below threshold
    auto_approve: false
  - action: send_engagement_reply
    auto_approve: false
  - action: book_calendar_slot
    auto_approve: false

approval_required_for:
  - send_polite_decline
  - send_engagement_reply
  - book_calendar_slot

thresholds:
  min_score_for_engagement: 0.65
  auto_decline_below: 0.30
```

---

## Key API Endpoints

```
# Delegate management
GET    /v1/delegates
POST   /v1/delegates/{id}/pause|resume

# Real-time event streaming
GET    /v1/events?delegate_id=recruiter      # SSE stream
WS     /v1/ws/events

# Approval inbox
GET    /v1/approvals
GET    /v1/approvals/{id}
POST   /v1/approvals/{id}/approve
POST   /v1/approvals/{id}/reject
POST   /v1/approvals/{id}/edit

# User goals
GET|PUT /v1/user/goals

# Memory
GET    /v1/memory/opportunities
GET    /v1/memory/decisions          # Full audit/replay log

# Async jobs (for manual triggers)
POST   /v1/jobs
GET    /v1/jobs/{id}
GET    /v1/jobs/{id}/events          # SSE
```

---

## Existing Code to Reuse

| Source File | Reuse As | Key Assets |
|-------------|----------|-----------|
| `RDT 2/backend/integrations/graph_connector.py` | `skills/email/msgraph.py` + `skills/calendar/msgraph.py` | MS Graph OAuth, email read/send, calendar CRUD |
| `RDT 6/orchestrator/pipeline.py` | `delegates/recruiter/pipeline.py` | `PipelineContext` dataclass, `@trace_span` stage pattern |
| `RDT 6/digital_twin/observability/tracing.py` | `observability/tracing.py` | Copy verbatim — `trace_span` decorator, `add_span_attribute` |
| `RDT 6/skills/calendar.py` | `skills/calendar/msgraph.py` | `find_free_slot()`, `create_calendar_event()` |
| `RDT 6/orchestrator/router.py` | `skills/llm_client.py` | Model tier routing (cheap vs. heavy) |
| `AegisAI/src/aegisai/services/job_store.py` | `runtime/event_bus.py` | In-memory + Redis + file persistence, retry, dead-letter |
| `AegisAI/src/aegisai/api/routes/v1_jobs.py` | `api/routes/jobs.py` | Async job lifecycle, idempotency, SSE, WebSocket, audit |
| `AegisAI/src/aegisai/policy/routing.py` + `loader.py` | `policy/models.py` + `policy/loader.py` | YAML-backed Pydantic policy, `public_view()` |
| `RDT 2/backend/utils/auditor.py` | `memory/graph.py` | SQLite `AuditLog` → base for `DecisionLog` |
| `RDT 2/frontend-next/` | `frontend/` | Next.js scaffold with App Router, TypeScript, Tailwind |

---

## UI/UX Specification

### Design System Tokens

**Colors** (`tailwind.config.ts` extend):
- Neutral: Tailwind `slate` scale. Background `slate-50`, cards `white`, text `slate-900`, muted `slate-400`, borders `slate-200`
- Brand: Indigo. `brand-500: #6366f1` (buttons, active), `brand-600: #4f46e5` (hover), `brand-50: #eef2ff` (tint bg)
- Trust zones (the product's core visual language):
  - Green (auto-approve): `green-500` / `green-50`
  - Amber (review needed): `amber-500` / `amber-50`
  - Red (blocked/reject): `red-500` / `red-50`

**Typography** (Geist via `next/font`):
- `text-xs` 12px timestamps/badges, `text-sm` 14px body, `text-base` 16px primary, `text-lg` 18px section headers, `text-2xl` 24px page titles, `text-3xl` 30px hero numbers (Geist Mono)
- Weights: 400 body, 500 labels, 600 headers/buttons, 700 page titles

**Spacing**: Tight. `8px` internal padding, `12px` card padding, `16px` section gaps, `24px` between-section, `32px` major breaks

**Radii**: `4px` badges, `8px` cards/inputs/buttons, `12px` modals, `full` avatars/dots

**Shadows**: `shadow-sm` at rest, `shadow-md` on hover, `shadow-lg` modals/command palette

---

### Icon Mapping (Lucide React — zero emojis in the entire product)

**Navigation**: Dashboard `LayoutDashboard`, Approvals `Inbox`, Delegates `Bot`, Goals `Target`, Policy `Shield`, Opportunities `Briefcase`, Settings `Settings`, Search `Search`, Notifications `Bell`

**Pipeline stages**: Ingest `Download`, Extract `FileSearch`, Score `BarChart3`, Policy `Shield`, Draft `PenLine`, Act `Send`

**Actions**: Approve `Check`, Reject `X`, Edit `PenLine`, Defer `Clock`, Auto-approved `CheckCheck`, Needs attention `AlertTriangle`, Blocked `ShieldAlert`

**Trust zones**: Auto `ShieldCheck` (green), Review `ShieldAlert` (amber), Block `ShieldX` (red)

**Domain**: `Calendar`, `MapPin`, `DollarSign`, `Building2`, `Mail`, `User`, `Gauge` (trust), `Sparkles` (learning), `History` (timeline)

---

### Layout Shell

**`AppShell`**: Fixed left sidebar (`w-56`, collapses to `w-14` on tablet, hidden on mobile with hamburger). Main content area `max-w-6xl` centered. Topbar inside content area.

**`Sidebar`**: "Delegates" logo in Geist 600 at top. Nav groups: Dashboard, Approvals (red count badge), Delegates (sub-nav with status dots), Goals, Opportunities. Footer: Settings, user avatar, collapse toggle. Active: 3px left border `brand-500`, `brand-50` bg.

**`Topbar`**: Breadcrumb left. Right: `Cmd+K` trigger, notification bell with badge, user avatar dropdown.

---

### Component Inventory

| Component | Purpose |
|-----------|---------|
| `ScoreBadge` | Circular SVG progress ring + centered number (Geist Mono). Sizes sm/md/lg. Color by threshold: >=80 green, 50-79 amber, <50 red |
| `StatusPill` | Rounded pill with icon + label. Variants: approved/pending/rejected/auto/draft |
| `EventCard` | Compact card: 8px status dot, action title, description, timestamp, optional score badge |
| `ApprovalCard` | Full context card: delegate + action type, context summary, score, expandable draft (editable), action buttons with keyboard hints |
| `PipelineVisualizer` | Horizontal 6-stage flow. Icons in 36px circles connected by lines. Active = pulsing brand-500, completed = green with Check, future = outline slate-300. Clickable to filter timeline |
| `TrustThermostat` | **Hero moat component.** Horizontal slider with 3 colored zones. Draggable threshold handles (Framer Motion spring: stiffness 300, damping 30). Real-time impact preview as user drags |
| `MatchBreakdown` | Horizontal bar chart: Role Fit, Comp, Location, Company, Recruiter Quality. Color-coded by threshold |
| `TimelineEvent` | Vertical timeline with dots + connecting line. Color by type. "What" and "Why" visually separated |
| `DelegateCard` | Bot icon, name, status dot, last active. Stats: processed today, pending, auto-rate. Click → detail |
| `EmptyDelegateCard` | Dashed border, desaturated. "Coming soon" badge. Placeholder for Calendar, Finance, etc. |
| `DecisionCard` | Expandable: What happened, Why (reasoning), Which Rules, What Data. "Was this right?" feedback buttons |
| `LearningPanel` | Detected patterns with confidence bars. New patterns animate with Sparkles. Historical accuracy trend |
| `GoalSection` | Collapsible card with icon + friendly title. Framer Motion accordion |
| `TagInput` | Multi-value with pills. Must-haves = green, dealbreakers = red. Type-to-add with autocomplete |
| `CommandPalette` | `Cmd+K` overlay (shadcn command). Sections: Recent, Approvals, Opportunities, Actions. Keyboard-navigable |
| `ConnectionBanner` | Full-width yellow bar on SSE disconnect. Auto-retry with backoff |
| `EmptyState` | Centered icon (48px slate-300), title, description, optional CTA button |

---

### Page Designs

#### Dashboard (`/`)
**Purpose**: "What needs my attention?" + "What happened while I was away?"

- **Greeting**: "Good morning, {name}" + "{n} items need your attention"
- **Attention Strip**: 3 metric cards — Approvals waiting (`Inbox`), High-match opportunities (`TrendingUp`), Processed today (`CheckCheck`). Each clickable.
- **Two-column** (single on mobile):
  - Left: "Pending Approvals" — top 3 compact `ApprovalCard` with inline one-tap approve. "View all" link
  - Right: "Activity Feed" — live `Timeline` of recent events via SSE. New events slide in from top
- **Delegates Row**: `DelegateCard` (Recruiter, active) + `EmptyDelegateCard` (Calendar, Finance, Social — "Coming Soon") + subtle "+" button

#### Approval Inbox (`/approvals`) — THE core interaction
**Design**: Linear triage + Superhuman speed

- **Filter Bar**: Tabs [All | Pending | Approved | Rejected] + score threshold dropdown
- **Split View** (desktop >=1024px): Left `w-1/3` scrollable list, Right `w-2/3` full detail. Mobile: stacked push navigation
- **Detail panel**:
  1. Company, role, location, comp range
  2. `ScoreBadge` (large) + `MatchBreakdown`
  3. `DraftEditor`: editable textarea with AI-generated response
  4. Policy check summary: which rules, auto-approve reasoning
  5. Mini `Timeline` of this opportunity's processing stages
  6. Action buttons: `[A] Approve` (green), `[E] Edit` (brand), `[R] Reject` (red), `[S] Skip` (slate) — keyboard hints visible
- **Speed features**: `j`/`k` navigation, auto-advance after action, undo toast (5s), batch mode (`x` toggle, `Shift+a` approve all), pre-fetch adjacent items

#### Delegate Detail (`/delegates/recruiter`)
- **Stats Row**: 4 metrics — processed today, pending approvals, auto-rate %, avg score
- **`PipelineVisualizer`**: Full-width horizontal. Click stage → filter timeline below
- **Two-column**:
  - Left: "Event Timeline" — filterable vertical `Timeline` with expandable `DecisionCard`. "Load more" pagination
  - Right: "Learning & Patterns" — `LearningPanel` with detected patterns + delegation stats bar (auto/review/blocked %). "View Policy" link

#### Goals Editor (`/goals`)
**Conversational, friendly, precise. Like setting up a dating profile.**

- Subtitle: "Help your delegate understand what you're looking for"
- **5 collapsible `GoalSection` cards** (Framer Motion accordion):
  1. **Role Preferences** (`Target`): Target titles `TagInput` (green), skills `TagInput` (green), dealbreakers `TagInput` (red)
  2. **Compensation** (`DollarSign`): Base range min/max + visual range bar, total comp floor, checkboxes (Equity, Bonus, Signing)
  3. **Location** (`MapPin`): Work style radio (Remote/Hybrid/On-site), preferred cities `TagInput`, relocation toggle
  4. **Company** (`Building2`): Stage checkboxes (Pre-seed → Public), size `RangeSlider`, industries `TagInput`, avoid list `TagInput` (red)
  5. **Communication** (`Mail`): Tone radio (Professional/Casual/Formal), auto-include checkboxes, signature input
- **Auto-save** with 500ms debounce. "Saving..." → "Saved" with Check icon
- Desktop: right sidebar shows "What your delegate sees" — real-time summary interpretation

#### Policy View (`/delegates/recruiter/policy`)
**Visual delegation boundaries. Trust thermostat is the hero.**

- **`TrustThermostat`**: Full-width. Three zones (green/amber/red). Draggable handles. Current distribution percentages below
- **3 `RuleCard` components** (one per zone):
  - Green: auto-approve conditions (score threshold, known recruiter, preferred industry)
  - Amber: hold-for-review (score range, first contact, comp edge cases)
  - Red: auto-reject (low score, spam, dealbreaker role)
  - Each rule editable: click threshold values to change. Natural language, not config syntax
- **`PolicyImpact` preview**: "If applied to last 30 days: {n} auto-approved, {n} reviewed, {n} auto-rejected. Estimated time saved: {n}h/week." Recalculates on every change (debounced)

#### Opportunity Detail (`/opportunities/{id}`)
- **Hero**: `Building2` + company, role, location + work style + comp, large `ScoreBadge`, `StatusPill`
- **Three-column** (stacks on mobile): `MatchBreakdown` | Details (source, recruiter, posting age, JD summary) | Decision Trail `Timeline`
- **`DraftEditor`** section: full draft + Approve & Send / Edit & Send / Reject buttons
- **Recruiter Contact History**: Prior messages with dates and outcomes

---

### Interaction Patterns

**Global shortcuts**: `Cmd+K` command palette, `g d` dashboard, `g a` approvals, `g r` recruiter, `g g` goals, `g p` policy, `?` shortcut overlay

**Approval shortcuts**: `j`/`k` navigate, `a` approve, `r` reject, `e` focus editor, `s` skip, `Cmd+Enter` approve+next, `x` toggle select, `Shift+a` batch approve, `/` focus filter, `Esc` deselect

**Animations** (Framer Motion):

| Element | Animation | Duration |
|---------|-----------|----------|
| Page transition | Fade + translateY(8px) | 200ms |
| Card hover | translateY(-2px) + shadow-md | 150ms |
| Approval action | Card slides out + fades | 300ms |
| New SSE event | Slide from top + highlight flash | 400ms |
| Score badge | Scale 0.8→1 + fade | 250ms |
| Pipeline stage | Circle fill from center | 300ms |
| Toast | Slide from right | 200ms |
| Command palette | Scale 0.95→1 + backdrop | 150ms |
| Trust thermostat drag | Spring (stiffness 300, damping 30) | continuous |
| Accordion expand | Height auto-animate | 250ms |

---

### Real-Time Data Flow

Client opens persistent `EventSource` to `GET /api/events/stream`. Custom `useEventStream` hook manages connection + reconnection (exponential backoff). Events dispatch to Zustand stores.

| Server Event | UI Update |
|-------------|-----------|
| `delegate.event` | New timeline entry (slide-in) |
| `approval.new` | Sidebar badge +1, new card in inbox |
| `approval.resolved` | Badge -1, card removal |
| `pipeline.progress` | Pipeline stage highlight |
| `stats.update` | Numbers update (count-up animation) |
| `connection.lost` | Yellow `ConnectionBanner` |
| `connection.restored` | Banner dismisses, missed events applied |

**Stores** (Zustand): `eventStore` (rolling 200 events + connection status), `approvalStore` (pending array + filter + selected ID), `uiStore` (sidebar collapsed, active page)

**Optimistic updates**: Approve/reject update UI immediately. Server error → revert + red toast with retry.

---

### Empty & Loading States

**Empty states** (all use `EmptyState` component — icon, title, description, optional CTA):
- Dashboard: `Inbox` icon, "Connect your email to get started" + [Connect Email] button
- Approvals: `CheckCheck` icon, "All clear! Your delegate handled {n} items automatically today"
- Activity: `Clock` icon, "No activity yet. Delegate starts working once connected"
- Opportunities: `Search` icon, "No opportunities found yet. Monitoring your inbox"
- Goals: `Target` icon, "Set your career goals to get started" + [Set Goals] button

**Loading**: Skeleton screens with `animate-pulse` on `bg-slate-200` matching real content dimensions. Immediate display, crossfade to content.

**Errors**: SSE disconnect → yellow banner with auto-retry. API 500 → red toast + retry. API 401 → redirect login. Validation → inline red text below field. Failed optimistic update → revert + toast.

---

### Mobile Responsiveness

| Component | Desktop >=1024 | Mobile <768 |
|-----------|---------------|-------------|
| Sidebar | Fixed w-56 | Hidden, hamburger, slide-in overlay |
| Approval Inbox | Split view (list + detail) | Stacked push navigation |
| Dashboard | 2-column | Single column |
| Opportunity detail | 3-column | Single column |
| Pipeline | Full horizontal | Horizontal scroll |
| Stats row | 4 inline | 2x2 grid |
| Trust thermostat | Horizontal | Vertical |
| Command palette | Centered max-w-lg | Full screen |
| Action buttons | Inline + keyboard hints | Bottom fixed bar (44px touch targets) |

Mobile-specific: bottom fixed action bar on approval detail, pull-to-refresh on feeds, 44x44px touch targets, sticky section headers.

---

### Moat-Building UI Patterns

**1. Decision Memory Visualization**: Every AI decision is logged, explained, searchable. `DecisionCard` expands to show What/Why/Which Rules/What Data. Command palette indexes all decisions — search "Why was CompanyX rejected?" Each includes "Was this right?" feedback (thumbs up/down) feeding the learning model.

**2. Trust Calibration (Thermostat, not YAML)**: `TrustThermostat` is the visual centerpiece. Users drag thresholds, not edit config. Every drag shows real-time impact. Over time, system recommends threshold adjustments based on approval patterns (shown with `Sparkles`).

**3. Pattern Learning Display**: `LearningPanel` surfaces detected behavioral patterns with confidence levels + evidence counts. New patterns animate with Sparkles. "Delegate Report Card" gives periodic summaries: precision, recall, time saved, patterns learned.

**4. Cross-Delegate Awareness**: `EmptyDelegateCard` for future delegates (Calendar, Finance, Social) creates anticipation. Dashed borders, desaturated styling. Optional "Notify me" button captures interest signals.

---

## MVP Scope (6 weeks)

**Week 1 — Foundation (Backend + Frontend scaffold)**
- Backend: Project scaffold, `DelegationPolicy` Pydantic models + YAML loader, `CareerGoals` CRUD + SQLite, `DelegateEvent` models
- Frontend: Next.js 14 + TypeScript + Tailwind + shadcn/ui + Lucide + Framer Motion + Geist font + Zustand. `AppShell`, `Sidebar`, `Topbar`, `PageHeader`. Design tokens in `tailwind.config.ts`. `lib/types.ts`. Empty route stubs for all pages

**Week 2 — Core Backend Pipeline**
- Recruiter pipeline Stages 1–3 (Ingest, Extract, Score). LLM prompt engineering. Unit tests for scorer
- Goals Editor frontend: 5 `GoalSection` cards, `TagInput`, `RangeSlider`, auto-save hook, "What your delegate sees" sidebar

**Week 3 — Pipeline Completion + Approval API**
- Stages 4–6 (Policy check, Draft, Act). `ApprovalItem` API. asyncio polling scheduler (15 min)
- SSE event streaming endpoint. `useEventStream` hook + `eventStore`

**Week 4 — Approval Inbox (the core interaction)**
- `ApprovalCard`, `ApprovalDetail`, `DraftEditor`, `ScoreBadge`, `MatchBreakdown`, `StatusPill`
- Keyboard shortcuts (`j/k` navigate, `a` approve, `r` reject, `Cmd+Enter` approve+next)
- Split view layout. Optimistic updates. Undo toast. `CommandPalette` (Cmd+K)

**Week 5 — Delegate Detail + Policy + Dashboard**
- Dashboard: attention strip, pending approvals, activity feed, `DelegateCard` + `EmptyDelegateCard`
- Delegate detail: `PipelineVisualizer`, `Timeline`, `DecisionCard`, `LearningPanel`
- Policy view: `TrustThermostat` (Framer Motion spring physics), `RuleCard`, `PolicyImpact`

**Week 6 — Integration, Polish, Moat**
- Docker Compose (Redis + backend + frontend). E2E test with sandbox MS365 mailbox
- `ConnectionBanner`, all empty/loading/error states, mobile responsive pass
- Decision memory search in command palette. Pattern learning animations
- OTel tracing verified. Opportunity detail page

**Phase 2**: Auto-approve for low-score declines, Calendar Delegate cross-collaboration, Redis Streams migration, Gmail adapter, preference evolution feedback loop, batch approval mode, Delegate Report Card

---

## Verification

### Unit Tests
- `test_policy_engine.py`: Parametrize over policy YAML fixtures; test every `can_auto_act()` permutation
- `test_scorer.py`: Mock `CareerGoals` + synthetic `JobOpportunity`; assert score ranges
- `test_recruiter_pipeline.py`: Mock `GraphConnector` + LLM calls; assert full `DelegateEvent` sequence

### Integration Tests (adapted from RDT 2 `test_api.py`)
1. Start `TestClient`, POST synthetic recruiter email event to `/v1/jobs`
2. Poll `/v1/jobs/{id}` until terminal state
3. Assert `ApprovalItem` at `/v1/approvals`
4. POST approve to `/v1/approvals/{id}/approve`
5. Assert `RESPONSE_SENT` in `/v1/memory/decisions`

### Manual End-to-End Checklist
1. Point `GraphConnector` at sandbox MS365 mailbox
2. Send test recruiter email to mailbox
3. Trigger `POST /v1/delegates/recruiter/run`
4. Verify approval card appears in UI within 30 seconds
5. Click Approve
6. Verify reply sent from mailbox
7. Verify `DecisionLog` SQLite entry with reasoning + policy trace

---

## Moat Architecture

The moat is NOT the AI. The moat is the compounding data + trust layer.

### Data Flywheel
1. **Behavior data** — every approve/reject/edit teaches the delegate what "right" looks like for this specific user
2. **Policy layer** — constraints evolve with user. A generic assistant resets every session; policies persist and sharpen
3. **Execution history** — every decision is traceable, replayable, searchable. This is the audit trail that builds trust
4. **Memory graph** — relationships (which recruiters are good), decisions (what worked), preferences (what shifted over time)
5. **Cross-surface consistency** — same delegate behavior regardless of which surface triggers it

### UI as Moat
The UI reinforces the flywheel:
- **Trust Thermostat** makes delegation tangible — no other product lets you drag a slider to control AI autonomy and see the impact in real-time
- **Decision Memory** makes AI transparent — "Why did you reject this?" is always one Cmd+K search away
- **Pattern Learning Display** makes AI improvement visible — "Your delegate learned you don't like crypto roles" builds confidence to grant more autonomy
- **Cross-Delegate Awareness** creates platform lock-in before the platform even scales — users see the vision of Calendar, Finance, Social delegates before they exist

### Network Effect (Phase 2+)
- Anonymized aggregate scoring signals ("87% of users with similar goals engaged with this recruiter")
- Recruiter reputation scores across users
- Industry comp benchmarks from extracted JD data
