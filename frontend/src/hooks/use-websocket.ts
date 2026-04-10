"use client";

import { useEffect, useRef, useCallback } from "react";
import { useEventStore } from "@/stores/event-store";
import { useApprovalStore } from "@/stores/approval-store";
import type { DelegateEvent, ApprovalItem, Notification } from "@/lib/types";

const WS_BASE =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    .replace(/^http/, "ws");
const MAX_BACKOFF_MS = 30_000;

/**
 * WebSocket-based real-time event stream.
 * Falls back to SSE (useEventStream) if WebSocket isn't available.
 */
export function useWebSocket(delegateId?: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const backoffRef = useRef(1000);
  const unmountedRef = useRef(false);
  const pingRef = useRef<ReturnType<typeof setInterval>>(undefined);

  const { addEvent, setConnectionStatus } = useEventStore();
  const { addApproval, updateApproval } = useApprovalStore();

  const connect = useCallback(() => {
    if (unmountedRef.current) return;

    const url = `${WS_BASE}/v1/events/ws`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus("connected");
      backoffRef.current = 1000;
      // Keep-alive ping every 25s
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        }
      }, 25_000);
    };

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        const { type, data } = msg;

        if (type === "delegate.event") {
          if (delegateId && data?.delegate_id !== delegateId) return;
          addEvent(data as DelegateEvent);
        } else if (type === "approval.new") {
          addApproval(data as ApprovalItem);
        } else if (type === "approval.resolved") {
          updateApproval(data.approval_id, { status: data.status });
        } else if (type === "notification.new") {
          import("@/stores/notification-store").then(({ useNotificationStore }) => {
            useNotificationStore.getState().addNotification(data as Notification);
          });
        }
        // pong and connected are silently ignored
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      clearInterval(pingRef.current);
      wsRef.current = null;
      if (unmountedRef.current) return;

      setConnectionStatus("reconnecting");
      const delay = backoffRef.current;
      backoffRef.current = Math.min(delay * 2, MAX_BACKOFF_MS);
      setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close(); // triggers onclose → reconnect
    };
  }, [delegateId, addEvent, addApproval, updateApproval, setConnectionStatus]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      clearInterval(pingRef.current);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect]);
}
