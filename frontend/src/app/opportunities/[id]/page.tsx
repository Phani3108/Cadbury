"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ChevronLeft,
  Building2,
  MapPin,
  DollarSign,
  Globe,
  Briefcase,
  ArrowRight,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ScoreBadge } from "@/components/scoring/score-badge";
import { MatchBreakdownCard } from "@/components/scoring/match-breakdown";
import { StatusPill } from "@/components/shared/status-pill";
import { api } from "@/lib/api";
import type { JobOpportunity, ApprovalItem } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-100 rounded-md ${className ?? ""}`} />;
}

function formatComp(min: number | null, max: number | null): string {
  if (!min && !max) return "Not disclosed";
  const fmt = (n: number) => {
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `$${Math.round(n / 1_000)}K`;
    return `$${n}`;
  };
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `From ${fmt(min)}`;
  return `Up to ${fmt(max!)}`;
}

const STATUS_ICONS: Record<string, React.ElementType> = {
  approved: CheckCircle2,
  responded: CheckCircle2,
  rejected: XCircle,
  pending: Clock,
  received: Clock,
  extracted: Clock,
  scored: AlertCircle,
  draft_created: AlertCircle,
  approval_pending: AlertCircle,
  scheduled: CheckCircle2,
};

export default function OpportunityDetailPage({ params }: { params: { id: string } }) {
  const [opp, setOpp] = useState<JobOpportunity | null>(null);
  const [approval, setApproval] = useState<ApprovalItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.opportunities.get(params.id).catch(() => null),
      api.approvals.list().catch(() => [] as ApprovalItem[]),
    ]).then(([o, allApprovals]) => {
      setOpp(o as JobOpportunity | null);
      const linked = (allApprovals as ApprovalItem[]).find(
        (a) => a.opportunity_id === params.id
      );
      setApproval(linked ?? null);
      setLoading(false);
    });
  }, [params.id]);

  if (loading) {
    return (
      <div>
        <PageHeader title="Loading…" subtitle="" />
        <div className="space-y-4 mt-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </div>
    );
  }

  if (!opp) {
    return (
      <div>
        <PageHeader
          title="Opportunity not found"
          subtitle=""
          actions={
            <Link href="/opportunities" className="text-xs text-slate-500 flex items-center gap-1 hover:text-slate-700">
              <ChevronLeft className="w-3 h-3" /> Back
            </Link>
          }
        />
        <div className="mt-8 text-center text-sm text-slate-400 py-16">
          <Briefcase className="w-10 h-10 mx-auto mb-3 text-slate-200" />
          This opportunity doesn&apos;t exist or hasn&apos;t been loaded yet.
        </div>
      </div>
    );
  }

  const StatusIcon = STATUS_ICONS[opp.status] ?? Clock;

  return (
    <div>
      <PageHeader
        title={opp.role}
        subtitle={opp.company}
        actions={
          <Link
            href="/opportunities"
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
          >
            <ChevronLeft className="w-3 h-3" /> All opportunities
          </Link>
        }
      />

      {/* Hero row */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 mb-4 flex items-start gap-5">
        {/* Score ring */}
        <div className="flex-shrink-0">
          <ScoreBadge score={opp.match_score} size="lg" showLabel />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <StatusPill variant={opp.status} />
            <span className="text-[10px] text-slate-400">
              {formatDistanceToNow(new Date(opp.created_at), { addSuffix: true })}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              <span className="truncate">{opp.company}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              <span className="truncate">{opp.location || "Unknown"}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              <span className="truncate">{formatComp(opp.comp_range_min, opp.comp_range_max)}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              <span className="capitalize">{opp.remote_policy}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Three-column body */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Match Breakdown */}
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Match breakdown
          </p>
          <MatchBreakdownCard breakdown={opp.match_breakdown} />
        </div>

        {/* Details */}
        <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Details
          </p>

          {opp.jd_summary && (
            <div>
              <p className="text-[10px] text-slate-400 mb-1">JD Summary</p>
              <p className="text-xs text-slate-600 leading-relaxed">{opp.jd_summary}</p>
            </div>
          )}

          {opp.equity && (
            <div>
              <p className="text-[10px] text-slate-400 mb-1">Equity</p>
              <p className="text-xs text-slate-600">{opp.equity}</p>
            </div>
          )}

          {opp.contact && (
            <div>
              <p className="text-[10px] text-slate-400 mb-1">Recruiter</p>
              <p className="text-xs text-slate-700 font-medium">{opp.contact.name}</p>
              <p className="text-[11px] text-slate-400">{opp.contact.email}</p>
            </div>
          )}

          {opp.email_subject && (
            <div>
              <p className="text-[10px] text-slate-400 mb-1">Email subject</p>
              <p className="text-xs text-slate-600 italic">{opp.email_subject}</p>
            </div>
          )}
        </div>

        {/* Decision / Approval */}
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Decision trail
          </p>

          {approval ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <StatusIcon className={`w-4 h-4 ${approval.status === "approved" ? "text-green-500" : approval.status === "rejected" ? "text-red-500" : "text-amber-500"}`} />
                <span className="text-xs font-medium capitalize text-slate-700">
                  {approval.status}
                </span>
              </div>

              <div>
                <p className="text-[10px] text-slate-400 mb-1">Action</p>
                <p className="text-xs text-slate-600">{approval.action_label || approval.action}</p>
              </div>

              <div>
                <p className="text-[10px] text-slate-400 mb-1">Reasoning</p>
                <p className="text-xs text-slate-600 leading-relaxed">{approval.reasoning}</p>
              </div>

              {approval.draft_content && (
                <div>
                  <p className="text-[10px] text-slate-400 mb-1">Draft response</p>
                  <div className="text-xs text-slate-600 bg-slate-50 rounded p-2 leading-relaxed max-h-32 overflow-y-auto">
                    {approval.draft_content}
                  </div>
                </div>
              )}

              <Link
                href={`/approvals?highlight=${approval.approval_id}`}
                className="inline-flex items-center gap-1 text-[11px] text-brand-600 hover:text-brand-700 font-medium"
              >
                View in inbox <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-24 text-slate-300 gap-1">
              <Clock className="w-5 h-5" />
              <p className="text-xs">No decision yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
