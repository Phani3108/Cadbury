"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  SlidersHorizontal,
  ArrowRight,
  Loader2,
  FlaskConical,
  XCircle,
  MessageSquare,
  Eye,
  Clock,
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { cn, scoreToColor } from "@/lib/utils";
import { api } from "@/lib/api";
import type { SimulationResult } from "@/lib/types";

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-100 rounded-md ${className ?? ""}`} />;
}

interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}

function ThresholdSlider({ label, value, min, max, step, onChange }: SliderProps) {
  return (
    <div className="flex-1 min-w-[200px]">
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-xs font-medium text-slate-700">{label}</label>
        <span className="text-xs font-mono text-slate-500 bg-slate-50 px-1.5 py-0.5 rounded">
          {value.toFixed(2)}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 bg-slate-200 rounded-full appearance-none cursor-pointer accent-brand-500"
      />
      <div className="flex items-center justify-between mt-0.5">
        <span className="text-[10px] text-slate-300">{min.toFixed(2)}</span>
        <span className="text-[10px] text-slate-300">{max.toFixed(2)}</span>
      </div>
    </div>
  );
}

const ACTION_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  auto_declined: XCircle,
  engaged: MessageSquare,
  reviewed: Eye,
  held: Clock,
};

function ActionLabel({ action }: { action: string }) {
  const Icon = ACTION_ICONS[action] ?? Eye;
  const labels: Record<string, string> = {
    auto_declined: "Auto-declined",
    engaged: "Engaged",
    reviewed: "Reviewed",
    held: "Held",
    auto_decline: "Auto-decline",
    engage: "Engage",
    review: "Review",
    hold: "Hold",
  };
  return (
    <span className="inline-flex items-center gap-1 text-xs text-slate-600">
      <Icon className="w-3 h-3" />
      {labels[action] ?? action}
    </span>
  );
}

export default function PolicySimulatorPage({
  params,
}: {
  params: { id: string };
}) {
  const delegateId = params.id;
  const delegateName = delegateId.charAt(0).toUpperCase() + delegateId.slice(1);
  const router = useRouter();

  const [engagement, setEngagement] = useState(0.65);
  const [autoDeclineBelow, setAutoDeclineBelow] = useState(0.3);
  const [autoDeclineThreshold, setAutoDeclineThreshold] = useState(0.25);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const simulate = useCallback(
    (eng: number, decBelow: number, decThresh: number) => {
      setLoading(true);
      api.policy
        .simulate(delegateId, {
          min_score_for_engagement: eng,
          auto_decline_below: decBelow,
          auto_decline_threshold: decThresh,
        })
        .then(setResult)
        .catch(() => setResult(null))
        .finally(() => {
          setLoading(false);
          setInitialLoad(false);
        });
    },
    [delegateId]
  );

  // Initial simulation on mount
  useEffect(() => {
    simulate(engagement, autoDeclineBelow, autoDeclineThreshold);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Debounced simulation on slider change
  function handleSliderChange(
    setter: (v: number) => void,
    value: number,
    which: "engagement" | "declineBelow" | "declineThreshold"
  ) {
    setter(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const eng = which === "engagement" ? value : engagement;
      const below = which === "declineBelow" ? value : autoDeclineBelow;
      const thresh = which === "declineThreshold" ? value : autoDeclineThreshold;
      simulate(eng, below, thresh);
    }, 500);
  }

  const statCards = result
    ? [
        {
          label: "Would Auto-Decline",
          value: result.would_auto_decline,
          color: "text-red-500",
          bg: "bg-red-50",
        },
        {
          label: "Would Engage",
          value: result.would_engage,
          color: "text-green-600",
          bg: "bg-green-50",
        },
        {
          label: "Would Review",
          value: result.would_review,
          color: "text-amber-600",
          bg: "bg-amber-50",
        },
        {
          label: "Time Saved",
          value: `${result.time_saved_hours}h`,
          color: "text-blue-600",
          bg: "bg-blue-50",
        },
      ]
    : [];

  return (
    <div>
      <PageHeader
        title={`${delegateName} · Policy Simulator`}
        subtitle="Preview how different thresholds would change outcomes"
        actions={
          <button
            onClick={() =>
              router.push(`/delegates/${delegateId}/policy`)
            }
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-brand-500 text-white hover:bg-brand-600 transition-colors"
          >
            Apply these settings
          </button>
        }
      />

      {/* Sliders */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <SlidersHorizontal className="w-4 h-4 text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-900">Thresholds</h2>
          {loading && (
            <Loader2 className="w-3.5 h-3.5 text-brand-500 animate-spin ml-auto" />
          )}
        </div>
        <div className="flex flex-wrap gap-6">
          <ThresholdSlider
            label="Engagement threshold"
            value={engagement}
            min={0}
            max={1}
            step={0.05}
            onChange={(v) =>
              handleSliderChange(setEngagement, v, "engagement")
            }
          />
          <ThresholdSlider
            label="Auto-decline below"
            value={autoDeclineBelow}
            min={0}
            max={1}
            step={0.05}
            onChange={(v) =>
              handleSliderChange(setAutoDeclineBelow, v, "declineBelow")
            }
          />
          <ThresholdSlider
            label="Auto-decline threshold"
            value={autoDeclineThreshold}
            min={0}
            max={1}
            step={0.05}
            onChange={(v) =>
              handleSliderChange(setAutoDeclineThreshold, v, "declineThreshold")
            }
          />
        </div>
      </div>

      {/* Loading skeleton for initial load */}
      {initialLoad && loading && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      )}

      {/* No result */}
      {!loading && !initialLoad && !result && (
        <div className="bg-white border border-slate-200 rounded-lg">
          <EmptyState
            icon={FlaskConical}
            title="Simulation unavailable"
            description="Could not run the policy simulation. Adjust the sliders and try again."
          />
        </div>
      )}

      {/* Results */}
      {result && !initialLoad && (
        <div className="space-y-4">
          {/* Stat cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {statCards.map((card) => (
              <div
                key={card.label}
                className="bg-white border border-slate-200 rounded-lg p-4"
              >
                <p className={cn("text-xl font-bold", card.color)}>
                  {card.value}
                </p>
                <p className="text-[11px] text-slate-400 mt-0.5">{card.label}</p>
              </div>
            ))}
          </div>

          {/* Approval reduction highlight */}
          <div className="bg-brand-50 border border-brand-200 rounded-lg px-5 py-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-900">
                Approval Reduction
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                Percentage reduction in items requiring manual review
              </p>
            </div>
            <p className="text-2xl font-bold text-brand-600">
              {result.approval_reduction_pct}%
            </p>
          </div>

          {/* Changed outcomes table */}
          {result.changed_outcomes.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
              <div className="px-5 py-3 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-900">
                  Changed Outcomes
                  <span className="ml-2 text-xs font-normal text-slate-400">
                    ({result.changed_outcomes.length} opportunit{result.changed_outcomes.length === 1 ? "y" : "ies"})
                  </span>
                </h2>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 text-left">
                      <th className="px-5 py-2 text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                        Company
                      </th>
                      <th className="px-5 py-2 text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-5 py-2 text-[11px] font-medium text-slate-400 uppercase tracking-wider text-right">
                        Score
                      </th>
                      <th className="px-5 py-2 text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                        Actual
                      </th>
                      <th className="px-5 py-2 text-[11px] font-medium text-slate-400 uppercase tracking-wider" />
                      <th className="px-5 py-2 text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                        Simulated
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {result.changed_outcomes.map((row) => (
                      <tr
                        key={row.opportunity_id}
                        className="hover:bg-slate-50/50 transition-colors"
                      >
                        <td className="px-5 py-2.5 text-slate-900 font-medium truncate max-w-[180px]">
                          {row.company}
                        </td>
                        <td className="px-5 py-2.5 text-slate-600 truncate max-w-[200px]">
                          {row.role}
                        </td>
                        <td className={cn("px-5 py-2.5 text-right font-mono text-xs", scoreToColor(row.match_score))}>
                          {Math.round(row.match_score * 100)}%
                        </td>
                        <td className="px-5 py-2.5">
                          <ActionLabel action={row.actual_action} />
                        </td>
                        <td className="px-1 py-2.5">
                          <ArrowRight className="w-3 h-3 text-slate-300" />
                        </td>
                        <td className="px-5 py-2.5">
                          <ActionLabel action={row.simulated_action} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {result.changed_outcomes.length === 0 && (
            <div className="bg-white border border-slate-200 rounded-lg py-8 text-center">
              <p className="text-sm text-slate-400">
                No outcomes would change with these thresholds.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
