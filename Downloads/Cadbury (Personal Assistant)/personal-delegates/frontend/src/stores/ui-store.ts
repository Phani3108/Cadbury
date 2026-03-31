import { create } from "zustand";

interface UIStore {
  sidebarCollapsed: boolean;
  commandPaletteOpen: boolean;
  activePage: string;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setActivePage: (page: string) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarCollapsed: false,
  commandPaletteOpen: false,
  activePage: "/",

  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),

  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),

  setActivePage: (activePage) => set({ activePage }),
}));
