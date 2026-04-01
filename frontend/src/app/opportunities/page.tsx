"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Briefcase, Building2, MapPin, DollarSign } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { ScoreBadge } from "@/components/scoring/score-badge";
import { StatusPill } from "@/components/shared/status-pill";
import { api } from "@/lib/api";
import type { JobOpportunity } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-100 rounded-md ${className ?? ""}`} />;
}

function formatComp(min: number | null, max: number | null): string {
  if (!min && !max) return "Not disclosed";
  const fmt = (n: number) => (n >= 1_000 ? `$${Math.round(n / 1_000)}K` : `$${n}`);
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `From ${fmt(min)}`;
  return `Up to ${fmt(max!)}`;
}

export default function OpportunitiesPage() {
  const [opps, setOpps] = useState<JobOpportunity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.opportunities.list()
      .then(setOpps)
      .catch(() => setOpps([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="Opportunities"
        subtitle="All job opportunities your delegate has processed"
      />

      {loading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : opps.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg">
          <EmptyState
            icon={Briefcase}
            title="No opportunities yet"
            description="Your delegate will populate this list as it screens incoming recruiter emails"
          />
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-lg divide-y divide-slate-50">
          {opps.map((opp) => (
            <Link
              key={opp.opportunity_id}
              href={`/opportunities/${opp.opportunity_id}`}
              className="flex items-center gap-4 px-4 py-3 hover:bg-slate-50 transition-colors group"
            >
              <ScoreBadge score={opp.match_score} size="sm" />

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-slate-900 truncate group-hover:text-brand-600">
                    {opp.role}
                  </p>
                  <StatusPill variant={opp.status} />
                </div>
                <div className="flex items-center gap-3 mt-0.5 text-[11px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <Building2 className="w-3 h-3" /> {opp.company}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" /> {opp.location || "Unknown"}
                  </span>
                  <span className="flex items-center gap-1">
                    <DollarSign className="w-3 h-3" />
                    {formatComp(opp.comp_range_min, opp.comp_range_max)}
                  </span>
                </div>
              </div>

              <p className="text-[11px] text-slate-300 flex-shrink-0">
                {formatDistanceToNow(new Date(opp.created_at), { addSuffix: true })}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
