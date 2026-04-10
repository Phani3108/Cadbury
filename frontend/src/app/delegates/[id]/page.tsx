"use client";

import { useEffect, useState, useCallback } from "react";
import { History, ExternalLink } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { StatusPill } from "@/components/shared/status-pill";
import { EmptyState } from "@/components/shared/empty-state";
import { PipelineVisualizer } from "@/components/delegates/pipeline-visualizer";
import { LearningPanel } from "@/components/delegates/learning-panel";
import { DelegateChat } from "@/components/delegates/delegate-chat";
import { Timeline } from "@/components/timeline/timeline";
import { delegates as delegatesApi, events as eventsApi } from "@/lib/api";
import type { Delegate, DelegateEvent, EventType } from "@/lib/types";
import { useEventStore } from "@/stores/event-store";

const EMPTY_STATS = {
  processed_today: 0,
  pending_approvals: 0,
  auto_rate: 0,
  avg_score: 0,
};

export default function DelegateDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const delegateId = params.id;
  const delegateName = delegateId.charAt(0).toUpperCase() + delegateId.slice(1);

  const [delegate, setDelegate] = useState<Delegate | undefined>(undefined);
  const [events, setEvents] = useState<DelegateEvent[]>([]);
  const [patterns, setPatterns] = useState<import("@/lib/types").PatternInsight[]>([]);
  const [displayLimit, setDisplayLimit] = useState(20);
  const [loading, setLoading] = useState(true);
  const [activeStage, setActiveStage] = useState<string | undefined>(undefined);

  const { events: liveEvents } = useEventStore();

  const fetchData = useCallback(async () => {
    const [del, evts, pats] = await Promise.all([
      delegatesApi.get(delegateId).catch(() => undefined),
      eventsApi.list(delegateId, 100).catch(() => []),
      import("@/lib/api").then(({ learning }) => learning.patterns(delegateId)).catch(() => []),
    ]);
    setDelegate(del);
    setEvents(evts as DelegateEvent[]);
    setPatterns(pats as import("@/lib/types").PatternInsight[]);
    setLoading(false);
  }, [delegateId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Merge live SSE events for this delegate
  const allEvents = [
    ...liveEvents.filter((e) => e.delegate_id === delegateId),
    ...events,
  ].filter((e, i, arr) => arr.findIndex((x) => x.event_id === e.event_id) === i);

  const recentEventTypes = allEvents.slice(0, 30).map((e) => e.event_type) as EventType[];

  // Filter events when a pipeline stage is clicked
  const stageEventMap: Record<string, EventType[]> = {
    ingest:  ["email_received"],
    extract: ["opportunity_extracted"],
    score:   ["opportunity_scored"],
    policy:  ["policy_blocked"],
    draft:   ["draft_created"],
    act:     ["approval_requested", "human_approved", "human_rejected", "response_sent"],
  };

  const filteredEvents = activeStage
    ? allEvents.filter((e) => (stageEventMap[activeStage] ?? []).includes(e.event_type as EventType))
    : allEvents;

  const stats = delegate?.stats ?? EMPTY_STATS;

  return (
    <div>
      <PageHeader
        title={`${delegateName} Delegate`}
        subtitle={
          loading
            ? "Loading…"
            : `${stats.processed_today} processed today · ${stats.pending_approvals} pending`
        }
        actions={
          <div className="flex items-center gap-2">
            <StatusPill variant={delegate?.status ?? "active"} />
            <button
              onClick={async () => {
                if (delegate?.status === "active") await delegatesApi.pause(delegateId);
                else await delegatesApi.resume(delegateId);
                fetchData();
              }}
              className="px-3 py-1.5 text-xs font-medium text-slate-600 border border-slate-200 rounded-md hover:bg-slate-50 transition-colors"
            >
              {delegate?.status === "active" ? "Pause" : "Resume"}
            </button>
            <a
              href={`/delegates/${delegateId}/policy`}
              className="px-3 py-1.5 text-xs font-medium text-brand-600 border border-brand-200 rounded-md hover:bg-brand-50 transition-colors flex items-center gap-1"
            >
              View Policy
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        }
      />

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: "Processed today", value: loading ? "—" : String(stats.processed_today) },
          { label: "Pending approvals", value: loading ? "—" : String(stats.pending_approvals) },
          { label: "Auto-approve rate", value: loading ? "—" : `${Math.round(stats.auto_rate * 100)}%` },
          { label: "Avg match score", value: loading ? "—" : stats.avg_score > 0 ? `${Math.round(stats.avg_score * 100)}%` : "—" },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white border border-slate-200 rounded-lg p-4">
            <p className="text-xl font-bold text-slate-900 tabular-nums">{value}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Pipeline visualizer */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pipeline</p>
          {activeStage && (
            <button
              onClick={() => setActiveStage(undefined)}
              className="text-xs text-slate-400 hover:text-slate-600"
            >
              Clear filter ×
            </button>
          )}
        </div>
        <PipelineVisualizer
          recentEventTypes={recentEventTypes}
          activeStageId={activeStage}
          onStageClick={(id) => setActiveStage((prev) => (prev === id ? undefined : id))}
        />
      </div>

      {/* Two column: timeline + learning */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900">
              Event Timeline
              {activeStage && (
                <span className="ml-2 text-[11px] text-brand-500 font-normal">
                  filtered to {activeStage}
                </span>
              )}
            </h2>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            {loading ? (
              <div className="p-6 space-y-4">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-10 bg-slate-50 animate-pulse rounded" />
                ))}
              </div>
            ) : filteredEvents.length === 0 ? (
              <EmptyState
                icon={History}
                title="No events"
                description={
                  activeStage
                    ? `No ${activeStage} events yet`
                    : "Events appear here as your delegate processes emails"
                }
                size="sm"
              />
            ) : (
              <Timeline
                events={filteredEvents}
                maxItems={displayLimit}
                hasMore={filteredEvents.length > displayLimit}
                onLoadMore={() => setDisplayLimit((n) => n + 20)}
              />
            )}
          </div>
        </div>

        {/* Learning panel */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900">Learning & Patterns</h2>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <LearningPanel events={allEvents} stats={stats} patterns={patterns} />
          </div>
        </div>
      </div>

      {/* Embedded chat per delegate (B5) */}
      <DelegateChat delegateId={delegateId} delegateLabel={delegateName} />
    </div>
  );
}

