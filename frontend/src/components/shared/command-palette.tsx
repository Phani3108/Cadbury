"use client";

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  LayoutDashboard,
  Inbox,
  Target,
  Briefcase,
  Bot,
  Shield,
  Check,
  Search,
} from "lucide-react";
import { useUIStore } from "@/stores/ui-store";
import { useApprovalStore } from "@/stores/approval-store";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Approval Inbox", href: "/approvals", icon: Inbox },
  { label: "Career Goals", href: "/goals", icon: Target },
  { label: "Opportunities", href: "/opportunities", icon: Briefcase },
  { label: "Recruiter Delegate", href: "/delegates/recruiter", icon: Bot },
  {
    label: "Recruiter Policy",
    href: "/delegates/recruiter/policy",
    icon: Shield,
  },
];

export function CommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const { approvals } = useApprovalStore();

  const pendingApprovals = approvals.filter((a) => a.status === "pending");

  // Open on Cmd+K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [setCommandPaletteOpen]);

  const close = useCallback(() => setCommandPaletteOpen(false), [setCommandPaletteOpen]);

  const navigate = (href: string) => {
    router.push(href);
    close();
  };

  if (!commandPaletteOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
      onClick={close}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-slate-900/30 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className="relative w-full max-w-lg mx-4 bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <Command>
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-100">
            <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <Command.Input
              placeholder="Search pages, approvals…"
              autoFocus
              className="flex-1 bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
            />
            <kbd className="text-[10px] font-mono text-slate-300 bg-slate-50 border border-slate-200 rounded px-1.5 py-0.5">
              Esc
            </kbd>
          </div>

          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="py-8 text-center text-sm text-slate-400">
              No results found
            </Command.Empty>

            {/* Navigation */}
            <Command.Group
              heading={
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 px-2 py-1 block">
                  Pages
                </span>
              }
            >
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                return (
                  <Command.Item
                    key={item.href}
                    value={item.label}
                    onSelect={() => navigate(item.href)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-700 cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                  >
                    <Icon className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    {item.label}
                  </Command.Item>
                );
              })}
            </Command.Group>

            {/* Pending approvals */}
            {pendingApprovals.length > 0 && (
              <Command.Group
                heading={
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 px-2 py-1 mt-2 block">
                    Pending approvals
                  </span>
                }
              >
                {pendingApprovals.slice(0, 5).map((approval) => (
                  <Command.Item
                    key={approval.approval_id}
                    value={`${approval.opportunity?.company ?? ""} ${approval.opportunity?.role ?? ""} ${approval.action_label}`}
                    onSelect={() => {
                      navigate("/approvals");
                      // The store's selectedId will auto-set to first pending,
                      // but we'd ideally select this one — handled via store
                      useApprovalStore.getState().setSelectedId(approval.approval_id);
                    }}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-700 cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                  >
                    <Check className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="font-medium truncate">
                        {approval.opportunity?.company ?? approval.delegate_id}
                      </p>
                      <p className="text-xs text-slate-400 truncate">
                        {approval.opportunity?.role ?? approval.action_label}
                      </p>
                    </div>
                  </Command.Item>
                ))}
              </Command.Group>
            )}
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
