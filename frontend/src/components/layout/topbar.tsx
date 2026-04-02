"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Search, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { useApprovalStore } from "@/stores/approval-store";
import { useEventStore } from "@/stores/event-store";
import { NotificationBell } from "@/components/shared/notification-bell";

const ROUTE_LABELS: Record<string, string> = {
  "/": "Dashboard",
  "/approvals": "Approvals",
  "/goals": "Goals",
  "/opportunities": "Opportunities",
  "/calendar": "Calendar",
  "/digest": "Digest",
  "/settings": "Settings",
};

function getPageLabel(pathname: string): { crumbs: { label: string; href: string }[] } {
  if (pathname.startsWith("/delegates/")) {
    const parts = pathname.split("/").filter(Boolean);
    const delegateId = parts[1];
    const sub = parts[2];
    const crumbs = [
      { label: "Delegates", href: "/delegates" },
      { label: delegateId.charAt(0).toUpperCase() + delegateId.slice(1), href: `/delegates/${delegateId}` },
    ];
    if (sub) {
      crumbs.push({ label: sub.charAt(0).toUpperCase() + sub.slice(1), href: pathname });
    }
    return { crumbs };
  }
  const label = ROUTE_LABELS[pathname] ?? "Page";
  return { crumbs: [{ label, href: pathname }] };
}

export function Topbar() {
  const pathname = usePathname();
  const { sidebarCollapsed, setCommandPaletteOpen } = useUIStore();
  const { pendingCount } = useApprovalStore();
  const { connectionStatus } = useEventStore();
  const { crumbs } = getPageLabel(pathname);

  return (
    <header className={cn(
      "sticky top-0 z-30 h-14 bg-white/80 backdrop-blur-md border-b border-slate-200",
      "flex items-center justify-between px-6 gap-4"
    )}>
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm min-w-0">
        {crumbs.map((crumb, i) => (
          <span key={crumb.href} className="flex items-center gap-1.5 min-w-0">
            {i > 0 && <ChevronRight className="w-3.5 h-3.5 text-slate-300 flex-shrink-0" />}
            {i === crumbs.length - 1 ? (
              <span className="font-medium text-slate-900 truncate">{crumb.label}</span>
            ) : (
              <Link href={crumb.href} className="text-slate-400 hover:text-slate-700 transition-colors truncate">
                {crumb.label}
              </Link>
            )}
          </span>
        ))}
      </nav>

      {/* Right side */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Connection status dot */}
        <span className={cn(
          "w-1.5 h-1.5 rounded-full",
          connectionStatus === "connected" ? "bg-green-500" :
          connectionStatus === "reconnecting" ? "bg-amber-400 animate-pulse" :
          "bg-red-400"
        )} title={`SSE: ${connectionStatus}`} />

        {/* Cmd+K trigger */}
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 text-xs text-slate-400 bg-slate-50 border border-slate-200 rounded-md hover:bg-white hover:text-slate-600 hover:border-slate-300 transition-all"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Search</span>
          <kbd className="ml-1 px-1 py-0.5 text-[10px] bg-slate-100 border border-slate-200 rounded font-mono">⌘K</kbd>
        </button>

        {/* Notifications */}
        <NotificationBell />

        {/* User avatar */}
        <button className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 text-xs font-semibold hover:ring-2 hover:ring-brand-300 transition-all">
          P
        </button>
      </div>
    </header>
  );
}
