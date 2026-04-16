"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { Activity, Loader2, RefreshCw, Zap, DollarSign, Clock } from "lucide-react";
import { observability as obsApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface SystemHealthPayload {
  delegates?: Array<{
    delegate_id: string;
    status: "healthy" | "degraded" | "unhealthy";
    paused?: boolean;
    last_active?: string | null;
    error_rate?: number;
  }>;
  pipeline_durations?: Record<
    string,
    { p50_ms?: number; p95_ms?: number; p99_ms?: number; count?: number }
  >;
  budgets?: Array<{
    delegate_id: string;
    tokens_used_today?: number;
    daily_token_limit?: number;
    cost_used_today_usd?: number;
    daily_cost_limit_usd?: number;
    is_over_budget?: boolean;
  }>;
  usage?: { total_tokens?: number; total_calls?: number };
}

export default function AdminHealthPage() {
  const [data, setData] = useState<SystemHealthPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const raw = (await obsApi.health()) as unknown as SystemHealthPayload;
      setData(raw);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load health");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 15_000);
    return () => window.clearInterval(timer);
  }, [load]);

  const statusColor = (s?: string) =>
    s === "healthy"
      ? "bg-green-500"
      : s === "degraded"
      ? "bg-amber-500"
      : s === "unhealthy"
      ? "bg-red-500"
      : "bg-slate-300";

  return (
    <div>
      <PageHeader
        title="System Health"
        subtitle="Live delegate status, budget utilization, and pipeline latency."
        actions={
          <button
            onClick={load}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
            Refresh
          </button>
        }
      />

      {loading && !data ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-sm text-red-600">{error}</div>
      ) : (
        <div className="space-y-6">
          {/* Delegates */}
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" />
              Delegates
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {(data?.delegates ?? []).map((d) => (
                <div key={d.delegate_id} className="bg-white border border-slate-200 rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={cn("w-2 h-2 rounded-full", statusColor(d.status))} />
                      <span className="text-sm font-semibold text-slate-800 capitalize">
                        {d.delegate_id}
                      </span>
                    </div>
                    <span className="text-[10px] uppercase tracking-wider text-slate-400">
                      {d.paused ? "paused" : d.status ?? "unknown"}
                    </span>
                  </div>
                  <dl className="mt-3 space-y-1 text-xs text-slate-500">
                    <div className="flex justify-between">
                      <dt>Error rate</dt>
                      <dd className="font-mono">
                        {d.error_rate != null ? `${(d.error_rate * 100).toFixed(1)}%` : "—"}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt>Last active</dt>
                      <dd>{d.last_active ? new Date(d.last_active).toLocaleTimeString() : "—"}</dd>
                    </div>
                  </dl>
                </div>
              ))}
              {(!data?.delegates || data.delegates.length === 0) && (
                <div className="col-span-full bg-slate-50 rounded-xl p-8 text-center text-xs text-slate-400">
                  No delegates reporting.
                </div>
              )}
            </div>
          </section>

          {/* Pipeline latency */}
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              Pipeline latency
            </h2>
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium">Stage</th>
                    <th className="text-right px-4 py-2 font-medium">p50</th>
                    <th className="text-right px-4 py-2 font-medium">p95</th>
                    <th className="text-right px-4 py-2 font-medium">p99</th>
                    <th className="text-right px-4 py-2 font-medium">count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data?.pipeline_durations ?? {}).map(([name, stats]) => (
                    <tr key={name} className="border-t border-slate-100">
                      <td className="px-4 py-2 font-mono text-xs">{name}</td>
                      <td className="px-4 py-2 text-right font-mono text-xs">{stats.p50_ms ?? "—"}ms</td>
                      <td className="px-4 py-2 text-right font-mono text-xs">{stats.p95_ms ?? "—"}ms</td>
                      <td className="px-4 py-2 text-right font-mono text-xs">{stats.p99_ms ?? "—"}ms</td>
                      <td className="px-4 py-2 text-right font-mono text-xs text-slate-500">{stats.count ?? 0}</td>
                    </tr>
                  ))}
                  {!data?.pipeline_durations || Object.keys(data.pipeline_durations).length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-xs text-slate-400">
                        No timing samples yet.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </section>

          {/* Budgets */}
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5" />
              Budgets today
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(data?.budgets ?? []).map((b) => {
                const tokPct = b.daily_token_limit
                  ? Math.min(100, ((b.tokens_used_today ?? 0) / b.daily_token_limit) * 100)
                  : 0;
                const costPct = b.daily_cost_limit_usd
                  ? Math.min(100, ((b.cost_used_today_usd ?? 0) / b.daily_cost_limit_usd) * 100)
                  : 0;
                return (
                  <div key={b.delegate_id} className="bg-white border border-slate-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-slate-800 capitalize">{b.delegate_id}</span>
                      {b.is_over_budget && (
                        <span className="text-[10px] uppercase font-semibold bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full">
                          Over budget
                        </span>
                      )}
                    </div>
                    <div className="space-y-2 text-xs">
                      <div>
                        <div className="flex justify-between text-slate-500">
                          <span>Tokens</span>
                          <span className="font-mono">
                            {b.tokens_used_today ?? 0} / {b.daily_token_limit || "∞"}
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-full transition-all",
                              tokPct >= 100 ? "bg-red-500" : tokPct >= 75 ? "bg-amber-500" : "bg-brand-500",
                            )}
                            style={{ width: `${tokPct}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-slate-500">
                          <span>Cost</span>
                          <span className="font-mono">
                            ${(b.cost_used_today_usd ?? 0).toFixed(4)} / ${b.daily_cost_limit_usd || "∞"}
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-full transition-all",
                              costPct >= 100 ? "bg-red-500" : costPct >= 75 ? "bg-amber-500" : "bg-brand-500",
                            )}
                            style={{ width: `${costPct}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Total usage */}
          {data?.usage && (
            <section className="bg-white border border-slate-200 rounded-xl p-4">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5" />
                LLM totals since start
              </h2>
              <div className="flex gap-6 text-sm">
                <div>
                  <div className="text-xs text-slate-400">Calls</div>
                  <div className="font-mono">{data.usage.total_calls ?? 0}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">Tokens</div>
                  <div className="font-mono">{data.usage.total_tokens ?? 0}</div>
                </div>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
