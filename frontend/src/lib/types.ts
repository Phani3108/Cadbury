// ─── Delegates ────────────────────────────────────────────────────────────────

export type DelegateId = "recruiter" | "calendar" | "comms" | "finance" | "shopping" | "learning" | "health";

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
  | "auto_declined"
  | "calendar_booked"
  | "calendar_cancelled"
  | "calendar_preblock_requested"
  | "calendar_slots_found"
  | "calendar_proposed"
  | "message_received"
  | "message_classified"
  | "message_routed"
  | "message_drafted"
  | "message_sent"
  | "message_archived"
  | "transaction_ingested"
  | "recurring_detected"
  | "spending_alert"
  | "subscription_flagged"
  | "price_tracked"
  | "price_drop"
  | "deal_found"
  | "skill_assessed"
  | "learning_path_created"
  | "learning_progress"
  | "learning_nudge"
  | "health_reminder"
  | "health_appointment"
  | "health_routine_logged"
  | "health_alert"
  | "policy_blocked"
  | "notification_created"
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
  jd_text: string | null;
  match_score: number; // 0-1
  match_breakdown: MatchBreakdown;
  status: OpportunityStatus;
  created_at: string;
  updated_at: string;
  email_subject: string | null;
  email_id: string | null;
  thread_id: string | null;
  company_enrichment: Record<string, unknown>;
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

// ─── Calendar ────────────────────────────────────────────────────────────────

export type CalendarEventStatus = "proposed" | "confirmed" | "tentative" | "cancelled";

export interface CalendarEvent {
  event_id: string;
  opportunity_id: string | null;
  title: string;
  start_at: string;
  end_at: string;
  attendees: string[];
  status: CalendarEventStatus;
  provider_event_id: string | null;
  delegate_id: string;
  created_at: string;
}

export interface TimeSlot {
  start: string;
  end: string;
  label: string;
}

// ─── Notifications ───────────────────────────────────────────────────────────

export type NotificationType =
  | "new_approval"
  | "high_match"
  | "auto_acted"
  | "digest_ready"
  | "threshold_crossed";

export interface Notification {
  notification_id: string;
  type: NotificationType;
  title: string;
  body: string;
  link: string;
  read: boolean;
  created_at: string;
}

// ─── Digest ──────────────────────────────────────────────────────────────────

export interface DigestReport {
  period: string;
  generated_at: string;
  highlights: string[];
  action_items: string[];
  stats: Record<string, number>;
  summary: string;
}

// ─── Learning Patterns ────────────────────────────────────────────────────────

export interface PatternInsight {
  label: string;
  description: string;
  confidence: number; // 0-1
  evidence: number;   // sample count
  pattern_type?: string;
  suggested_action?: {
    type: string;
    field: string;
    action: string;
    value: string;
    reason: string;
  } | null;
}

// ─── Policy Simulation ───────────────────────────────────────────────────────

export interface SimulationResult {
  period_days: number;
  total_opportunities: number;
  would_auto_decline: number;
  would_engage: number;
  would_hold: number;
  would_review: number;
  changed_outcomes: {
    opportunity_id: string;
    company: string;
    role: string;
    match_score: number;
    actual_action: string;
    simulated_action: string;
    reason: string;
  }[];
  time_saved_hours: number;
  approval_reduction_pct: number;
}

// ─── Real-time / SSE ──────────────────────────────────────────────────────────

export type ConnectionStatus = "connected" | "reconnecting" | "disconnected";

export interface SSEMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

// ─── Comms ────────────────────────────────────────────────────────────────────

export type MessageChannel = "email" | "telegram" | "whatsapp" | "slack" | "sms";
export type MessagePriority = "urgent" | "high" | "normal" | "low" | "spam";

export interface CommsMessage {
  message_id: string;
  channel: MessageChannel;
  sender: string;
  sender_name: string;
  subject: string;
  body: string;
  priority: MessagePriority;
  category: string;
  reply_draft: string | null;
  action_taken: string;
  created_at: string;
}

// ─── Finance ──────────────────────────────────────────────────────────────────

export interface FinanceTransaction {
  transaction_id: string;
  amount: number;
  currency: string;
  merchant: string;
  category: string;
  date: string;
  is_recurring: boolean;
  notes: string;
}

export interface FinanceSubscription {
  subscription_id: string;
  merchant: string;
  amount: number;
  currency: string;
  period_days: number;
  status: string;
  usage_rating: string;
  created_at: string;
}

// ─── Shopping ─────────────────────────────────────────────────────────────────

export interface WatchItem {
  item_id: string;
  name: string;
  target_price: number | null;
  current_price: number | null;
  url: string;
  retailer: string;
  price_history: { date: string; price: number }[];
  alert_on_drop: boolean;
  status: string;
  created_at: string;
}

// ─── Learning ─────────────────────────────────────────────────────────────────

export interface SkillGap {
  skill: string;
  current_level: string;
  target_level: string;
  priority: string;
  related_roles: string[];
}

export interface LearningPath {
  path_id: string;
  title: string;
  skill_gaps: SkillGap[];
  resources: { title: string; url: string; type: string; completed: boolean }[];
  progress_pct: number;
  created_at: string;
  updated_at: string;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export interface HealthRoutine {
  routine_id: string;
  name: string;
  routine_type: string;
  frequency: string;
  time_of_day: string;
  last_logged: string | null;
  streak_days: number;
  active: boolean;
  created_at: string;
}

export interface HealthAppointment {
  appointment_id: string;
  title: string;
  provider: string;
  appointment_type: string;
  scheduled_at: string | null;
  status: string;
  notes: string;
  created_at: string;
}

// ─── Observability ────────────────────────────────────────────────────────────

export interface SystemHealth {
  status: string;
  timestamp: string;
  pending_approvals: number;
  events_24h: number;
  errors_24h: number;
  delegates: Record<string, {
    status: string;
    runs_24h: number;
    errors_24h: number;
    avg_duration_s: number;
    error_rate: number;
  }>;
}
