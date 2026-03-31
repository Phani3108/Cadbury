"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Inbox,
  Bot,
  Target,
  Briefcase,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import { useApprovalStore } from "@/stores/approval-store";

const DELEGATE_NAV = [
  { id: "recruiter", label: "Recruiter", status: "active" as const },
];

const COMING_SOON = [
  { id: "calendar", label: "Calendar" },
  { id: "finance", label: "Finance" },
  { id: "comms", label: "Comms" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { pendingCount } = useApprovalStore();

  const navItems = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/approvals", label: "Approvals", icon: Inbox, badge: pendingCount },
    { href: "/goals", label: "Goals", icon: Target },
    { href: "/opportunities", label: "Opportunities", icon: Briefcase },
  ];

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen bg-white border-r border-slate-200 flex flex-col z-40 transition-all duration-200",
        sidebarCollapsed ? "w-14" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-14 px-4 border-b border-slate-200 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-brand-500 flex items-center justify-center flex-shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          {!sidebarCollapsed && (
            <span className="text-sm font-semibold text-slate-900 tracking-tight">
              Delegates
            </span>
          )}
        </div>
      </div>

      {/* Main nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-2 py-2 rounded-md text-sm transition-colors relative group",
                active
                  ? "bg-brand-50 text-brand-600 font-medium"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              {active && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-brand-500 rounded-r-full" />
              )}
              <Icon className={cn("w-4 h-4 flex-shrink-0", active ? "text-brand-500" : "text-slate-400 group-hover:text-slate-600")} />
              {!sidebarCollapsed && <span className="truncate">{label}</span>}
              {badge != null && badge > 0 && (
                <span className={cn(
                  "ml-auto flex-shrink-0 min-w-[18px] h-[18px] text-[10px] font-semibold rounded-full flex items-center justify-center",
                  "bg-red-500 text-white px-1"
                )}>
                  {badge > 99 ? "99+" : badge}
                </span>
              )}
            </Link>
          );
        })}

        {/* Delegates section */}
        {!sidebarCollapsed && (
          <div className="pt-4 pb-1">
            <p className="px-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Delegates
            </p>
          </div>
        )}

        {DELEGATE_NAV.map(({ id, label, status }) => {
          const href = `/delegates/${id}`;
          const active = pathname.startsWith(href);
          return (
            <Link
              key={id}
              href={href}
              className={cn(
                "flex items-center gap-3 px-2 py-2 rounded-md text-sm transition-colors relative group",
                active
                  ? "bg-brand-50 text-brand-600 font-medium"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              {active && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-brand-500 rounded-r-full" />
              )}
              <Bot className={cn("w-4 h-4 flex-shrink-0", active ? "text-brand-500" : "text-slate-400 group-hover:text-slate-600")} />
              {!sidebarCollapsed && (
                <>
                  <span className="truncate flex-1">{label}</span>
                  <span className={cn(
                    "w-2 h-2 rounded-full flex-shrink-0",
                    status === "active" ? "bg-green-500" : "bg-amber-500"
                  )} />
                </>
              )}
            </Link>
          );
        })}

        {/* Coming soon placeholders */}
        {!sidebarCollapsed && COMING_SOON.map(({ id, label }) => (
          <div
            key={id}
            className="flex items-center gap-3 px-2 py-2 rounded-md text-sm text-slate-300 cursor-default select-none"
          >
            <Bot className="w-4 h-4 flex-shrink-0 text-slate-200" />
            <span className="truncate flex-1">{label}</span>
            <span className="text-[9px] font-medium text-slate-300 bg-slate-100 rounded px-1">
              Soon
            </span>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-2 py-3 border-t border-slate-200 space-y-0.5">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-2 py-2 rounded-md text-sm text-slate-500 hover:bg-slate-50 hover:text-slate-900 transition-colors"
        >
          <Settings className="w-4 h-4 flex-shrink-0 text-slate-400" />
          {!sidebarCollapsed && <span>Settings</span>}
        </Link>

        {/* Collapse toggle */}
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center gap-3 px-2 py-2 rounded-md text-sm text-slate-400 hover:bg-slate-50 hover:text-slate-600 transition-colors"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
