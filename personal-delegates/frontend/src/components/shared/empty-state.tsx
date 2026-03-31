import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
  size = "md",
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center text-center py-12 px-6", className)}>
      <div className={cn(
        "rounded-full bg-slate-100 flex items-center justify-center mb-4",
        size === "sm" ? "w-10 h-10" : size === "md" ? "w-14 h-14" : "w-20 h-20"
      )}>
        <Icon className={cn(
          "text-slate-300",
          size === "sm" ? "w-5 h-5" : size === "md" ? "w-7 h-7" : "w-10 h-10"
        )} />
      </div>
      <h3 className={cn(
        "font-semibold text-slate-700",
        size === "sm" ? "text-sm" : "text-base"
      )}>{title}</h3>
      <p className={cn(
        "mt-1 text-slate-400 max-w-xs",
        size === "sm" ? "text-xs" : "text-sm"
      )}>{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
