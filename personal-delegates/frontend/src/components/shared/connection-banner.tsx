"use client";

import { WifiOff, Loader2 } from "lucide-react";
import { useEventStore } from "@/stores/event-store";
import { cn } from "@/lib/utils";

export function ConnectionBanner() {
  const { connectionStatus } = useEventStore();

  if (connectionStatus === "connected") return null;

  return (
    <div className={cn(
      "fixed top-0 left-0 right-0 z-[80] h-9 flex items-center justify-center gap-2 text-sm font-medium",
      connectionStatus === "reconnecting"
        ? "bg-amber-400 text-amber-900"
        : "bg-red-500 text-white"
    )}>
      {connectionStatus === "reconnecting" ? (
        <>
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          Reconnecting to live events…
        </>
      ) : (
        <>
          <WifiOff className="w-3.5 h-3.5" />
          Disconnected — some data may be stale
        </>
      )}
    </div>
  );
}
