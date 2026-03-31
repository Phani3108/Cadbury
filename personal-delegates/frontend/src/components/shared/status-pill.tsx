import { Check, X, Clock, CheckCheck, AlertTriangle, ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ApprovalStatus, TrustZone } from "@/lib/types";

type PillVariant = ApprovalStatus | TrustZone | "active" | "paused" | "error" | "draft";

const VARIANT_CONFIG: Record<PillVariant, {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  className: string;
}> = {
  pending: {
    label: "Pending",
    icon: Clock,
    className: "bg-amber-50 text-amber-700 border-amber-200",
  },
  approved: {
    label: "Approved",
    icon: Check,
    className: "bg-green-50 text-green-700 border-green-200",
  },
  rejected: {
    label: "Rejected",
    icon: X,
    className: "bg-red-50 text-red-600 border-red-200",
  },
  skipped: {
    label: "Skipped",
    icon: Clock,
    className: "bg-slate-50 text-slate-500 border-slate-200",
  },
  expired: {
    label: "Expired",
    icon: Clock,
    className: "bg-slate-50 text-slate-400 border-slate-200",
  },
  auto: {
    label: "Auto",
    icon: ShieldCheck,
    className: "bg-green-50 text-green-700 border-green-200",
  },
  review: {
    label: "Review",
    icon: ShieldAlert,
    className: "bg-amber-50 text-amber-700 border-amber-200",
  },
  block: {
    label: "Block",
    icon: ShieldX,
    className: "bg-red-50 text-red-600 border-red-200",
  },
  active: {
    label: "Active",
    icon: CheckCheck,
    className: "bg-green-50 text-green-700 border-green-200",
  },
  paused: {
    label: "Paused",
    icon: Clock,
    className: "bg-slate-50 text-slate-500 border-slate-200",
  },
  error: {
    label: "Error",
    icon: AlertTriangle,
    className: "bg-red-50 text-red-600 border-red-200",
  },
  draft: {
    label: "Draft",
    icon: Clock,
    className: "bg-slate-50 text-slate-500 border-slate-200",
  },
};

interface StatusPillProps {
  variant: PillVariant;
  label?: string;
  size?: "sm" | "md";
  className?: string;
}

export function StatusPill({ variant, label, size = "md", className }: StatusPillProps) {
  const config = VARIANT_CONFIG[variant] ?? VARIANT_CONFIG.draft;
  const Icon = config.icon;
  const displayLabel = label ?? config.label;

  return (
    <span className={cn(
      "inline-flex items-center gap-1 rounded-full border font-medium",
      size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-xs",
      config.className,
      className
    )}>
      <Icon className={size === "sm" ? "w-2.5 h-2.5" : "w-3 h-3"} />
      {displayLabel}
    </span>
  );
}
