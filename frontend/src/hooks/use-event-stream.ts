"use client";

import { useEffect, useRef, useCallback } from "react";
import { useEventStore } from "@/stores/event-store";
import { useApprovalStore } from "@/stores/approval-store";
import type { DelegateEvent, ApprovalItem } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const MAX_BACKOFF_MS = 30_000;

export function useEventStream(delegateId?: string) {
  const esRef = useRef<EventSource | null>(null);
  const backoffRef = useRef(1000);
  const unmountedRef = useRef(false);

  const { addEvent, setConnectionStatus } = useEventStore();
  const { addApproval, updateApproval } = useApprovalStore();

  const connect = useCallback(() => {
    if (unmountedRef.current) return;

    const qs = delegateId ? `?delegate_id=${delegateId}` : "";
    const url = `${API_BASE}/v1/events/stream${qs}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => {
      setConnectionStatus("connected");
      backoffRef.current = 1000; // reset backoff on success
    };

    es.addEventListener("delegate.event", (e: MessageEvent) => {
      try {
        const event: DelegateEvent = JSON.parse(e.data);
        addEvent(event);
      } catch {}
    });

    es.addEventListener("approval.new", (e: MessageEvent) => {
      try {
        const approval: ApprovalItem = JSON.parse(e.data);
        addApproval(approval);
      } catch {}
    });

    es.addEventListener("approval.resolved", (e: MessageEvent) => {
      try {
        const { approval_id, status } = JSON.parse(e.data);
        updateApproval(approval_id, { status });
      } catch {}
    });

    es.onerror = () => {
      es.close();
      esRef.current = null;
      if (unmountedRef.current) return;

      setConnectionStatus("reconnecting");
      const delay = backoffRef.current;
      backoffRef.current = Math.min(delay * 2, MAX_BACKOFF_MS);
      setTimeout(connect, delay);
    };
  }, [delegateId, addEvent, addApproval, updateApproval, setConnectionStatus]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      esRef.current?.close();
      esRef.current = null;
    };
  }, [connect]);
}
