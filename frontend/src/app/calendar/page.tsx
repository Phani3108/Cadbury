"use client";

import { useEffect, useState } from "react";
import {
  Calendar as CalendarIcon,
  Clock,
  Users,
  Search,
  X,
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import type { CalendarEvent, CalendarEventStatus, TimeSlot } from "@/lib/types";

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-100 rounded-md ${className ?? ""}`} />;
}

const STATUS_STYLES: Record<CalendarEventStatus, { label: string; className: string }> = {
  proposed: {
    label: "Proposed",
    className: "bg-blue-50 text-blue-700 border-blue-200",
  },
  confirmed: {
    label: "Confirmed",
    className: "bg-green-50 text-green-700 border-green-200",
  },
  tentative: {
    label: "Tentative",
    className: "bg-amber-50 text-amber-700 border-amber-200",
  },
  cancelled: {
    label: "Cancelled",
    className: "bg-red-50 text-red-600 border-red-200",
  },
};

function formatEventTime(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const dateStr = s.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  const startTime = s.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  const endTime = e.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${dateStr} · ${startTime} – ${endTime}`;
}

function formatSlotTime(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const dateStr = s.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  const startTime = s.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  const endTime = e.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${dateStr}, ${startTime} – ${endTime}`;
}

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [slots, setSlots] = useState<TimeSlot[] | null>(null);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  useEffect(() => {
    api.calendar
      .events()
      .then(setEvents)
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, []);

  function handleFindSlots() {
    setSlotsLoading(true);
    setSlots(null);
    api.calendar
      .slots()
      .then(setSlots)
      .catch(() => setSlots([]))
      .finally(() => setSlotsLoading(false));
  }

  function handleCancel(eventId: string) {
    setCancellingId(eventId);
    api.calendar
      .cancel(eventId)
      .then(() => {
        setEvents((prev) =>
          prev.map((ev) =>
            ev.event_id === eventId ? { ...ev, status: "cancelled" as const } : ev
          )
        );
      })
      .catch(() => {})
      .finally(() => setCancellingId(null));
  }

  return (
    <div>
      <PageHeader
        title="Calendar"
        subtitle="Upcoming events managed by your delegates"
        actions={
          <button
            onClick={handleFindSlots}
            disabled={slotsLoading}
            className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors",
              "bg-brand-500 text-white hover:bg-brand-600",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            <Search className="w-3.5 h-3.5" />
            {slotsLoading ? "Searching..." : "Find Available Slots"}
          </button>
        }
      />

      {/* Available Slots Panel */}
      {(slotsLoading || slots !== null) && (
        <div className="bg-white border border-slate-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-900">Available Slots</h2>
            {slots !== null && (
              <button
                onClick={() => setSlots(null)}
                className="text-slate-300 hover:text-slate-500 transition-colors"
                aria-label="Close slots"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {slotsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : slots && slots.length === 0 ? (
            <p className="text-sm text-slate-400 py-3 text-center">
              No available slots found in the requested range.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {slots?.map((slot, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg text-sm hover:border-brand-300 hover:bg-brand-50/30 transition-colors cursor-pointer"
                >
                  <Clock className="w-3.5 h-3.5 text-brand-500 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-700 truncate">
                      {slot.label}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      {formatSlotTime(slot.start, slot.end)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Events */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg">
          <EmptyState
            icon={CalendarIcon}
            title="No calendar events"
            description="Events booked by your delegates will appear here"
          />
        </div>
      ) : (
        <div className="space-y-3">
          {events.map((ev) => {
            const statusConfig = STATUS_STYLES[ev.status];
            const isCancelled = ev.status === "cancelled";

            return (
              <div
                key={ev.event_id}
                className={cn(
                  "bg-white border border-slate-200 rounded-lg p-4 transition-colors",
                  isCancelled && "opacity-60"
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3
                        className={cn(
                          "text-sm font-medium text-slate-900 truncate",
                          isCancelled && "line-through"
                        )}
                      >
                        {ev.title}
                      </h3>
                      <span
                        className={cn(
                          "inline-flex items-center px-1.5 py-0.5 rounded-full border text-[10px] font-medium flex-shrink-0",
                          statusConfig.className
                        )}
                      >
                        {statusConfig.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatEventTime(ev.start_at, ev.end_at)}
                      </span>
                      {ev.attendees.length > 0 && (
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {ev.attendees.length} attendee{ev.attendees.length !== 1 ? "s" : ""}
                        </span>
                      )}
                    </div>

                    {ev.attendees.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {ev.attendees.map((a, i) => (
                          <span
                            key={i}
                            className="inline-block px-1.5 py-0.5 text-[10px] bg-slate-50 text-slate-500 rounded"
                          >
                            {a}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Cancel button */}
                  {!isCancelled && (
                    <button
                      onClick={() => handleCancel(ev.event_id)}
                      disabled={cancellingId === ev.event_id}
                      className={cn(
                        "flex-shrink-0 inline-flex items-center gap-1 px-2 py-1 text-[11px] font-medium rounded-md transition-colors",
                        "text-red-500 hover:bg-red-50 border border-transparent hover:border-red-200",
                        "disabled:opacity-50 disabled:cursor-not-allowed"
                      )}
                    >
                      <X className="w-3 h-3" />
                      {cancellingId === ev.event_id ? "Cancelling..." : "Cancel"}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
