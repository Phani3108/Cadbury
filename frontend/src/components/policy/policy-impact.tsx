import { Clock, CheckCheck, Eye, ShieldX } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PolicyImpact } from "@/lib/types";

interface PolicyImpactCardProps {
  impact: PolicyImpact;
  className?: string;
}

export function PolicyImpactCard({ impact, className }: PolicyImpactCardProps) {
  const total = Math.max(impact.total_processed, 1);

  const stats = [
    {
      label: "Auto-approved",
      value: impact.auto_approved,
      pct: Math.round((impact.auto_approved / total) * 100),
      icon: CheckCheck,
      colorClass: "text-green-600",
      bgClass: "bg-green-50",
    },
    {
      label: "Reviewed",
      value: impact.reviewed,
      pct: Math.round((impact.reviewed / total) * 100),
      icon: Eye,
      colorClass: "text-amber-600",
      bgClass: "bg-amber-50",
    },
    {
      label: "Auto-rejected",
      value: impact.auto_rejected,
      pct: Math.round((impact.auto_rejected / total) * 100),
      icon: ShieldX,
      colorClass: "text-red-500",
      bgClass: "bg-red-50",
    },
    {
      label: "Est. time saved",
      value: `${impact.estimated_time_saved_hours.toFixed(1)}h`,
      pct: null,
      icon: Clock,
      colorClass: "text-brand-600",
      bgClass: "bg-brand-50",
    },
  ];

  return (
    <div className={cn("bg-white border border-slate-200 rounded-lg p-4", className)}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Policy impact · last {impact.period_days} days
        </p>
        <span className="text-[10px] text-slate-300">{impact.total_processed} processed</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className={cn("rounded-lg px-3 py-2.5 flex items-start gap-2", stat.bgClass)}
            >
              <Icon className={cn("w-3.5 h-3.5 mt-0.5 flex-shrink-0", stat.colorClass)} />
              <div>
                <p className={cn("text-base font-bold tabular-nums", stat.colorClass)}>
                  {stat.value}
                  {stat.pct !== null && (
                    <span className="text-xs font-normal ml-1">
                      ({stat.pct}%)
                    </span>
                  )}
                </p>
                <p className="text-[10px] text-slate-500">{stat.label}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
