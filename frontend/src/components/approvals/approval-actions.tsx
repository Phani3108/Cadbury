"use client";

import { Check, X, PenLine, SkipForward } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ApprovalStatus } from "@/lib/types";

interface ApprovalActionsProps {
  status: ApprovalStatus;
  isEditing: boolean;
  onApprove: () => void;
  onReject: () => void;
  onEdit: () => void;
  onSkip: () => void;
  loading?: boolean;
  className?: string;
}

interface ActionBtn {
  label: string;
  shortcut: string;
  icon: React.ComponentType<{ className?: string }>;
  onClick: () => void;
  variant: "approve" | "reject" | "edit" | "skip";
  disabled?: boolean;
}

export function ApprovalActions({
  status,
  isEditing,
  onApprove,
  onReject,
  onEdit,
  onSkip,
  loading = false,
  className,
}: ApprovalActionsProps) {
  const isPending = status === "pending";

  const buttons: ActionBtn[] = [
    {
      label: isEditing ? "Approve & send" : "Approve",
      shortcut: isEditing ? "⌘↵" : "A",
      icon: Check,
      onClick: onApprove,
      variant: "approve",
      disabled: !isPending || loading,
    },
    {
      label: isEditing ? "Done editing" : "Edit draft",
      shortcut: "E",
      icon: PenLine,
      onClick: onEdit,
      variant: "edit",
      disabled: !isPending || loading,
    },
    {
      label: "Reject",
      shortcut: "R",
      icon: X,
      onClick: onReject,
      variant: "reject",
      disabled: !isPending || loading,
    },
    {
      label: "Skip",
      shortcut: "S",
      icon: SkipForward,
      onClick: onSkip,
      variant: "skip",
      disabled: loading,
    },
  ];

  const variantClasses: Record<ActionBtn["variant"], string> = {
    approve:
      "bg-green-500 text-white hover:bg-green-600 border-transparent disabled:opacity-40",
    reject:
      "bg-red-50 text-red-600 hover:bg-red-100 border-red-200 disabled:opacity-40",
    edit: "bg-brand-50 text-brand-600 hover:bg-brand-100 border-brand-200 disabled:opacity-40",
    skip: "bg-slate-50 text-slate-500 hover:bg-slate-100 border-slate-200 disabled:opacity-40",
  };

  if (!isPending && status !== "skipped") {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <div
          className={cn(
            "px-3 py-1.5 rounded-md text-xs font-medium border",
            status === "approved"
              ? "bg-green-50 text-green-700 border-green-200"
              : "bg-red-50 text-red-600 border-red-200"
          )}
        >
          {status === "approved" ? "Approved" : "Rejected"}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-2 flex-wrap", className)}>
      {buttons.map((btn) => {
        const Icon = btn.icon;
        return (
          <button
            key={btn.variant}
            type="button"
            onClick={btn.onClick}
            disabled={btn.disabled}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border transition-colors",
              variantClasses[btn.variant]
            )}
          >
            <Icon className="w-3.5 h-3.5" />
            {btn.label}
            <kbd className="ml-1 font-mono text-[10px] opacity-60 bg-white/20 rounded px-1 leading-none">
              {btn.shortcut}
            </kbd>
          </button>
        );
      })}
    </div>
  );
}
