"use client";

import { useCallback, useEffect, useState } from "react";
import { use } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { Loader2, Activity, Layers, BookOpen } from "lucide-react";
import { events as eventsApi, pipelineRuns as runsApi, type PipelineRun } from "@/lib/api";
import type { DelegateEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

type Tab = "events" | "runs" | "decisions";

export default function DelegateHistoryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [tab, setTab] = useState<Tab>("events");
  const [evts, setEvts] = useState<DelegateEvent[]>([]);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [e, r] = await Promise.all([eventsApi.list(id, 100), runsApi.list(id, undefined, 50)]);
      setEvts(e);
      setRuns(r);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const decisionEvents = evts.filter((e) =>
    ["HUMAN_APPROVED", "HUMAN_REJECTED", "HUMAN_EDITED", "AUTO_DECLINED", "POLICY_BLOCKED"].includes(e.event_type),
  );

  return (
    <div>
      <PageHeader
        title={`${id[0]?.toUpperCase()}${id.slice(1)} history`}
        subtitle="Events, pipeline runs, and decisions logged for this delegate."
      />

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200 mb-4">
        {(
          [
            { id: "events", label: "Events", icon: Activity, count: evts.length },
            { id: "runs", label: "Pipeline runs", icon: Layers, count: runs.length },
            { id: "decisions", label: "Decisions", icon: BookOpen, count: decisionEvents.length },
          ] as const
        ).map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "px-3 py-2 text-xs font-medium border-b-2 -mb-px transition-colors inline-flex items-center gap-1.5",
                tab === t.id
                  ? "border-brand-500 text-brand-600"
                  : "border-transparent text-slate-500 hover:text-slate-800",
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {t.label}
              <span className="text-[10px] bg-slate-100 text-slate-500 rounded-full px-1.5">{t.count}</span>
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          {tab === "events" && <EventTable events={evts} />}
          {tab === "runs" && <RunsTable runs={runs} />}
          {tab === "decisions" && <EventTable events={decisionEvents} />}
        </div>
      )}
    </div>
  );
}

function EventTable({ events }: { events: DelegateEvent[] }) {
  if (!events.length) return <EmptyState label="No events yet" />;
  return (
    <table className="w-full text-sm">
      <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-slate-400">
        <tr>
          <th className="text-left px-4 py-2 font-medium">When</th>
          <th className="text-left px-4 py-2 font-medium">Event</th>
          <th className="text-left px-4 py-2 font-medium">Summary</th>
        </tr>
      </thead>
      <tbody>
        {events.map((e) => (
          <tr key={e.event_id} className="border-t border-slate-100 hover:bg-slate-50/60">
            <td className="px-4 py-2 text-[11px] text-slate-500 whitespace-nowrap">
              {new Date(e.timestamp).toLocaleString()}
            </td>
            <td className="px-4 py-2">
              <span className="font-mono text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                {e.event_type}
              </span>
            </td>
            <td className="px-4 py-2 text-xs text-slate-700">{e.summary}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RunsTable({ runs }: { runs: PipelineRun[] }) {
  if (!runs.length) return <EmptyState label="No pipeline runs yet" />;
  return (
    <table className="w-full text-sm">
      <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-slate-400">
        <tr>
          <th className="text-left px-4 py-2 font-medium">Started</th>
          <th className="text-left px-4 py-2 font-medium">Status</th>
          <th className="text-left px-4 py-2 font-medium">Stage</th>
          <th className="text-left px-4 py-2 font-medium">Duration</th>
          <th className="text-left px-4 py-2 font-medium">Summary</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((r) => {
          const duration =
            r.completed_at && r.started_at
              ? `${((new Date(r.completed_at).getTime() - new Date(r.started_at).getTime()) / 1000).toFixed(1)}s`
              : "—";
          return (
            <tr key={r.id} className="border-t border-slate-100">
              <td className="px-4 py-2 text-[11px] text-slate-500 whitespace-nowrap">
                {new Date(r.started_at).toLocaleString()}
              </td>
              <td className="px-4 py-2">
                <span
                  className={cn(
                    "font-mono text-[10px] px-1.5 py-0.5 rounded",
                    r.status === "completed"
                      ? "bg-green-50 text-green-700"
                      : r.status === "failed"
                      ? "bg-red-50 text-red-700"
                      : "bg-amber-50 text-amber-700",
                  )}
                >
                  {r.status}
                </span>
              </td>
              <td className="px-4 py-2 text-xs text-slate-600">{r.stage ?? "—"}</td>
              <td className="px-4 py-2 text-xs text-slate-500 font-mono">{duration}</td>
              <td className="px-4 py-2 text-xs text-slate-700 truncate">{r.summary ?? r.error ?? "—"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function EmptyState({ label }: { label: string }) {
  return <div className="p-10 text-center text-xs text-slate-400">{label}</div>;
}
