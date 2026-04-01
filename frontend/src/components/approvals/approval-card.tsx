"use client";

import { MapPin, Building2, DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScoreBadge } from "@/components/scoring/score-badge";
import { StatusPill } from "@/components/shared/status-pill";
import type { ApprovalItem } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";

interface ApprovalCardProps {
  item: ApprovalItem;
  isSelected: boolean;
  onClick: () => void;
}

function formatComp(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) =>
    n >= 100_000
      ? `₹${(n / 100_000).toFixed(1)}L`
      : `₹${n.toLocaleString("en-IN")}`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (max) return `Up to ${fmt(max)}`;
  return `${fmt(min!)}+`;
}

export function ApprovalCard({ item, isSelected, onClick }: ApprovalCardProps) {
  const opp = item.opportunity;
  const score = opp?.match_score ?? 0;
  const comp = opp ? formatComp(opp.comp_range_min, opp.comp_range_max) : null;
  const timeAgo = formatDistanceToNow(new Date(item.created_at), {
    addSuffix: true,
  });

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full text-left px-4 py-3 border-b border-slate-100 transition-colors hover:bg-slate-50 focus:outline-none",
        isSelected && "bg-brand-50 border-l-2 border-l-brand-500 hover:bg-brand-50"
      )}
    >
      {/* Top row: company + score */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-slate-900 truncate">
            {opp?.company ?? item.delegate_id}
          </p>
          <p className="text-xs text-slate-500 truncate mt-0.5">
            {opp?.role ?? item.action_label}
          </p>
        </div>
        {opp && <ScoreBadge score={score} size="sm" />}
      </div>

      {/* Meta row */}
      <div className="flex items-center gap-3 mt-2 flex-wrap">
        {opp?.location && (
          <span className="flex items-center gap-1 text-[11px] text-slate-400">
            <MapPin className="w-3 h-3" />
            {opp.location}
          </span>
        )}
        {comp && (
          <span className="flex items-center gap-1 text-[11px] text-slate-400">
            <DollarSign className="w-3 h-3" />
            {comp}
          </span>
        )}
        {opp?.remote_policy && opp.remote_policy !== "unknown" && (
          <span className="text-[11px] text-slate-400 capitalize">
            {opp.remote_policy}
          </span>
        )}
      </div>

      {/* Bottom row: status + time */}
      <div className="flex items-center justify-between mt-2">
        <StatusPill variant={item.status} size="sm" />
        <span className="text-[10px] text-slate-300">{timeAgo}</span>
      </div>
    </button>
  );
}
