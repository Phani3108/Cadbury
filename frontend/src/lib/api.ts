import type {
  Delegate,
  ApprovalItem,
  ApprovalStatus,
  JobOpportunity,
  CareerGoals,
  DelegationPolicy,
  PolicyImpact,
  DelegateEvent,
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
};

// ─── Bundled export ───────────────────────────────────────────────────────────

export const api = { delegates, approvals, opportunities, goals, events, policy };
