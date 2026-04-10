"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Briefcase,
  Clock,
  XCircle,
  TrendingUp,
  Timer,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import type { DigestReport } from "@/lib/types";

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-100 rounded-md ${className ?? ""}`} />;
}

type Period = "daily" | "weekly";

export default function DigestPage() {
  const [period, setPeriod] = useState<Period>("daily");
  const [digest, setDigest] = useState<DigestReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.digest
      .get(period)
      .then(setDigest)
      .catch(() => setDigest(null))
      .finally(() => setLoading(false));
  }, [period]);

  const stats = digest?.stats ?? {};

  const statCards = [
    {
      label: "Events (24h)",
      value: stats.total_events ?? stats.new_opportunities ?? 0,
      icon: Briefcase,
      color: "text-brand-500",
      bg: "bg-brand-50",
    },
    {
      label: "Pending Approvals",
      value: stats.pending_approvals ?? 0,
      icon: Clock,
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
    {
      label: "Messages Triaged",
      value: stats.messages_triaged ?? stats.auto_declined ?? 0,
      icon: CheckCircle2,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      label: "Amount Spent",
      value:
        stats.amount_spent != null
          ? `$${(stats.amount_spent as number).toFixed(0)}`
          : "--",
      icon: TrendingUp,
      color: "text-violet-600",
      bg: "bg-violet-50",
    },
    {
      label: "Time Saved",
      value:
        stats.time_saved_minutes != null
          ? `${Math.round(stats.time_saved_minutes as number)}m`
          : "--",
      icon: Timer,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
  ];

  return (
    <div>
      <PageHeader
        title="Digest"
        subtitle="Summary of your delegate activity"
        actions={
          <div className="flex items-center bg-slate-100 rounded-lg p-0.5">
            {(["daily", "weekly"] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded-md transition-all",
                  period === p
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                {p === "daily" ? "Daily" : "Weekly"}
              </button>
            ))}
          </div>
        }
      />

      {/* Loading */}
      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
          <Skeleton className="h-40 w-full" />
        </div>
      )}

      {/* Empty */}
      {!loading && !digest && (
        <div className="bg-white border border-slate-200 rounded-lg">
          <EmptyState
            icon={FileText}
            title="No digest available"
            description={`No ${period} digest has been generated yet. Check back later.`}
          />
        </div>
      )}

      {/* Content */}
      {!loading && digest && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <p className="text-lg text-slate-700 leading-relaxed">
              {digest.summary}
            </p>
            <p className="text-[11px] text-slate-300 mt-3">
              Generated{" "}
              {new Date(digest.generated_at).toLocaleDateString("en-US", {
                weekday: "long",
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
              })}
            </p>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {statCards.map((card) => {
              const Icon = card.icon;
              return (
                <div
                  key={card.label}
                  className="bg-white border border-slate-200 rounded-lg p-4"
                >
                  <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center mb-2", card.bg)}>
                    <Icon className={cn("w-4 h-4", card.color)} />
                  </div>
                  <p className="text-xl font-bold text-slate-900">{card.value}</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">{card.label}</p>
                </div>
              );
            })}
          </div>

          {/* Highlights */}
          {digest.highlights.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-slate-900 mb-3">Highlights</h2>
              <ul className="space-y-2">
                {digest.highlights.map((h, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                    <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Items */}
          {digest.action_items.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-slate-900 mb-3">Action Items</h2>
              <ul className="divide-y divide-slate-50">
                {digest.action_items.map((item, i) => {
                  // Action items may contain markdown-style links: [text](url)
                  const linkMatch = item.match(/\[(.+?)\]\((.+?)\)/);
                  if (linkMatch) {
                    const [, text, url] = linkMatch;
                    const before = item.slice(0, linkMatch.index);
                    const after = item.slice(
                      (linkMatch.index ?? 0) + linkMatch[0].length
                    );
                    return (
                      <li key={i} className="flex items-center gap-2 py-2 text-sm text-slate-600">
                        <ArrowRight className="w-3.5 h-3.5 text-brand-500 flex-shrink-0" />
                        <span>
                          {before}
                          <Link
                            href={url}
                            className="text-brand-500 hover:text-brand-600 underline underline-offset-2"
                          >
                            {text}
                          </Link>
                          {after}
                        </span>
                      </li>
                    );
                  }
                  return (
                    <li key={i} className="flex items-center gap-2 py-2 text-sm text-slate-600">
                      <ArrowRight className="w-3.5 h-3.5 text-brand-500 flex-shrink-0" />
                      <span>{item}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
