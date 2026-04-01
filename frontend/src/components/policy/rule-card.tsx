import { ShieldCheck, ShieldAlert, ShieldX, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TrustZone, ActionPermission } from "@/lib/types";

const ZONE_CONFIG = {
  auto: {
    title: "Auto-approve",
    description: "Delegate acts without asking you",
    Icon: ShieldCheck,
    headerClass: "bg-green-50 border-green-100",
    titleClass: "text-green-700",
    iconClass: "text-green-500",
    pillClass: "bg-green-100 text-green-700",
  },
  review: {
    title: "Review required",
    description: "Delegate drafts, you approve",
    Icon: ShieldAlert,
    headerClass: "bg-amber-50 border-amber-100",
    titleClass: "text-amber-700",
    iconClass: "text-amber-500",
    pillClass: "bg-amber-100 text-amber-700",
  },
  block: {
    title: "Always blocked",
    description: "Delegate never does this",
    Icon: ShieldX,
    headerClass: "bg-red-50 border-red-100",
    titleClass: "text-red-700",
    iconClass: "text-red-500",
    pillClass: "bg-red-100 text-red-600",
  },
};

interface RuleCardProps {
  zone: TrustZone;
  actions: ActionPermission[];
}

export function RuleCard({ zone, actions }: RuleCardProps) {
  const config = ZONE_CONFIG[zone];
  const Icon = config.Icon;

  if (actions.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className={cn("flex items-center gap-3 px-4 py-3 border-b", config.headerClass)}>
        <Icon className={cn("w-4 h-4", config.iconClass)} />
        <div>
          <p className={cn("text-sm font-semibold", config.titleClass)}>{config.title}</p>
          <p className="text-xs text-slate-500">{config.description}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="divide-y divide-slate-50">
        {actions.map((action) => (
          <div key={action.action} className="flex items-center justify-between px-4 py-2.5">
            <div className="flex items-center gap-2">
              <ChevronRight className="w-3 h-3 text-slate-300" />
              <span className="text-xs text-slate-600">{action.action_label || action.action}</span>
            </div>
            <span className={cn("text-[10px] font-medium rounded-full px-2 py-0.5", config.pillClass)}>
              {zone}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
