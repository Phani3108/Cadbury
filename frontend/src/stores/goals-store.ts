"use client";
import { create } from "zustand";
import type { CareerGoals } from "@/lib/types";

interface GoalsState {
  goals: CareerGoals | null;
  dirty: boolean;
  saving: boolean;
  lastSaved: Date | null;

  setGoals: (goals: CareerGoals) => void;
  patchGoals: (patch: Partial<CareerGoals>) => void;
  setSaving: (saving: boolean) => void;
  markSaved: () => void;
}

export const useGoalsStore = create<GoalsState>((set, get) => ({
  goals: null,
  dirty: false,
  saving: false,
  lastSaved: null,

  setGoals: (goals) => set({ goals, dirty: false }),

  patchGoals: (patch) => {
    const current = get().goals;
    if (!current) return;
    set({ goals: { ...current, ...patch }, dirty: true });
  },

  setSaving: (saving) => set({ saving }),

  markSaved: () => set({ dirty: false, saving: false, lastSaved: new Date() }),
}));
