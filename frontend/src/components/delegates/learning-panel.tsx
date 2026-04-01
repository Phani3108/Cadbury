"use client";

import { Sparkles, TrendingUp, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DelegateEvent } from "@/lib/types";

interface Pattern {
  label: string;
  description: string;
  confidence: number; // 0-1
  evidence: number;   // count
}

/** Derive simple behavioral patterns from event history. */
function derivePatterns(events: DelegateEvent[]): Pattern[] {
  const scored = events.filter((e) => e.event_type === "opportunity_scored");
  const approved = events.filter((e) => e.event_type === "human_approved");
  const rejected = events.filter((e) => e.event_type === "human_rejected");
  const blocked = events.filter((e) => e.event_type === "policy_blocked");

  const patterns: Pattern[] = [];

  if (rejected.length >= 2) {
    patterns.push({
      label: "Low-score rejections",
      description: `${rejected.length} opportunities rejected — delegate is learning your standards`,
      confidence: Math.min(0.4 + rejected.length * 0.1, 0.9),
      evidence: rejected.length,
    });
  }

  if (approved.length >= 1) {
    patterns.push({
      label: "Approval pattern",
      description: `${approved.length} item${approved.length !== 1 ? "s" : ""} approved — delegate learns what good looks like`,
      confidence: Math.min(0.5 + approved.length * 0.1, 0.95),
      evidence: approved.length,
    });
  }

  if (blocked.length >= 1) {
    patterns.push({
      label: "Policy blocks working",
      description: `${blocked.length} low-quality pitch${blocked.length !== 1 ? "es" : ""} blocked automatically`,
      confidence: 0.99,
      evidence: blocked.length,
    });
  }

  if (scored.length >= 5) {
    patterns.push({
      label: "Consistent scoring",
      description: `${scored.length} opportunities scored — scoring model is reliable`,
      confidence: Math.min(0.6 + scored.length * 0.02, 0.95),
      evidence: scored.length,
    });
  }

  return patterns;
}

interface LearningPanelProps {
  events: DelegateEvent[];
  stats: {
    processed_today: number;
    pending_approvals: number;
    auto_rate: number;
    avg_score: number;
  };
  className?: string;
}

export function LearningPanel({ events, stats, className }: LearningPanelProps) {
  const patterns = derivePatterns(events);

  const autoCount = Math.round(stats.auto_rate * stats.processed_today);
  const reviewCount = stats.processed_today - autoCount;

  return (
    <div className={cn("space-y-4", className)}>
      {/* Delegation distribution bar */}
      <div>
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Delegation breakdown
        </p>
        <div className="flex rounded-full overflow-hidden h-2 bg-slate-100">
          {autoCount > 0 && (
            <div
              className="bg-green-400 transition-all duration-500"
              style={{ width: `${(autoCount / Math.max(stats.processed_today, 1)) * 100}%` }}
            />
          )}
          {reviewCount > 0 && (
            <div
              className="bg-amber-300 transition-all duration-500"
              style={{ width: `${(reviewCount / Math.max(stats.processed_today, 1)) * 100}%` }}
            />
          )}
          {stats.pending_approvals > 0 && (
            <div
              className="bg-orange-300 transition-all duration-500"
              style={{ width: `${(stats.pending_approvals / Math.max(stats.processed_today + stats.pending_approvals, 1)) * 100}%` }}
            />
          )}
        </div>
        <div className="flex items-center gap-4 mt-2">
          <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
            <span className="w-2 h-2 rounded-full bg-green-400" />
            Auto ({autoCount})
          </span>
          <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
            <span className="w-2 h-2 rounded-full bg-amber-300" />
            Reviewed ({reviewCount})
          </span>
          <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
            <span className="w-2 h-2 rounded-full bg-orange-300" />
            Pending ({stats.pending_approvals})
          </span>
        </div>
      </div>

      {/* Avg score */}
      {stats.avg_score > 0 && (
        <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 rounded-lg px-3 py-2">
          <TrendingUp className="w-3.5 h-3.5 text-brand-400" />
          Average match score: <span className="font-semibold text-slate-700">{Math.round(stats.avg_score * 100)}%</span>
        </div>
      )}

      {/* Patterns */}
      {patterns.length > 0 ? (
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Detected patterns
          </p>
          <div className="space-y-3">
            {patterns.map((pattern) => (
              <div key={pattern.label} className="space-y-1.5">
                <div className="flex items-start gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-brand-400 flex-shrink-0 mt-0.5" />
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-700">{pattern.label}</p>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{pattern.description}</p>
                  </div>
                </div>
                {/* Confidence bar */}
                <div className="pl-5">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-300 rounded-full transition-all duration-700"
                        style={{ width: `${pattern.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-slate-400 tabular-nums">
                      {Math.round(pattern.confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-2 text-xs text-slate-400 bg-slate-50 rounded-lg px-3 py-3">
          <Clock className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>Patterns will appear after the delegate processes more opportunities.</span>
        </div>
      )}
    </div>
  );
}
