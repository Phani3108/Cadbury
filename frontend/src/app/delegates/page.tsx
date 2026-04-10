"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Bot,
  Pause,
  Play,
  DollarSign,
  Zap,
  Clock,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  WalletIcon,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { delegates as delegatesApi, budgets as budgetsApi } from "@/lib/api";
import type { BudgetResponse } from "@/lib/api";
import type { Delegate } from "@/lib/types";
import { useEventStore } from "@/stores/event-store";

interface DelegateWithBudget extends Delegate {
  budget?: BudgetResponse;
}

export default function DelegatesPage() {
  const [items, setItems] = useState<DelegateWithBudget[]>([]);
  const [loading, setLoading] = useState(true);
  const events = useEventStore((s) => s.events);

  const fetchAll = useCallback(async () => {
    try {
      const ds = await delegatesApi.list();
      const withBudgets = await Promise.all(
        ds.map(async (d) => {
          try {
            const budget = await budgetsApi.get(d.id);
            return { ...d, budget } as DelegateWithBudget;
          } catch {
            return { ...d } as DelegateWithBudget;
          }
        })
      );
      setItems(withBudgets);
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  // Refresh on new events
  useEffect(() => {
    if (events.length > 0) fetchAll();
  }, [events.length, fetchAll]);

  const togglePause = async (d: DelegateWithBudget) => {
    if (d.status === "active") {
      await delegatesApi.pause(d.id);
    } else {
      await delegatesApi.resume(d.id);
    }
    fetchAll();
  };

  if (loading) {
    return (
      <div className="p-8 space-y-4">
        <h1 className="text-xl font-semibold text-slate-900">Delegate Command Center</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-xl p-6 animate-pulse">
              <div className="h-6 bg-slate-100 rounded w-2/3 mb-4" />
              <div className="h-4 bg-slate-100 rounded w-1/2 mb-2" />
              <div className="h-4 bg-slate-100 rounded w-3/4" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">
            Delegate Command Center
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Monitor, control, and manage all active delegates
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {items.map((d) => (
          <DelegateCard key={d.id} delegate={d} onToggle={() => togglePause(d)} />
        ))}
      </div>
    </div>
  );
}

function DelegateCard({
  delegate,
  onToggle,
}: {
  delegate: DelegateWithBudget;
  onToggle: () => void;
}) {
  const d = delegate;
  const budget = d.budget;
  const isActive = d.status === "active";
  const isOverBudget = budget?.is_over_budget ?? false;

  const statusColor = isOverBudget
    ? "text-amber-600 bg-amber-50 border-amber-200"
    : isActive
    ? "text-emerald-600 bg-emerald-50 border-emerald-200"
    : "text-slate-500 bg-slate-50 border-slate-200";

  const statusLabel = isOverBudget
    ? "Over Budget"
    : isActive
    ? "Active"
    : "Paused";

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 hover:shadow-sm transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-lg", isActive ? "bg-indigo-50" : "bg-slate-100")}>
            <Bot className={cn("h-5 w-5", isActive ? "text-indigo-600" : "text-slate-400")} />
          </div>
          <div>
            <Link
              href={`/delegates/${d.id}`}
              className="text-sm font-semibold text-slate-900 hover:text-indigo-600 transition-colors"
            >
              {d.name}
            </Link>
            <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
              {d.description}
            </p>
          </div>
        </div>
        <button
          onClick={onToggle}
          className={cn(
            "p-1.5 rounded-md border transition-colors",
            isActive
              ? "border-slate-200 hover:bg-slate-50 text-slate-500"
              : "border-emerald-200 hover:bg-emerald-50 text-emerald-600"
          )}
          title={isActive ? "Pause delegate" : "Resume delegate"}
        >
          {isActive ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
        </button>
      </div>

      {/* Status pill */}
      <div className="mb-4">
        <span
          className={cn(
            "inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border",
            statusColor
          )}
        >
          {isOverBudget ? (
            <AlertTriangle className="h-3 w-3" />
          ) : isActive ? (
            <CheckCircle2 className="h-3 w-3" />
          ) : (
            <Pause className="h-3 w-3" />
          )}
          {statusLabel}
        </span>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <StatCell
          icon={<Zap className="h-3.5 w-3.5 text-amber-500" />}
          label="Processed today"
          value={String(d.stats?.processed_today ?? 0)}
        />
        <StatCell
          icon={<Clock className="h-3.5 w-3.5 text-blue-500" />}
          label="Pending"
          value={String(d.stats?.pending_approvals ?? 0)}
        />
        <StatCell
          icon={<TrendingUp className="h-3.5 w-3.5 text-emerald-500" />}
          label="Auto rate"
          value={`${((d.stats?.auto_rate ?? 0) * 100).toFixed(0)}%`}
        />
        <StatCell
          icon={<DollarSign className="h-3.5 w-3.5 text-violet-500" />}
          label="Avg score"
          value={`${((d.stats?.avg_score ?? 0) * 100).toFixed(0)}%`}
        />
      </div>

      {/* Budget bar */}
      {budget && (
        <div className="border-t border-slate-100 pt-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-slate-500 flex items-center gap-1">
              <WalletIcon className="h-3 w-3" />
              Budget
            </span>
            <span className={cn(
              "font-medium",
              isOverBudget ? "text-red-600" : "text-slate-700"
            )}>
              ${budget.cost_used_today_usd.toFixed(4)} / ${budget.daily_cost_limit_usd.toFixed(2)}
            </span>
          </div>
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                budget.cost_usage_pct >= 100
                  ? "bg-red-500"
                  : budget.cost_usage_pct >= 75
                  ? "bg-amber-500"
                  : "bg-emerald-500"
              )}
              style={{ width: `${Math.min(budget.cost_usage_pct, 100)}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-xs mt-1">
            <span className="text-slate-400">
              {budget.tokens_used_today.toLocaleString()} tokens
            </span>
            <span className="text-slate-400">
              {budget.token_usage_pct.toFixed(0)}% of limit
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCell({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2">
      {icon}
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-sm font-semibold text-slate-900">{value}</p>
      </div>
    </div>
  );
}
