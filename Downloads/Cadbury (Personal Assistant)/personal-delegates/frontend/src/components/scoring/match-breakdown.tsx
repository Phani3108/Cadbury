import { cn } from "@/lib/utils";
import type { MatchBreakdown } from "@/lib/types";

const DIMENSION_LABELS: Record<keyof MatchBreakdown, string> = {
  role: "Role Fit",
  comp: "Compensation",
  location: "Location",
  criteria: "Must-Haves",
  company: "Company Signal",
};

const WEIGHTS: Record<keyof MatchBreakdown, number> = {
  comp: 0.35,
  role: 0.30,
  location: 0.20,
  criteria: 0.15,
  company: 0.10,
};

function getBarColor(score: number): string {
  if (score >= 0.8) return "bg-green-500";
  if (score >= 0.5) return "bg-amber-400";
  return "bg-red-400";
}

interface MatchBreakdownProps {
  breakdown: MatchBreakdown;
  className?: string;
  compact?: boolean;
}

export function MatchBreakdownCard({ breakdown, className, compact }: MatchBreakdownProps) {
  const keys = (Object.keys(DIMENSION_LABELS) as (keyof MatchBreakdown)[])
    .sort((a, b) => WEIGHTS[b] - WEIGHTS[a]);

  return (
    <div className={cn("space-y-2.5", className)}>
      {keys.map((key) => {
        const score = breakdown[key];
        const pct = Math.round(score * 100);
        return (
          <div key={key}>
            <div className="flex items-center justify-between mb-1">
              <span className={cn("text-slate-500", compact ? "text-[11px]" : "text-xs")}>
                {DIMENSION_LABELS[key]}
              </span>
              <span className={cn(
                "font-semibold tabular-nums",
                compact ? "text-[11px]" : "text-xs",
                score >= 0.8 ? "text-green-600" : score >= 0.5 ? "text-amber-600" : "text-red-500"
              )}>
                {pct}%
              </span>
            </div>
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all duration-500", getBarColor(score))}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
