import type {
  Delegate,
  ApprovalItem,
  ApprovalStatus,
  JobOpportunity,
  CareerGoals,
  DelegationPolicy,
  PolicyImpact,
  DelegateEvent,
  PatternInsight,
  CalendarEvent,
  TimeSlot,
  Notification,
  DigestReport,
  RecruiterContact,
  SimulationResult,
  CommsMessage,
  FinanceTransaction,
  FinanceSubscription,
  WatchItem,
  LearningPath,
  HealthRoutine,
  HealthAppointment,
  SystemHealth,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.json() as Promise<T>;
}

// ─── Delegates ────────────────────────────────────────────────────────────────

export const delegates = {
  list: () => request<Delegate[]>("/v1/delegates"),
  get: (id: string) => request<Delegate>(`/v1/delegates/${id}`),
  pause: (id: string) => request<void>(`/v1/delegates/${id}/pause`, { method: "POST" }),
  resume: (id: string) => request<void>(`/v1/delegates/${id}/resume`, { method: "POST" }),
  runRecruiter: () => request<{ trace_id: string }>("/v1/delegates/recruiter/run", { method: "POST" }),
};

// ─── Approvals ────────────────────────────────────────────────────────────────

export const approvals = {
  list: (status?: ApprovalStatus) => {
    const qs = status ? `?status=${status}` : "";
    return request<ApprovalItem[]>(`/v1/approvals${qs}`);
  },
  get: (id: string) => request<ApprovalItem>(`/v1/approvals/${id}`),
  approve: (id: string) =>
    request<void>(`/v1/approvals/${id}/approve`, { method: "POST" }),
  reject: (id: string, reason?: string) =>
    request<void>(`/v1/approvals/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  edit: (id: string, draft: string) =>
    request<void>(`/v1/approvals/${id}/edit`, {
      method: "POST",
      body: JSON.stringify({ draft_content: draft }),
    }),
  approveWithDraft: (id: string, draft: string) =>
    request<void>(`/v1/approvals/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ draft_content: draft }),
    }),
};

// ─── Opportunities ────────────────────────────────────────────────────────────

export const opportunities = {
  list: () => request<JobOpportunity[]>("/v1/memory/opportunities"),
  get: (id: string) => request<JobOpportunity>(`/v1/memory/opportunities/${id}`),
  batch: (ids: string[]) => {
    if (!ids.length) return Promise.resolve({} as Record<string, JobOpportunity>);
    const qs = ids.map((id) => `ids=${encodeURIComponent(id)}`).join("&");
    return request<Record<string, JobOpportunity>>(`/v1/memory/opportunities/batch?${qs}`);
  },
};

// ─── Goals ────────────────────────────────────────────────────────────────────

