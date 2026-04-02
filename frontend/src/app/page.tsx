"use client";

import { useEffect, useState } from "react";
import {
  Inbox,
  TrendingUp,
  CheckCheck,
  Bot,
  Calendar,
  DollarSign,
  MessageSquare,
  Target,
  Settings,
  Shield,
  Brain,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusPill } from "@/components/shared/status-pill";
import { ScoreBadge } from "@/components/scoring/score-badge";
import { cn } from "@/lib/utils";
import {
  delegates as delegatesApi,
  approvals as approvalsApi,
  events as eventsApi,
} from "@/lib/api";
import type { Delegate, ApprovalItem, DelegateEvent } from "@/lib/types";
import { useEventStore } from "@/stores/event-store";
import { useApprovalStore } from "@/stores/approval-store";
import { formatDistanceToNow } from "date-fns";

// ─── Feature card ────────────────────────────────────────────────────────────
function FeatureCard({
  emoji,
  title,
  description,
}: {
  emoji: string;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5">
      <span className="text-2xl">{emoji}</span>
      <h3 className="text-sm font-semibold text-slate-900 mt-3">{title}</h3>
      <p className="text-xs text-slate-500 mt-1 leading-relaxed">
        {description}
      </p>
    </div>
  );
}

// ─── Getting started step ────────────────────────────────────────────────────
function GettingStartedStep({
  number,
  icon: Icon,
  title,
  description,
  href,
}: {
  number: number;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  href: string;
}) {
  return (
    <div className="flex items-start gap-4 py-4 border-b border-slate-100 last:border-0">
      <div className="w-7 h-7 rounded-full bg-brand-500 text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
        {number}
      </div>
      <div className="w-8 h-8 rounded-md bg-slate-100 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Icon className="w-4 h-4 text-slate-500" />
      </div>
      <div className="min-w-0 flex-1">
        <Link
          href={href}
          className="text-sm font-semibold text-slate-900 hover:text-brand-600 transition-colors inline-flex items-center gap-1 group"
        >
          {title}
          <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-brand-500 transition-colors" />
        </Link>
        <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
          {description}
        </p>
      </div>
    </div>
  );
}

// ─── Stat card ───────────────────────────────────────────────────────────────
function StatCard({
  icon: Icon,
  label,
  value,
  href,
  accent,
  loading,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
  href: string;
  accent?: string;
  loading?: boolean;
}) {
  return (
    <Link
      href={href}
      className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-150 group"
    >
      <div className="flex items-center justify-between mb-3">
        <div
          className={cn(
            "w-8 h-8 rounded-md flex items-center justify-center",
            accent ?? "bg-slate-100"
          )}
        >
          <Icon
            className={cn(
              "w-4 h-4",
              accent ? "text-white" : "text-slate-500"
            )}
          />
        </div>
      </div>
      {loading ? (
        <div className="h-8 w-10 bg-slate-100 animate-pulse rounded mb-1" />
      ) : (
        <p className="text-2xl font-bold text-slate-900 tabular-nums">
          {value}
        </p>
      )}
      <p className="text-xs text-slate-400 mt-0.5">{label}</p>
    </Link>
  );
}

// ─── Delegate card (live) ────────────────────────────────────────────────────
function DelegateCard({
  delegate,
  loading,
}: {
  delegate?: Delegate;
  loading?: boolean;
}) {
  return (
    <Link
      href="/delegates/recruiter"
      className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-150"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="w-9 h-9 rounded-lg bg-brand-50 flex items-center justify-center">
          <Bot className="w-5 h-5 text-brand-500" />
        </div>
        <StatusPill variant={delegate?.status ?? "active"} size="sm" />
      </div>
      <p className="text-sm font-semibold text-slate-900">Recruiter Delegate</p>
      <p className="text-xs text-slate-400 mt-0.5 mb-3">
        Screens inbound opportunities
      </p>
      {loading ? (
        <div className="grid grid-cols-3 gap-2 text-center">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-8 bg-slate-50 animate-pulse rounded" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-2 text-center">
          {[
            {
              label: "Today",
              value: String(delegate?.stats.processed_today ?? 0),
            },
            {
              label: "Pending",
              value: String(delegate?.stats.pending_approvals ?? 0),
            },
            {
              label: "Auto",
              value: `${Math.round((delegate?.stats.auto_rate ?? 0) * 100)}%`,
            },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-sm font-semibold text-slate-900 tabular-nums">
                {value}
              </p>
              <p className="text-[10px] text-slate-400">{label}</p>
            </div>
          ))}
        </div>
      )}
    </Link>
  );
}

