"use client";

import { useEffect, useCallback, useState, useRef } from "react";
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
  History,
  Globe,
  Calendar,
  Bell,
  MessageSquare,
  BookOpen,
  Heart,
  ShoppingCart,
  DollarSign,
  FileText,
  Activity,
} from "lucide-react";
import { useUIStore } from "@/stores/ui-store";
import { useApprovalStore } from "@/stores/approval-store";
import { api, type SearchResult } from "@/lib/api";
import type { JobOpportunity } from "@/lib/types";

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

const ENTITY_ICONS: Record<string, typeof Globe> = {
  opportunity: Briefcase,
  contact: Globe,
  approval: Check,
  event: Activity,
  calendar: Calendar,
  notification: Bell,
  message: MessageSquare,
  memory: FileText,
  scratchpad: FileText,
  learning: BookOpen,
  health_routine: Heart,
  health_appointment: Heart,
  transaction: DollarSign,
  watch_item: ShoppingCart,
};

function getSearchResultLabel(result: SearchResult): string {
  const d = result.data;
  switch (result.type) {
    case "opportunity":
      return `${d.company ?? ""} — ${d.role ?? ""}`;
    case "contact":
      return `${d.email ?? ""}`;
    case "calendar":
      return `${d.title ?? ""}`;
    case "notification":
      return `${d.title ?? ""}`;
    case "memory":
      return `${(d.content as string)?.slice(0, 60) ?? ""}`;
    case "scratchpad":
      return `${d.title ?? ""}`;
    case "transaction":
      return `${d.merchant ?? ""} — $${d.amount ?? ""}`;
    case "watch_item":
      return `${d.name ?? ""}`;
    default:
      return JSON.stringify(d).slice(0, 60);
  }
}

export function CommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const { approvals } = useApprovalStore();
  const [opportunities, setOpportunities] = useState<JobOpportunity[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const pendingApprovals = approvals.filter((a) => a.status === "pending");

  // Load opportunities lazily when palette opens
  useEffect(() => {
    if (commandPaletteOpen && opportunities.length === 0) {
      api.opportunities.list().then(setOpportunities).catch(() => {});
    }
    if (!commandPaletteOpen) {
      setSearchQuery("");
      setSearchResults([]);
    }
  }, [commandPaletteOpen, opportunities.length]);

  // Debounced cross-entity search
  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    debounceRef.current = setTimeout(() => {
      api.search.query(searchQuery, 10).then(setSearchResults).catch(() => {});
    }, 250);
    return () => clearTimeout(debounceRef.current);
  }, [searchQuery]);

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

  const navigateToResult = (result: SearchResult) => {
    const d = result.data;
    switch (result.type) {
      case "opportunity":
        navigate(`/opportunities/${d.opportunity_id ?? ""}`);
        break;
      case "contact":
        navigate("/delegates/recruiter");
        break;
      case "approval":
        navigate("/approvals");
        break;
      case "calendar":
        navigate("/calendar");
        break;
      case "notification":
        navigate("/");
        break;
      case "memory":
      case "scratchpad":
        navigate("/");
        break;
      case "transaction":
        navigate("/");
        break;
      default:
        navigate("/");
    }
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
        <Command
          onValueChange={() => {}}
        >
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-100">
            <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <Command.Input
              placeholder="Search everything… pages, approvals, contacts, memories"
              autoFocus
              value={searchQuery}
              onValueChange={setSearchQuery}
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
            {/* Decision memory */}
            {opportunities.length > 0 && (
              <Command.Group
                heading={
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 px-2 py-1 mt-2 block">
                    Decision memory
                  </span>
                }
              >
                {opportunities.slice(0, 8).map((opp) => (
                  <Command.Item
                    key={opp.opportunity_id}
                    value={`${opp.company} ${opp.role} ${opp.location} ${opp.status}`}
                    onSelect={() => navigate(`/opportunities/${opp.opportunity_id}`)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-700 cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                  >
                    <History className="w-4 h-4 text-slate-300 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="font-medium truncate">{opp.role}</p>
                      <p className="text-xs text-slate-400 truncate">
                        {opp.company} · {Math.round(opp.match_score * 100)}% match · {opp.status}
                      </p>
                    </div>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Cross-entity search results */}
            {searchResults.length > 0 && (
              <Command.Group
                heading={
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 px-2 py-1 mt-2 block">
                    Search results
                  </span>
                }
              >
                {searchResults.map((result, i) => {
                  const Icon = ENTITY_ICONS[result.type] ?? Globe;
                  const label = getSearchResultLabel(result);
                  return (
                    <Command.Item
                      key={`${result.type}-${i}`}
                      value={label}
                      onSelect={() => navigateToResult(result)}
                      className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-700 cursor-pointer data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
                    >
                      <Icon className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="font-medium truncate">{label}</p>
                        <p className="text-xs text-slate-400 truncate capitalize">{result.type}</p>
                      </div>
                    </Command.Item>
                  );
                })}
              </Command.Group>
            )}
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
