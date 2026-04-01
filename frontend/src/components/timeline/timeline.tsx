"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, ThumbsUp, ThumbsDown } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import type { DelegateEvent } from "@/lib/types";

// ─── Event type config ────────────────────────────────────────────────────────
const EVENT_CONFIG: Record<string, { label: string; dotColor: string }> = {
  email_received:        { label: "Email received",        dotColor: "bg-blue-400" },
  opportunity_extracted: { label: "Opportunity extracted", dotColor: "bg-purple-400" },
  opportunity_scored:    { label: "Opportunity scored",    dotColor: "bg-amber-400" },
  draft_created:         { label: "Draft created",         dotColor: "bg-brand-400" },
  approval_requested:    { label: "Approval requested",    dotColor: "bg-orange-400" },
  human_approved:        { label: "Approved by you",       dotColor: "bg-green-500" },
  human_rejected:        { label: "Rejected by you",       dotColor: "bg-red-400" },
  response_sent:         { label: "Response sent",         dotColor: "bg-green-600" },
  calendar_booked:       { label: "Calendar booked",       dotColor: "bg-teal-400" },
  policy_blocked:        { label: "Blocked by policy",     dotColor: "bg-red-500" },
  error:                 { label: "Error",                  dotColor: "bg-red-600" },
};

// ─── DecisionCard ─────────────────────────────────────────────────────────────
interface DecisionCardProps {
  event: DelegateEvent;
}

function DecisionCard({ event }: DecisionCardProps) {
  const [expanded, setExpanded] = useState(false);
  const hasDetail =
    event.reasoning ||
    event.policy_rules_checked.length > 0 ||
    Object.keys(event.payload).length > 0;

  return (
    <div className="pl-4 py-0.5">
      {hasDetail && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-600 transition-colors mb-1"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {expanded ? "Hide details" : "Show details"}
        </button>
      )}
      {expanded && (
        <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 space-y-2 text-xs">
          {/* What */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-0.5">What</p>
            <p className="text-slate-600">{event.summary}</p>
          </div>

          {/* Why */}
          {event.reasoning && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-0.5">Why</p>
              <p className="text-slate-600">{event.reasoning}</p>
            </div>
          )}

          {/* Rules */}
          {event.policy_rules_checked.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1">Rules checked</p>
              <div className="flex flex-wrap gap-1">
                {event.policy_rules_checked.map((rule) => (
                  <span
                    key={rule}
                    className="font-mono text-[10px] bg-white border border-slate-200 text-slate-500 rounded px-1.5 py-0.5"
                  >
                    {rule}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Data */}
          {Object.keys(event.payload).length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-0.5">Data</p>
              <pre className="text-[10px] text-slate-500 overflow-x-auto whitespace-pre-wrap break-all leading-relaxed">
                {JSON.stringify(event.payload, null, 2)}
              </pre>
            </div>
          )}

          {/* Feedback */}
          <div className="flex items-center gap-3 pt-1 border-t border-slate-100">
            <span className="text-[10px] text-slate-400">Was this right?</span>
            <button className="w-6 h-6 flex items-center justify-center rounded hover:bg-green-50 text-slate-300 hover:text-green-500 transition-colors">
              <ThumbsUp className="w-3 h-3" />
            </button>
            <button className="w-6 h-6 flex items-center justify-center rounded hover:bg-red-50 text-slate-300 hover:text-red-400 transition-colors">
              <ThumbsDown className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── TimelineEvent ────────────────────────────────────────────────────────────
interface TimelineEventProps {
  event: DelegateEvent;
  isLast: boolean;
}

function TimelineEventRow({ event, isLast }: TimelineEventProps) {
  const config = EVENT_CONFIG[event.event_type] ?? {
    label: event.event_type,
    dotColor: "bg-slate-300",
  };

  return (
    <div className="flex gap-3">
      {/* Left: dot + line */}
      <div className="flex flex-col items-center flex-shrink-0">
        <div className={cn("w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ring-2 ring-white", config.dotColor)} />
        {!isLast && <div className="w-px flex-1 bg-slate-100 my-1" />}
      </div>

      {/* Right: content */}
      <div className={cn("min-w-0 flex-1", isLast ? "pb-2" : "pb-3")}>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-700 truncate">{config.label}</p>
            {event.summary && (
              <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">{event.summary}</p>
            )}
          </div>
          <span className="text-[10px] text-slate-300 flex-shrink-0 mt-0.5">
            {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
          </span>
        </div>
        <DecisionCard event={event} />
      </div>
    </div>
  );
}

// ─── Timeline ─────────────────────────────────────────────────────────────────
interface TimelineProps {
  events: DelegateEvent[];
  className?: string;
  maxItems?: number;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

export function Timeline({ events, className, maxItems, onLoadMore, hasMore }: TimelineProps) {
  const displayed = maxItems ? events.slice(0, maxItems) : events;

  return (
    <div className={cn("px-4 pt-4", className)}>
      {displayed.map((event, i) => (
        <TimelineEventRow
          key={event.event_id}
          event={event}
          isLast={i === displayed.length - 1 && !hasMore}
        />
      ))}
      {hasMore && (
        <button
          type="button"
          onClick={onLoadMore}
          className="w-full py-2 text-xs text-brand-500 hover:text-brand-600 font-medium"
        >
          Load more events
        </button>
      )}
    </div>
  );
}
