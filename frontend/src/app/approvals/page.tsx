"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Inbox, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { ApprovalCard } from "@/components/approvals/approval-card";
import { ApprovalDetail } from "@/components/approvals/approval-detail";
import { useApprovalStore } from "@/stores/approval-store";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import { approvals as approvalsApi, opportunities as oppsApi } from "@/lib/api";
import type { ApprovalItem, ApprovalStatus, JobOpportunity } from "@/lib/types";
import { cn } from "@/lib/utils";

// ─── Undo toast ───────────────────────────────────────────────────────────────
interface UndoToast {
  id: string;
  message: string;
  undo: () => void;
  timeoutId: ReturnType<typeof setTimeout>;
}

// ─── Filter tabs ──────────────────────────────────────────────────────────────
const TABS: { label: string; value: ApprovalStatus | "all" }[] = [
  { label: "All", value: "all" },
  { label: "Pending", value: "pending" },
  { label: "Approved", value: "approved" },
  { label: "Rejected", value: "rejected" },
];

export default function ApprovalsPage() {
  const {
    approvals,
    selectedId,
    filterStatus,
    setApprovals,
    updateApproval,
    setSelectedId,
    setFilterStatus,
    pendingCount,
  } = useApprovalStore();

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [toasts, setToasts] = useState<UndoToast[]>([]);
  const listRef = useRef<HTMLDivElement>(null);

  // Enrich approvals with opportunity data
  const [oppCache, setOppCache] = useState<Record<string, JobOpportunity>>({});

  const fetchApprovals = useCallback(async () => {
    try {
      const items = await approvalsApi.list();
      // Fetch opp data for each item that has an opportunity_id
      const oppIds = [...new Set(items.flatMap((a) => (a.opportunity_id ? [a.opportunity_id] : [])))];
      const newCache: Record<string, JobOpportunity> = { ...oppCache };
      await Promise.all(
        oppIds
          .filter((id) => !newCache[id])
          .map(async (id) => {
            try {
              newCache[id] = await oppsApi.get(id);
            } catch {
              // ignore — opp just won't be enriched
            }
          })
      );
      setOppCache(newCache);
      const enriched = items.map((a) => ({
        ...a,
        opportunity: a.opportunity_id ? newCache[a.opportunity_id] : undefined,
      }));
      setApprovals(enriched as ApprovalItem[]);
    } finally {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchApprovals();
  }, [fetchApprovals]);

  // Derived: filtered list
  const filtered =
    filterStatus === "all"
      ? approvals
      : approvals.filter((a) => a.status === filterStatus);

  // Auto-select first pending item
  useEffect(() => {
    if (!selectedId && filtered.length > 0) {
      const first = filtered.find((a) => a.status === "pending") ?? filtered[0];
      setSelectedId(first.approval_id);
    }
  }, [filtered, selectedId, setSelectedId]);

  const selectedItem = filtered.find((a) => a.approval_id === selectedId) ?? null;
  const selectedIdx = filtered.findIndex((a) => a.approval_id === selectedId);

  // ─── Navigation helpers ───────────────────────────────────────────────────
  const selectNext = useCallback(() => {
    if (selectedIdx < filtered.length - 1) {
      setSelectedId(filtered[selectedIdx + 1].approval_id);
    }
  }, [selectedIdx, filtered, setSelectedId]);

  const selectPrev = useCallback(() => {
    if (selectedIdx > 0) {
      setSelectedId(filtered[selectedIdx - 1].approval_id);
    }
  }, [selectedIdx, filtered, setSelectedId]);

  // ─── Undo toast helpers ───────────────────────────────────────────────────
  const addToast = useCallback(
    (message: string, undo: () => void) => {
      const id = Math.random().toString(36).slice(2);
      const timeoutId = setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 5000);
      setToasts((prev) => [...prev, { id, message, undo, timeoutId }]);
    },
    []
  );

  const dismissToast = (id: string) => {
    setToasts((prev) => {
      const toast = prev.find((t) => t.id === id);
      if (toast) clearTimeout(toast.timeoutId);
      return prev.filter((t) => t.id !== id);
    });
  };

  // ─── Actions with optimistic updates ──────────────────────────────────────
  const handleApprove = useCallback(
    async (draft: string) => {
      if (!selectedItem || selectedItem.status !== "pending") return;
      const prev = { ...selectedItem };
      // Optimistic update
      updateApproval(selectedItem.approval_id, { status: "approved" });
      selectNext();
      setActionLoading(false);

      try {
        await approvalsApi.approveWithDraft(selectedItem.approval_id, draft);
        addToast("Approved and sent", () => {
          updateApproval(selectedItem.approval_id, { status: "pending" });
        });
      } catch {
        // Revert on error
        updateApproval(selectedItem.approval_id, prev);
        addToast("Failed to approve — reverted", () => {});
      }
    },
    [selectedItem, updateApproval, selectNext, addToast]
  );

  const handleReject = useCallback(async () => {
    if (!selectedItem || selectedItem.status !== "pending") return;
    const prev = { ...selectedItem };
    updateApproval(selectedItem.approval_id, { status: "rejected" });
    selectNext();

    try {
      await approvalsApi.reject(selectedItem.approval_id);
      addToast("Rejected", () => {
        updateApproval(selectedItem.approval_id, { ...prev });
      });
    } catch {
      updateApproval(selectedItem.approval_id, prev);
    }
  }, [selectedItem, updateApproval, selectNext, addToast]);

  const handleSkip = useCallback(() => {
    selectNext();
  }, [selectNext]);

  // ─── Keyboard shortcuts ───────────────────────────────────────────────────
  useKeyboardShortcuts([
    { key: "j", handler: selectNext },
    { key: "k", handler: selectPrev },
    {
      key: "a",
      handler: () => {
        if (selectedItem) handleApprove(selectedItem.draft_content ?? "");
      },
    },
    { key: "r", handler: () => handleReject() },
    { key: "s", handler: () => handleSkip() },
    {
      key: "Enter",
      meta: true,
      handler: () => {
        if (selectedItem) handleApprove(selectedItem.draft_content ?? "");
      },
    },
  ]);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <PageHeader
        title="Approval Inbox"
        subtitle="Review what your delegates want to do on your behalf"
        actions={
          <div className="flex items-center gap-2">
            {/* Filter tabs */}
            <div className="flex text-xs border border-slate-200 rounded-md overflow-hidden">
              {TABS.map((tab) => (
                <button
                  key={tab.value}
                  onClick={() => setFilterStatus(tab.value)}
                  className={cn(
                    "px-3 py-1.5 font-medium transition-colors",
                    filterStatus === tab.value
                      ? "bg-slate-900 text-white"
                      : "text-slate-500 hover:bg-slate-50"
                  )}
                >
                  {tab.label}
                  {tab.value === "pending" && pendingCount > 0 && (
                    <span className="ml-1.5 bg-red-500 text-white rounded-full text-[9px] font-bold px-1.5 py-px">
                      {pendingCount}
                    </span>
                  )}
                </button>
              ))}
            </div>
            <button
              onClick={() => { setLoading(true); fetchApprovals(); }}
              className="p-1.5 rounded-md border border-slate-200 text-slate-400 hover:bg-slate-50 transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        }
      />

      {/* Split view */}
      <div className="flex gap-0 flex-1 overflow-hidden min-h-0">

        {/* List panel */}
        <div
          ref={listRef}
          className="w-80 flex-shrink-0 bg-white border border-slate-200 rounded-lg overflow-hidden flex flex-col mr-4"
        >
          <div className="p-3 border-b border-slate-100 flex-shrink-0">
            <p className="text-xs font-medium text-slate-400">
              {loading ? "Loading…" : `${filtered.length} item${filtered.length !== 1 ? "s" : ""}`}
            </p>
          </div>
          <div className="flex-1 overflow-y-auto">
            {!loading && filtered.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <EmptyState
                  icon={Inbox}
                  title="All clear"
                  description={
                    filterStatus === "pending"
                      ? "No pending approvals right now"
                      : "No approvals match this filter"
                  }
                  size="sm"
                />
              </div>
            ) : (
              filtered.map((item) => (
                <ApprovalCard
                  key={item.approval_id}
                  item={item}
                  isSelected={item.approval_id === selectedId}
                  onClick={() => setSelectedId(item.approval_id)}
                />
              ))
            )}
          </div>
        </div>

        {/* Detail panel */}
        <div className="flex-1 bg-white border border-slate-200 rounded-lg overflow-hidden min-w-0">
          {selectedItem ? (
            <ApprovalDetail
              key={selectedItem.approval_id}
              item={selectedItem}
              onApprove={handleApprove}
              onReject={handleReject}
              onSkip={handleSkip}
              loading={actionLoading}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <EmptyState
                icon={Inbox}
                title="Select an item"
                description="Choose an approval from the list to review it"
                size="sm"
              />
            </div>
          )}
        </div>
      </div>

      {/* Keyboard hint bar */}
      <div className="mt-3 flex items-center gap-4 text-[11px] text-slate-300 flex-shrink-0">
        {[
          ["j/k", "navigate"],
          ["a", "approve"],
          ["r", "reject"],
          ["e", "edit draft"],
          ["s", "skip"],
          ["⌘K", "search"],
        ].map(([key, label]) => (
          <span key={key}>
            <kbd className="font-mono bg-slate-100 border border-slate-200 rounded px-1">
              {key}
            </kbd>{" "}
            {label}
          </span>
        ))}
      </div>

      {/* Undo toasts */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="flex items-center gap-3 bg-slate-900 text-white px-4 py-3 rounded-lg shadow-lg text-sm"
          >
            <span>{toast.message}</span>
            <button
              onClick={() => {
                toast.undo();
                dismissToast(toast.id);
              }}
              className="text-brand-300 hover:text-brand-200 font-medium text-xs underline"
            >
              Undo
            </button>
            <button
              onClick={() => dismissToast(toast.id)}
              className="text-slate-400 hover:text-white ml-1"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
