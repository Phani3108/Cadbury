"use client";

import { useState } from "react";
import {
  Building2,
  MapPin,
  DollarSign,
  Briefcase,
  Wifi,
  WifiOff,
  Globe,
  Shield,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ScoreBadge } from "@/components/scoring/score-badge";
import { MatchBreakdownCard } from "@/components/scoring/match-breakdown";
import { StatusPill } from "@/components/shared/status-pill";
import { DraftEditor } from "./draft-editor";
import { ApprovalActions } from "./approval-actions";
import type { ApprovalItem } from "@/lib/types";

interface ApprovalDetailProps {
  item: ApprovalItem;
  onApprove: (draft: string) => void;
  onReject: () => void;
  onSkip: () => void;
  loading?: boolean;
}

function formatComp(min: number | null, max: number | null): string {
  if (!min && !max) return "Not disclosed";
  const fmt = (n: number) =>
    n >= 100_000
      ? `₹${(n / 100_000).toFixed(1)}L`
      : `₹${n.toLocaleString("en-IN")}`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (max) return `Up to ${fmt(max)}`;
  return `${fmt(min!)}+`;
}

const REMOTE_ICONS = {
  remote: Wifi,
  hybrid: Globe,
  onsite: WifiOff,
  unknown: Globe,
};

export function ApprovalDetail({
  item,
  onApprove,
  onReject,
  onSkip,
  loading = false,
}: ApprovalDetailProps) {
  const opp = item.opportunity;
  const [draft, setDraft] = useState(item.draft_content ?? "");
  const [isEditing, setIsEditing] = useState(false);

  // Keep draft in sync when item changes (navigating between items)
  // Reset to item's draft when selected item changes
  const [lastItemId, setLastItemId] = useState(item.approval_id);
  if (item.approval_id !== lastItemId) {
    setLastItemId(item.approval_id);
    setDraft(item.draft_content ?? "");
    setIsEditing(false);
  }

  const [policyExpanded, setPolicyExpanded] = useState(false);

  const RemoteIcon = opp
    ? REMOTE_ICONS[opp.remote_policy] ?? Globe
    : Globe;

  return (
    <div className="flex flex-col h-full">
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Header: company + role + status */}
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-8 h-8 rounded-md bg-slate-100 flex items-center justify-center flex-shrink-0">
                <Building2 className="w-4 h-4 text-slate-500" />
              </div>
              <h2 className="text-lg font-bold text-slate-900 truncate">
                {opp?.company ?? "Unknown company"}
              </h2>
            </div>
            <p className="text-sm text-slate-600 font-medium pl-10">
              {opp?.role ?? item.action_label}
            </p>
          </div>
          <StatusPill variant={item.status} />
        </div>

        {/* Meta strip */}
        {opp && (
          <div className="flex items-center gap-4 flex-wrap text-xs text-slate-500 bg-slate-50 rounded-lg px-4 py-3">
            {opp.location && (
              <span className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5" />
                {opp.location}
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <RemoteIcon className="w-3.5 h-3.5" />
              <span className="capitalize">{opp.remote_policy}</span>
            </span>
            <span className="flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5" />
              {formatComp(opp.comp_range_min, opp.comp_range_max)}
            </span>
            {opp.equity && (
              <span className="flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5" />
                {opp.equity}
              </span>
            )}
          </div>
        )}

        {/* Score + breakdown */}
        {opp && (
          <div className="flex items-start gap-6 bg-white border border-slate-100 rounded-lg p-4">
            <div className="flex flex-col items-center gap-1">
              <ScoreBadge score={opp.match_score} size="lg" showLabel />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Match breakdown
              </p>
              <MatchBreakdownCard breakdown={opp.match_breakdown} />
            </div>
          </div>
        )}

        {/* JD summary */}
        {opp?.jd_summary && (
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Summary
            </p>
            <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 rounded-lg p-3">
              {opp.jd_summary}
            </p>
          </div>
        )}

        {/* Draft editor */}
        <DraftEditor
          draft={draft}
          onChange={setDraft}
          focused={isEditing}
          readOnly={!isEditing}
          originalDraft={item.draft_content ?? ""}
        />

        {/* Policy check (collapsible) */}
        {item.reasoning && (
          <div className="border border-slate-100 rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={() => setPolicyExpanded((v) => !v)}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Shield className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-xs font-medium text-slate-500">
                  Policy check
                </span>
              </div>
              {policyExpanded ? (
                <ChevronUp className="w-3.5 h-3.5 text-slate-300" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-slate-300" />
              )}
            </button>
            {policyExpanded && (
              <div className="px-4 pb-3 space-y-2 border-t border-slate-100">
                <p className="text-xs text-slate-500 pt-2 leading-relaxed">
                  {item.reasoning}
                </p>
                {Array.isArray(item.policy_check?.rules_checked) && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {(item.policy_check.rules_checked as string[]).map((rule) => (
                      <span
                        key={rule}
                        className="text-[10px] font-mono bg-slate-100 text-slate-500 rounded px-1.5 py-0.5"
                      >
                        {rule}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sticky action bar */}
      <div className="flex-shrink-0 border-t border-slate-100 px-6 py-4 bg-white">
        <ApprovalActions
          status={item.status}
          isEditing={isEditing}
          onApprove={() => onApprove(draft)}
          onReject={onReject}
          onEdit={() => setIsEditing((v) => !v)}
          onSkip={onSkip}
          loading={loading}
        />
      </div>
    </div>
  );
}
