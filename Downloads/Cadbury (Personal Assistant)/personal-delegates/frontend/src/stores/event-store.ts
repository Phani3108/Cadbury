import { create } from "zustand";
import type { DelegateEvent, ConnectionStatus } from "@/lib/types";

const MAX_EVENTS = 200;

interface EventStore {
  events: DelegateEvent[];
  connectionStatus: ConnectionStatus;
  addEvent: (event: DelegateEvent) => void;
  setEvents: (events: DelegateEvent[]) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  clearEvents: () => void;
}

export const useEventStore = create<EventStore>((set) => ({
  events: [],
  connectionStatus: "disconnected",

  addEvent: (event) =>
    set((state) => ({
      events: [event, ...state.events].slice(0, MAX_EVENTS),
    })),

  setEvents: (events) => set({ events }),

  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),

  clearEvents: () => set({ events: [] }),
}));
