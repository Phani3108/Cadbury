import { create } from "zustand";
import type { ApprovalItem, ApprovalStatus } from "@/lib/types";

interface ApprovalStore {
  approvals: ApprovalItem[];
  selectedId: string | null;
  filterStatus: ApprovalStatus | "all";
  pendingCount: number;
  setApprovals: (approvals: ApprovalItem[]) => void;
  addApproval: (approval: ApprovalItem) => void;
  updateApproval: (id: string, updates: Partial<ApprovalItem>) => void;
  removeApproval: (id: string) => void;
  setSelectedId: (id: string | null) => void;
  setFilterStatus: (status: ApprovalStatus | "all") => void;
}

export const useApprovalStore = create<ApprovalStore>((set, get) => ({
  approvals: [],
  selectedId: null,
  filterStatus: "all",
  pendingCount: 0,

  setApprovals: (approvals) =>
    set({
      approvals,
      pendingCount: approvals.filter((a) => a.status === "pending").length,
    }),

  addApproval: (approval) =>
    set((state) => {
      const next = [approval, ...state.approvals];
      return {
        approvals: next,
        pendingCount: next.filter((a) => a.status === "pending").length,
      };
    }),

  updateApproval: (id, updates) =>
    set((state) => {
      const next = state.approvals.map((a) =>
        a.approval_id === id ? { ...a, ...updates } : a
      );
      return {
        approvals: next,
        pendingCount: next.filter((a) => a.status === "pending").length,
      };
    }),

  removeApproval: (id) =>
    set((state) => {
      const next = state.approvals.filter((a) => a.approval_id !== id);
      const newSelected =
        state.selectedId === id
          ? next.find((a) => a.status === "pending")?.approval_id ?? null
          : state.selectedId;
      return {
        approvals: next,
        selectedId: newSelected,
        pendingCount: next.filter((a) => a.status === "pending").length,
      };
    }),

  setSelectedId: (selectedId) => set({ selectedId }),

  setFilterStatus: (filterStatus) => set({ filterStatus }),
}));
