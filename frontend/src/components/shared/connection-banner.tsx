"use client";

import { useEffect, useState } from "react";
import { WifiOff, Loader2, X } from "lucide-react";
import { useEventStore } from "@/stores/event-store";
import { cn } from "@/lib/utils";

export function ConnectionBanner() {
  const { connectionStatus } = useEventStore();
  const [dismissed, setDismissed] = useState(false);
  const [countdown, setCountdown] = useState(10);

  // Reset dismiss when we go back to connected
  useEffect(() => {
    if (connectionStatus === "connected") setDismissed(false);
  }, [connectionStatus]);

  // Countdown for reconnecting attempts
  useEffect(() => {
    if (connectionStatus !== "reconnecting") {
      setCountdown(10);
      return;
    }
    setCountdown(10);
    const id = setInterval(() => {
      setCountdown((c) => (c <= 1 ? 10 : c - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [connectionStatus]);

  if (connectionStatus === "connected" || dismissed) return null;

  const isDisconnected = connectionStatus === "disconnected";

  return (
    <div
      className={cn(
        "fixed top-0 left-0 right-0 z-[80] h-9 flex items-center justify-between px-4 text-xs font-medium",
        isDisconnected ? "bg-red-500 text-white" : "bg-amber-400 text-amber-900"
      )}
    >
      <div className="flex items-center gap-2">
        {isDisconnected ? (
          <WifiOff className="w-3.5 h-3.5" />
        ) : (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        )}
        <span>
          {isDisconnected
            ? "Disconnected — some data may be stale."
            : `Reconnecting to live events… retrying in ${countdown}s`}
        </span>
      </div>

      <div className="flex items-center gap-3">
        {isDisconnected && (
          <button
            onClick={() => window.location.reload()}
            className="underline underline-offset-2 hover:opacity-80"
          >
            Refresh
          </button>
        )}
        <button onClick={() => setDismissed(true)} aria-label="Dismiss banner">
          <X className="w-3.5 h-3.5 hover:opacity-80" />
        </button>
      </div>
    </div>
  );
}
