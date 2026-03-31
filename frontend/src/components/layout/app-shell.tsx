"use client";

import { useUIStore } from "@/stores/ui-store";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { cn } from "@/lib/utils";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { sidebarCollapsed } = useUIStore();

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <div
        className={cn(
          "transition-all duration-200",
          sidebarCollapsed ? "ml-14" : "ml-56"
        )}
      >
        <Topbar />
        <main className="px-6 py-6 max-w-7xl">
          {children}
        </main>
      </div>
    </div>
  );
}
