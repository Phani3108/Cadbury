"use client";

import { Download, FileSearch, BarChart3, Shield, PenLine, Send } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EventType } from "@/lib/types";

// ─── Stage config ─────────────────────────────────────────────────────────────
const STAGES = [
  { id: "ingest",  label: "Ingest",  icon: Download,    events: ["email_received"] as EventType[] },
  { id: "extract", label: "Extract", icon: FileSearch,   events: ["opportunity_extracted"] as EventType[] },
  { id: "score",   label: "Score",   icon: BarChart3,    events: ["opportunity_scored"] as EventType[] },
  { id: "policy",  label: "Policy",  icon: Shield,       events: ["policy_blocked"] as EventType[] },
  { id: "draft",   label: "Draft",   icon: PenLine,      events: ["draft_created"] as EventType[] },
  { id: "act",     label: "Act",     icon: Send,         events: ["approval_requested", "human_approved", "human_rejected", "response_sent"] as EventType[] },
];

type StageState = "idle" | "active" | "complete" | "blocked";

interface PipelineVisualizerProps {
  /** Most recent event types seen (drives which stages are lit) */
  recentEventTypes?: EventType[];
  /** Stage ID to highlight as currently active */
  activeStageId?: string;
  onStageClick?: (stageId: string) => void;
  className?: string;
}

function getStageState(
  stageIdx: number,
  stages: typeof STAGES,
  recentEventTypes: EventType[],
  activeStageId: string | undefined
): StageState {
  const stage = stages[stageIdx];

  if (activeStageId === stage.id) return "active";

  // Check if any of this stage's event types appear in recent events
  const seen = stage.events.some((et) => recentEventTypes.includes(et));
  if (!seen) return "idle";

  if (stage.events.includes("policy_blocked") && recentEventTypes.includes("policy_blocked")) {
    return "blocked";
  }

  // If a later stage has been seen, this one is complete
  const laterSeen = stages
    .slice(stageIdx + 1)
    .some((s) => s.events.some((et) => recentEventTypes.includes(et)));

  return laterSeen ? "complete" : "active";
}

export function PipelineVisualizer({
  recentEventTypes = [],
  activeStageId,
  onStageClick,
  className,
}: PipelineVisualizerProps) {
  return (
    <div className={cn("flex items-center justify-between", className)}>
      {STAGES.map((stage, i) => {
        const Icon = stage.icon;
        const state = getStageState(i, STAGES, recentEventTypes, activeStageId);

        const circleClass = cn(
          "w-9 h-9 rounded-full border-2 flex items-center justify-center transition-all duration-300",
          state === "complete" && "border-green-400 bg-green-50",
          state === "active"  && "border-brand-400 bg-brand-50 ring-2 ring-brand-200 ring-offset-1",
          state === "blocked" && "border-red-400 bg-red-50",
          state === "idle"    && "border-slate-200 bg-slate-50"
        );

        const iconClass = cn(
          "w-4 h-4 transition-colors",
          state === "complete" && "text-green-500",
          state === "active"  && "text-brand-500",
          state === "blocked" && "text-red-400",
          state === "idle"    && "text-slate-300"
        );

        const labelClass = cn(
          "text-[10px] font-medium",
          state === "complete" && "text-green-600",
          state === "active"  && "text-brand-600",
          state === "blocked" && "text-red-500",
          state === "idle"    && "text-slate-300"
        );

        return (
          <div key={stage.id} className="flex items-center flex-1">
            <button
              type="button"
              onClick={() => onStageClick?.(stage.id)}
              className="flex flex-col items-center gap-1.5 focus:outline-none"
            >
              <div className={cn(circleClass, onStageClick && "cursor-pointer hover:shadow-sm")}>
                <Icon className={iconClass} />
              </div>
              <span className={labelClass}>{stage.label}</span>
            </button>

            {/* Connector line */}
            {i < STAGES.length - 1 && (
              <div
                className={cn(
                  "flex-1 h-px mx-2 mb-4 transition-colors duration-300",
                  state === "complete" ? "bg-green-200" : "bg-slate-100"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