export const goals = {
  get: () => request<CareerGoals>("/v1/user/goals"),
  update: (data: Partial<CareerGoals>) =>
    request<CareerGoals>("/v1/user/goals", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};

// ─── Events / Timeline ────────────────────────────────────────────────────────

export const events = {
  list: (delegateId?: string, limit = 50) => {
    const qs = new URLSearchParams();
    if (delegateId) qs.set("delegate_id", delegateId);
    qs.set("limit", String(limit));
    return request<DelegateEvent[]>(`/v1/events?${qs}`);
  },
};

// ─── Policy ───────────────────────────────────────────────────────────────────

export const policy = {
  get: (delegateId: string) =>
    request<DelegationPolicy>(`/v1/delegates/${delegateId}/policy`),
  impact: (delegateId: string) =>
    request<PolicyImpact>(`/v1/delegates/${delegateId}/policy/impact`),
  update: (delegateId: string, data: Partial<DelegationPolicy>) =>
    request<DelegationPolicy>(`/v1/delegates/${delegateId}/policy`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  simulate: (delegateId: string, thresholds: {
    min_score_for_engagement: number;
    auto_decline_below: number;
    auto_decline_threshold: number;
    period_days?: number;
  }) =>
    request<SimulationResult>(`/v1/delegates/${delegateId}/policy/simulate`, {
      method: "POST",
      body: JSON.stringify(thresholds),
    }),
};

// ─── Learning ─────────────────────────────────────────────────────────────────

export const learning = {
  patterns: (delegateId: string) =>
    request<PatternInsight[]>(`/v1/delegates/${delegateId}/learning/patterns`),
  applySuggestion: (delegateId: string, suggestion: {
    type: string;
    field: string;
    action: string;
    value: string;
  }) =>
    request<{ status: string }>(`/v1/delegates/${delegateId}/learning/apply-suggestion`, {
      method: "POST",
      body: JSON.stringify(suggestion),
    }),
};

// ─── Calendar ─────────────────────────────────────────────────────────────────

export const calendar = {
  slots: (fromDate?: string, toDate?: string, durationMins = 60) => {
    const qs = new URLSearchParams();
    if (fromDate) qs.set("from_date", fromDate);
    if (toDate) qs.set("to_date", toDate);
    qs.set("duration_mins", String(durationMins));
    return request<TimeSlot[]>(`/v1/calendar/slots?${qs}`);
  },
  book: (data: { opportunity_id?: string; slot_start: string; slot_end: string; title: string; attendees?: string[] }) =>
    request<CalendarEvent>("/v1/calendar/book", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  events: () => request<CalendarEvent[]>("/v1/calendar/events"),
  cancel: (eventId: string) =>
    request<void>(`/v1/calendar/events/${eventId}/cancel`, { method: "POST" }),
};

// ─── Notifications ────────────────────────────────────────────────────────────

export const notifications = {
  list: (unreadOnly = false, limit = 20) => {
    const qs = new URLSearchParams();
    if (unreadOnly) qs.set("unread_only", "true");
    qs.set("limit", String(limit));
    return request<Notification[]>(`/v1/notifications?${qs}`);
  },
  markRead: (id: string) =>
    request<void>(`/v1/notifications/${id}/read`, { method: "POST" }),
  markAllRead: () =>
    request<void>("/v1/notifications/read-all", { method: "POST" }),
};

// ─── Contacts ─────────────────────────────────────────────────────────────────

export const contacts = {
  list: () => request<RecruiterContact[]>("/v1/contacts"),
  get: (id: string) => request<RecruiterContact>(`/v1/contacts/${id}`),
};

// ─── Digest ───────────────────────────────────────────────────────────────────

export const digest = {
  get: (period: "daily" | "weekly" = "daily", scope: "all" | "recruiter" = "all") =>
    request<DigestReport>(`/v1/digest?period=${period}&scope=${scope}`),
  send: (period: "daily" | "weekly" = "daily") =>
    request<{ status: string; channels?: Record<string, boolean> }>(`/v1/digest/send?period=${period}`, { method: "POST" }),
};

// ─── Comms ────────────────────────────────────────────────────────────────────

export const comms = {
  messages: (channel?: string, limit = 50) => {
    const qs = new URLSearchParams();
    if (channel) qs.set("channel", channel);
    qs.set("limit", String(limit));
    return request<CommsMessage[]>(`/v1/comms/messages?${qs}`);
  },
  ingest: (data: { channel: string; sender: string; sender_name?: string; subject?: string; body?: string }) =>
    request<{ ingested: number; classified: number; drafts: number }>("/v1/comms/ingest", {
      method: "POST", body: JSON.stringify(data),
    }),
};

// ─── Finance ──────────────────────────────────────────────────────────────────

export const finance = {
  transactions: (limit = 100) =>
    request<FinanceTransaction[]>(`/v1/finance/transactions?limit=${limit}`),
  addTransaction: (data: { amount: number; merchant: string; category?: string; notes?: string }) =>
    request<{ ingested: number; alerts: unknown[] }>("/v1/finance/transactions", {
      method: "POST", body: JSON.stringify(data),
    }),
  subscriptions: (status?: string) => {
    const qs = status ? `?status=${status}` : "";
    return request<FinanceSubscription[]>(`/v1/finance/subscriptions${qs}`);
  },
  cancelSubscription: (id: string) =>
    request<{ status: string }>(`/v1/finance/subscriptions/${id}/cancel`, { method: "POST" }),
};

// ─── Shopping ─────────────────────────────────────────────────────────────────

export const shopping = {
  watchlist: (status?: string) => {
    const qs = status ? `?status=${status}` : "";
    return request<WatchItem[]>(`/v1/shopping/watchlist${qs}`);
  },
  addItem: (data: { name: string; target_price?: number; url?: string; retailer?: string }) =>
    request<WatchItem>("/v1/shopping/watchlist", {
      method: "POST", body: JSON.stringify(data),
    }),
  updatePrice: (itemId: string, price: number) =>
    request<{ items_checked: number; price_drops: unknown[] }>(`/v1/shopping/watchlist/${itemId}/update-price`, {
      method: "POST", body: JSON.stringify({ item_id: itemId, price }),
    }),
  removeItem: (itemId: string) =>
    request<{ status: string }>(`/v1/shopping/watchlist/${itemId}`, { method: "DELETE" }),
};

// ─── Learning ─────────────────────────────────────────────────────────────────

export const learningPaths = {
  list: () => request<LearningPath[]>("/v1/learning/paths"),
  get: (pathId: string) => request<LearningPath>(`/v1/learning/paths/${pathId}`),
  assess: () =>
    request<{ skill_gaps: { skill: string; priority: string }[]; paths_created: number }>("/v1/learning/assess", { method: "POST" }),
  completeResource: (pathId: string, resourceIndex: number, completed: boolean) =>
    request<{ progress_pct: number }>(`/v1/learning/paths/${pathId}/complete-resource`, {
      method: "POST", body: JSON.stringify({ resource_index: resourceIndex, completed }),
    }),
};

// ─── Health ───────────────────────────────────────────────────────────────────

export const health = {
  routines: (activeOnly = true) =>
    request<HealthRoutine[]>(`/v1/health/routines?active_only=${activeOnly}`),
  addRoutine: (data: { name: string; routine_type?: string; frequency?: string; time_of_day?: string }) =>
    request<HealthRoutine>("/v1/health/routines", {
      method: "POST", body: JSON.stringify(data),
    }),
  logRoutine: (routineId: string) =>
    request<{ logged: boolean; streak: number }>(`/v1/health/routines/${routineId}/log`, { method: "POST" }),
  appointments: (status?: string) => {
    const qs = status ? `?status=${status}` : "";
    return request<HealthAppointment[]>(`/v1/health/appointments${qs}`);
  },
  addAppointment: (data: { title: string; provider?: string; appointment_type?: string; scheduled_at?: string; notes?: string }) =>
    request<HealthAppointment>("/v1/health/appointments", {
      method: "POST", body: JSON.stringify(data),
    }),
  check: () =>
    request<{ routines_checked: number; reminders: string[]; alerts: string[] }>("/v1/health/check", { method: "POST" }),
};

// ─── Observability ────────────────────────────────────────────────────────────

export const observability = {
  health: () => request<SystemHealth>("/v1/observability/health"),
  metrics: () => request<Record<string, unknown>>("/v1/observability/metrics"),
};

// ─── Budgets ──────────────────────────────────────────────────────────────────

export interface BudgetResponse {
  delegate_id: string;
  daily_token_limit: number;
  daily_cost_limit_usd: number;
  tokens_used_today: number;
  cost_used_today_usd: number;
  total_tokens_all_time: number;
  total_cost_all_time_usd: number;
  is_over_budget: boolean;
  token_usage_pct: number;
  cost_usage_pct: number;
}

export const budgets = {
  get: (delegateId: string) =>
    request<BudgetResponse>(`/v1/budgets/${delegateId}`),
  update: (delegateId: string, data: { daily_token_limit?: number; daily_cost_limit_usd?: number }) =>
    request<BudgetResponse>(`/v1/budgets/${delegateId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  listAll: () =>
    request<{ budgets: BudgetResponse[]; global_usage: Record<string, unknown> }>("/v1/budgets"),
};

// ─── Auth / OAuth ─────────────────────────────────────────────────────────────

export const auth = {
  status: () => request<{ microsoft: boolean; google: boolean }>("/v1/auth/status"),
  disconnect: (provider: string) =>
    request<{ disconnected: boolean }>(`/v1/auth/${provider}/disconnect`, { method: "POST" }),
  loginUrl: (provider: string) => `${API_BASE}/v1/auth/${provider}/login`,
};

// ─── Pipeline Runs ────────────────────────────────────────────────────────────

export interface PipelineRun {
  id: string;
  delegate_id: string;
  trace_id: string;
  status: "running" | "completed" | "failed";
  stage: string | null;
  error: string | null;
  summary: string | null;
  started_at: string;
  completed_at: string | null;
}

export const pipelineRuns = {
  list: (delegateId?: string, status?: string, limit = 50) => {
    const qs = new URLSearchParams();
    if (delegateId) qs.set("delegate_id", delegateId);
    if (status) qs.set("status", status);
    qs.set("limit", String(limit));
    return request<PipelineRun[]>(`/v1/pipeline-runs?${qs}`);
  },
  get: (id: string) => request<PipelineRun>(`/v1/pipeline-runs/${id}`),
};

// ─── Search ───────────────────────────────────────────────────────────────────

export interface SearchResult {
  type: string;
  data: Record<string, unknown>;
}

export const search = {
  query: (q: string, limit = 20) =>
    request<SearchResult[]>(`/v1/search?q=${encodeURIComponent(q)}&limit=${limit}`),
};

// ─── Chat ─────────────────────────────────────────────────────────────────────

export interface ChatSession {
  id: string;
  delegate_id: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export const chat = {
  sessions: (delegateId?: string, limit = 50) => {
    const qs = new URLSearchParams();
    if (delegateId) qs.set("delegate_id", delegateId);
    qs.set("limit", String(limit));
    return request<ChatSession[]>(`/v1/chat/sessions?${qs}`);
  },
  createSession: (delegateId: string) =>
    request<ChatSession>(`/v1/chat/sessions?delegate_id=${delegateId}`, { method: "POST" }),
  messages: (sessionId: string, limit = 200) =>
    request<ChatMessage[]>(`/v1/chat/sessions/${sessionId}/messages?limit=${limit}`),
  send: (sessionId: string, content: string) =>
    request<{ user_message: ChatMessage; assistant_message: ChatMessage }>(
      `/v1/chat/sessions/${sessionId}/messages`,
      { method: "POST", body: JSON.stringify({ content }) },
    ),
};

// ─── Bundled export ───────────────────────────────────────────────────────────

export const api = {
  delegates,
  approvals,
  opportunities,
  goals,
  events,
  policy,
  learning,
  calendar,
  notifications,
  contacts,
  digest,
  budgets,
  auth,
  comms,
  finance,
  shopping,
  learningPaths,
  health,
  observability,
  pipelineRuns,
  search,
  chat,
};
