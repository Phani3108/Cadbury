"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { DollarSign, Loader2, Save } from "lucide-react";
import { budgets as budgetsApi, type BudgetResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

const DELEGATES = ["recruiter", "calendar", "comms", "finance", "shopping", "learning", "health"];

interface Draft {
  daily_token_limit: number;
  daily_cost_limit_usd: number;
}

export default function BudgetsPage() {
  const [rows, setRows] = useState<BudgetResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const collected: BudgetResponse[] = [];
      for (const id of DELEGATES) {
        try {
          collected.push(await budgetsApi.get(id));
        } catch {
          /* skip delegate without a budget row yet */
        }
      }
      setRows(collected);
      const draftMap: Record<string, Draft> = {};
      for (const b of collected) {
        draftMap[b.delegate_id] = {
          daily_token_limit: b.daily_token_limit,
          daily_cost_limit_usd: b.daily_cost_limit_usd,
        };
      }
      setDrafts(draftMap);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load budgets");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const save = async (delegateId: string) => {
    const draft = drafts[delegateId];
    if (!draft) return;
    setSaving(delegateId);
    try {
      const updated = await budgetsApi.update(delegateId, draft);
      setRows((prev) => prev.map((r) => (r.delegate_id === delegateId ? updated : r)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(null);
    }
  };

  const isDirty = (b: BudgetResponse) => {
    const d = drafts[b.delegate_id];
    return d && (d.daily_token_limit !== b.daily_token_limit || d.daily_cost_limit_usd !== b.daily_cost_limit_usd);
  };

  return (
    <div>
      <PageHeader
        title="Budgets"
        subtitle="Daily LLM token and cost ceilings per delegate. Zero means unlimited. Breach auto-pauses the delegate."
      />

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-600">{error}</div>
      ) : (
        <div className="max-w-4xl space-y-3">
          {rows.map((b) => {
            const draft = drafts[b.delegate_id];
            if (!draft) return null;
            const dirty = isDirty(b);
            return (
              <div key={b.delegate_id} className="bg-white border border-slate-200 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-brand-500" />
                    <span className="text-sm font-semibold capitalize text-slate-800">
                      {b.delegate_id}
                    </span>
                    {b.is_over_budget && (
                      <span className="text-[10px] uppercase font-semibold bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full">
                        Over budget
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Today: {b.tokens_used_today} tok · ${b.cost_used_today_usd.toFixed(4)}
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <label className="block">
                    <span className="block text-[11px] font-medium text-slate-500 mb-1">
                      Daily token limit (0 = unlimited)
                    </span>
                    <input
                      type="number"
                      min={0}
                      step={1000}
                      value={draft.daily_token_limit}
                      onChange={(e) =>
                        setDrafts((prev) => ({
                          ...prev,
                          [b.delegate_id]: { ...draft, daily_token_limit: Number(e.target.value) },
                        }))
                      }
                      className="w-full text-sm px-3 py-2 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
                    />
                  </label>
                  <label className="block">
                    <span className="block text-[11px] font-medium text-slate-500 mb-1">
                      Daily cost ($USD, 0 = unlimited)
                    </span>
                    <input
                      type="number"
                      min={0}
                      step={0.01}
                      value={draft.daily_cost_limit_usd}
                      onChange={(e) =>
                        setDrafts((prev) => ({
                          ...prev,
                          [b.delegate_id]: {
                            ...draft,
                            daily_cost_limit_usd: Number(e.target.value),
                          },
                        }))
                      }
                      className="w-full text-sm px-3 py-2 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
                    />
                  </label>
                </div>
                <div className="mt-3 flex justify-end">
                  <button
                    onClick={() => save(b.delegate_id)}
                    disabled={!dirty || saving === b.delegate_id}
                    className={cn(
                      "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors",
                      dirty
                        ? "bg-brand-500 text-white hover:bg-brand-600"
                        : "bg-slate-100 text-slate-300 cursor-not-allowed",
                    )}
                  >
                    {saving === b.delegate_id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Save className="w-3.5 h-3.5" />
                    )}
                    Save
                  </button>
                </div>
              </div>
            );
          })}
          {rows.length === 0 && (
            <div className="bg-slate-50 rounded-xl p-10 text-center text-xs text-slate-400">
              No budget rows yet. Trigger a delegate pipeline to create one.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
