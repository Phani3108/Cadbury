"use client";

/**
 * TanStack Query hooks — typed wrappers around api.ts functions.
 * These replace the manual useEffect+fetch+useState pattern.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  api,
  approvals as approvalsApi,
  delegates as delegatesApi,
  events as eventsApi,
  goals as goalsApi,
  notifications as notificationsApi,
  pipelineRuns as pipelineRunsApi,
  search as searchApi,
  chat as chatApi,
  calendar as calendarApi,
  contacts as contactsApi,
  type PipelineRun,
  type SearchResult,
  type ChatSession,
  type ChatMessage,
} from "@/lib/api";
import type {
  Delegate,
  ApprovalItem,
  DelegateEvent,
  CareerGoals,
  Notification,
  CalendarEvent,
  RecruiterContact,
} from "@/lib/types";

// ─── Delegates ───────────────────────────────────────────────────────────────

export function useDelegates() {
  return useQuery<Delegate[]>({
    queryKey: ["delegates"],
    queryFn: () => delegatesApi.list(),
  });
}

export function useDelegate(id: string) {
  return useQuery<Delegate>({
    queryKey: ["delegates", id],
    queryFn: () => delegatesApi.get(id),
    enabled: !!id,
  });
}

// ─── Approvals ───────────────────────────────────────────────────────────────

export function useApprovals(status?: string) {
  return useQuery<ApprovalItem[]>({
    queryKey: ["approvals", status],
    queryFn: () => approvalsApi.list(status as any),
  });
}

// ─── Events ──────────────────────────────────────────────────────────────────

export function useEvents(delegateId?: string, limit = 50) {
  return useQuery<DelegateEvent[]>({
    queryKey: ["events", delegateId, limit],
    queryFn: () => eventsApi.list(delegateId, limit),
  });
}

// ─── Goals ───────────────────────────────────────────────────────────────────

export function useGoals() {
  return useQuery<CareerGoals>({
    queryKey: ["goals"],
    queryFn: () => goalsApi.get(),
  });
}

export function useUpdateGoals() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<CareerGoals>) => goalsApi.update(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
}

// ─── Notifications ───────────────────────────────────────────────────────────

export function useNotifications(unreadOnly = false, limit = 20) {
  return useQuery<Notification[]>({
    queryKey: ["notifications", unreadOnly, limit],
    queryFn: () => notificationsApi.list(unreadOnly, limit),
  });
}

// ─── Calendar ────────────────────────────────────────────────────────────────

export function useCalendarEvents() {
  return useQuery<CalendarEvent[]>({
    queryKey: ["calendar-events"],
    queryFn: () => calendarApi.events(),
  });
}

// ─── Contacts ────────────────────────────────────────────────────────────────

export function useContacts() {
  return useQuery<RecruiterContact[]>({
    queryKey: ["contacts"],
    queryFn: () => contactsApi.list(),
  });
}

// ─── Pipeline Runs ───────────────────────────────────────────────────────────

export function usePipelineRuns(delegateId?: string, status?: string) {
  return useQuery<PipelineRun[]>({
    queryKey: ["pipeline-runs", delegateId, status],
    queryFn: () => pipelineRunsApi.list(delegateId, status),
    refetchInterval: 5_000, // poll while runs are active
  });
}

// ─── Search ──────────────────────────────────────────────────────────────────

export function useSearch(query: string) {
  return useQuery<SearchResult[]>({
    queryKey: ["search", query],
    queryFn: () => searchApi.query(query),
    enabled: query.length >= 2,
    staleTime: 10_000,
  });
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export function useChatSessions(delegateId?: string) {
  return useQuery<ChatSession[]>({
    queryKey: ["chat-sessions", delegateId],
    queryFn: () => chatApi.sessions(delegateId),
  });
}

export function useChatMessages(sessionId: string) {
  return useQuery<ChatMessage[]>({
    queryKey: ["chat-messages", sessionId],
    queryFn: () => chatApi.messages(sessionId),
    enabled: !!sessionId,
  });
}
