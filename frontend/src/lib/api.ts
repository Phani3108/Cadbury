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
  get: (period: "daily" | "weekly" = "daily") =>
    request<DigestReport>(`/v1/digest?period=${period}`),
  send: (period: "daily" | "weekly" = "daily") =>
    request<{ status: string }>(`/v1/digest/send?period=${period}`, { method: "POST" }),
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
};
