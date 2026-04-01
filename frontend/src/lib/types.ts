// ─── Delegates ────────────────────────────────────────────────────────────────

export type DelegateId = "recruiter" | "calendar" | "finance" | "comms" | "travel" | "shopping";

export type DelegateStatus = "active" | "paused" | "error" | "setup_required";

export interface Delegate {
  id: DelegateId;
  name: string;
  description: string;
  status: DelegateStatus;
  last_active: string | null;
  stats: {
    processed_today: number;
    pending_approvals: number;
    auto_rate: number; // 0-1
    avg_score: number; // 0-1
  };
}

// ─── Events ───────────────────────────────────────────────────────────────────

export type EventType =
  | "email_received"
  | "opportunity_extracted"
  | "opportunity_scored"
  | "draft_created"
  | "approval_requested"
  | "human_approved"
  | "human_rejected"
  | "response_sent"
  | "calendar_booked"
  | "policy_blocked"
  | "error";

export interface DelegateEvent {
  event_id: string;
  delegate_id: DelegateId;
  event_type: EventType;
  timestamp: string;
  payload: Record<string, unknown>;
  parent_event_id: string | null;
  trace_id: string | null;
  risk_score: number;
  requires_approval: boolean;
  summary: string; // human-readable description
  reasoning: string | null;
  policy_rules_checked: string[];
}

// ─── Approvals ────────────────────────────────────────────────────────────────

export type ApprovalStatus = "pending" | "approved" | "rejected" | "skipped" | "expired";

export interface ApprovalItem {
  approval_id: string;
  delegate_id: DelegateId;
  event_id: string;
  opportunity_id: string | null;
  action: string;
  action_label: string;
  context_summary: string;
  draft_content: string | null;
  risk_score: number;
  reasoning: string;
  policy_check: Record<string, unknown>;
  created_at: string;
  expires_at: string | null;
  status: ApprovalStatus;
  opportunity?: JobOpportunity;
}

// ─── Job Opportunities ────────────────────────────────────────────────────────

export type OpportunityStatus =
  | "received"
  | "extracted"
  | "scored"
  | "draft_created"
  | "approval_pending"
  | "responded"
  | "rejected"
  | "scheduled";

export interface MatchBreakdown {
  role: number;       // 0-1
  comp: number;       // 0-1
  location: number;   // 0-1
  criteria: number;   // 0-1
  company: number;    // 0-1
}

export interface RecruiterContact {
  contact_id: string;
  name: string;
  email: string;
  company: string;
  title: string;
  first_contact: string;
  interaction_count: number;
  trust_score: number; // 0-1
}

export interface JobOpportunity {
  opportunity_id: string;
  contact_id: string;
  contact?: RecruiterContact;
  company: string;
  role: string;
  comp_range_min: number | null;
  comp_range_max: number | null;
  location: string;
  remote_policy: "remote" | "hybrid" | "onsite" | "unknown";
  equity: string | null;
  jd_summary: string | null;
  match_score: number; // 0-1
  match_breakdown: MatchBreakdown;
  status: OpportunityStatus;
  created_at: string;
  updated_at: string;
  email_subject: string | null;
  email_id: string | null;
}

// ─── Career Goals ─────────────────────────────────────────────────────────────

export interface CareerGoals {
  user_id: string;
  target_roles: string[];
  min_comp_usd: number;
  preferred_locations: string[];
  open_to_relocation: boolean;
  work_style: "remote" | "hybrid" | "onsite" | "any";
  must_have_criteria: string[];
  dealbreakers: string[];
  company_stages: string[];
  preferred_industries: string[];
  avoid_companies: string[];
  comp_includes_equity: boolean;
  comp_includes_bonus: boolean;
  communication_tone: "professional" | "casual" | "formal";
  updated_at: string;
}

// ─── Policy ───────────────────────────────────────────────────────────────────

export type TrustZone = "auto" | "review" | "block";

export interface ActionPermission {
  action: string;
  action_label: string;
  zone: TrustZone;
  auto_approve: boolean;
  threshold: number | null;
}

export interface DelegationPolicy {
  version: number;
  delegate_id: DelegateId;
  thresholds: {
    auto_approve_above: number;   // score above this → auto
    review_between_min: number;   // score in range → review
    review_between_max: number;
    auto_reject_below: number;    // score below this → auto-reject
  };
  allowed_actions: ActionPermission[];
  risk_boundary: {
    max_financial_commitment: number;
    max_calendar_commitment_hours: number;
    max_autonomy_score: number;
  };
  approval_required_for: string[];
  updated_at: string;
}

export interface PolicyImpact {
  period_days: number;
  total_processed: number;
  auto_approved: number;
  reviewed: number;
  auto_rejected: number;
  estimated_time_saved_hours: number;
}

// ─── Learning Patterns ────────────────────────────────────────────────────────

export interface PatternInsight {
  label: string;
  description: string;
  confidence: number; // 0-1
  evidence: number;   // sample count
}

// ─── Real-time / SSE ──────────────────────────────────────────────────────────

export type ConnectionStatus = "connected" | "reconnecting" | "disconnected";

export interface SSEMessage {
  type: string;
  data: unknown;
  timestamp: string;
}