// ─── Coming soon delegate card ───────────────────────────────────────────────
function EmptyDelegateCard({
  name,
  icon: Icon,
}: {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="bg-white border border-dashed border-slate-200 rounded-lg p-4 cursor-default">
      <div className="flex items-start justify-between mb-3">
        <div className="w-9 h-9 rounded-lg bg-slate-50 flex items-center justify-center">
          <Icon className="w-5 h-5 text-slate-300" />
        </div>
        <span className="text-[10px] font-medium text-slate-300 bg-slate-50 rounded px-1.5 py-0.5">
          Soon
        </span>
      </div>
      <p className="text-sm font-medium text-slate-300">{name} Delegate</p>
      <p className="text-xs text-slate-200 mt-0.5">Coming soon</p>
    </div>
  );
}

// ─── Approval preview card ───────────────────────────────────────────────────
function ApprovalPreviewCard({ item }: { item: ApprovalItem }) {
  const score = item.opportunity?.match_score ?? 0;
  return (
    <Link
      href="/approvals"
      className="flex items-center gap-3 px-4 py-3 border-b border-slate-50 last:border-0 hover:bg-slate-50 transition-colors"
    >
      <ScoreBadge score={score} size="sm" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-slate-900 truncate">
          {item.opportunity?.company ?? item.delegate_id}
        </p>
        <p className="text-xs text-slate-400 truncate">
          {item.opportunity?.role ?? item.action_label}
        </p>
      </div>
      <span className="text-[10px] text-slate-300 flex-shrink-0">
        {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
      </span>
    </Link>
  );
}

// ─── Activity event row ──────────────────────────────────────────────────────
const EVENT_COLORS: Record<string, string> = {
  email_received: "bg-blue-400",
  opportunity_extracted: "bg-purple-400",
  opportunity_scored: "bg-amber-400",
  draft_created: "bg-brand-400",
  approval_requested: "bg-orange-400",
  human_approved: "bg-green-500",
  human_rejected: "bg-red-400",
  response_sent: "bg-green-600",
  policy_blocked: "bg-red-500",
  calendar_booked: "bg-teal-400",
  error: "bg-red-600",
};

function ActivityRow({ event }: { event: DelegateEvent }) {
  const color = EVENT_COLORS[event.event_type] ?? "bg-slate-300";
  return (
    <div className="flex items-start gap-3 px-4 py-2.5 border-b border-slate-50 last:border-0">
      <div
        className={cn("w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0", color)}
      />
      <div className="min-w-0 flex-1">
        <p className="text-xs text-slate-700 leading-relaxed truncate">
          {event.summary}
        </p>
      </div>
      <span className="text-[10px] text-slate-300 flex-shrink-0">
        {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
      </span>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────
export default function HomePage() {
  const [delegate, setDelegate] = useState<Delegate | undefined>(undefined);
  const [pendingApprovals, setPendingApprovals] = useState<ApprovalItem[]>([]);
  const [recentEvents, setRecentEvents] = useState<DelegateEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const { events: liveEvents } = useEventStore();
  const { approvals: storeApprovals } = useApprovalStore();

  useEffect(() => {
    Promise.all([
      delegatesApi.get("recruiter").catch(() => undefined),
      approvalsApi.list("pending").catch(() => []),
      eventsApi.list("recruiter", 20).catch(() => []),
    ]).then(([del, appr, evts]) => {
      setDelegate(del);
      setPendingApprovals((appr as ApprovalItem[]).slice(0, 3));
      setRecentEvents(evts as DelegateEvent[]);
      setLoading(false);
    });
  }, []);

  // Merge live events from SSE store into activity feed
  const allEvents = [...liveEvents.slice(0, 5), ...recentEvents].slice(0, 10);

  // Merge store approvals (may have been updated via SSE)
  const displayApprovals =
    storeApprovals.filter((a) => a.status === "pending").length > 0
      ? storeApprovals.filter((a) => a.status === "pending").slice(0, 3)
      : pendingApprovals;

  const pendingCount = displayApprovals.length;
  const highMatchCount = [...pendingApprovals].filter(
    (a) => (a.opportunity?.match_score ?? 0) >= 0.65
  ).length;

  return (
    <div>
      {/* ── Section 1: Welcome Hero ──────────────────────────────────────── */}
      <div className="mb-10">
        <h1 className="text-2xl font-bold text-slate-900">
          Welcome to Cadbury
        </h1>
        <p className="text-sm text-brand-500 font-medium mt-1">
          Your AI-powered personal delegation network
        </p>
        <p className="text-sm text-slate-500 mt-3 max-w-2xl leading-relaxed">
          Specialized AI delegates handle distinct areas of your life — screening
          recruiters, managing your calendar, and learning your preferences over
          time. You stay in control through clear policies and an approval inbox.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
          <FeatureCard
            emoji="🎯"
            title="Smart Screening"
            description="AI scores every opportunity against your career goals. Low matches are auto-declined."
          />
          <FeatureCard
            emoji="🔒"
            title="You're in Control"
            description="Set delegation policies. Every AI decision needs your approval until you trust it."
          />
          <FeatureCard
            emoji="📈"
            title="Gets Smarter"
            description="Learns from your approve/reject patterns. Surfaces insights and suggestions."
          />
        </div>
      </div>

      {/* ── Section 2: Getting Started ───────────────────────────────────── */}
      <div className="mb-10">
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-1">
            Getting Started
          </h2>
          <p className="text-xs text-slate-400 mb-4">
            Five steps to get your delegation network running.
          </p>

          <div>
            <GettingStartedStep
              number={1}
              icon={Settings}
              title="Configure your integrations"
              description="Add your OpenAI API key and optionally connect Microsoft 365 for live email."
              href="/settings"
            />
            <GettingStartedStep
              number={2}
              icon={Target}
              title="Set your career goals"
              description="Define target roles, minimum compensation, location preferences, and dealbreakers."
              href="/goals"
            />
            <GettingStartedStep
              number={3}
              icon={Shield}
              title="Review your delegation policy"
              description="Control what the AI can do automatically vs. what needs your approval."
              href="/delegates/recruiter/policy"
            />
            <GettingStartedStep
              number={4}
              icon={Inbox}
              title="Check your approval inbox"
              description="Review AI-drafted responses, approve with one click, or edit before sending."
              href="/approvals"
            />
            <GettingStartedStep
              number={5}
              icon={Brain}
              title="Watch it learn"
              description="The delegate detects patterns in your decisions and suggests policy improvements."
              href="/delegates/recruiter"
            />
          </div>
        </div>
      </div>

      {/* ── Section 3: Live Dashboard ────────────────────────────────────── */}
      <div>
        <h2 className="text-base font-semibold text-slate-900 mb-4">
          Dashboard
        </h2>

        {/* Stat cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <StatCard
            icon={Inbox}
            label="Approvals waiting"
            value={pendingCount}
            href="/approvals"
            accent="bg-amber-400"
            loading={loading}
          />
          <StatCard
            icon={TrendingUp}
            label="High-match opportunities"
            value={highMatchCount}
            href="/opportunities"
            accent="bg-brand-500"
            loading={loading}
          />
          <StatCard
            icon={CheckCheck}
            label="Processed today"
            value={delegate?.stats.processed_today ?? 0}
            href="/delegates/recruiter"
            accent="bg-green-500"
            loading={loading}
          />
        </div>

        {/* Main 2-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Pending approvals */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-900">
                Pending Approvals
              </h3>
              <Link
                href="/approvals"
                className="text-xs text-brand-500 hover:text-brand-600 font-medium"
              >
                View all &rarr;
              </Link>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
              {loading ? (
                <div className="p-4 space-y-3">
                  {[0, 1].map((i) => (
                    <div
                      key={i}
                      className="h-12 bg-slate-50 animate-pulse rounded"
                    />
                  ))}
                </div>
              ) : displayApprovals.length === 0 ? (
                <EmptyState
                  icon={Inbox}
                  title="All clear"
                  description="No approvals waiting. Your delegates are caught up."
                  size="sm"
                />
              ) : (
                <>
                  {displayApprovals.map((item) => (
                    <ApprovalPreviewCard
                      key={item.approval_id}
                      item={item}
                    />
                  ))}
                  {pendingCount > 3 && (
                    <Link
                      href="/approvals"
                      className="flex items-center justify-center py-2.5 text-xs text-brand-500 hover:bg-brand-50 transition-colors"
                    >
                      +{pendingCount - 3} more &rarr;
                    </Link>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Right: Activity feed */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-900">Activity</h3>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
              {loading ? (
                <div className="p-4 space-y-2">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="h-8 bg-slate-50 animate-pulse rounded"
                    />
                  ))}
                </div>
              ) : allEvents.length === 0 ? (
                <EmptyState
                  icon={Target}
                  title="No activity yet"
                  description="Trigger the pipeline to see events here."
                  size="sm"
                />
              ) : (
                allEvents.map((evt) => (
                  <ActivityRow key={evt.event_id} event={evt} />
                ))
              )}
            </div>
          </div>
        </div>

        {/* Delegates row */}
        <div className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900">
              Your Delegates
            </h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <DelegateCard delegate={delegate} loading={loading} />
            <EmptyDelegateCard name="Calendar" icon={Calendar} />
            <EmptyDelegateCard name="Finance" icon={DollarSign} />
            <EmptyDelegateCard name="Comms" icon={MessageSquare} />
          </div>
        </div>
      </div>
    </div>
  );
}
