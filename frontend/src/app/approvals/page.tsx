import { Inbox } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";

export default function ApprovalsPage() {
  return (
    <div>
      <PageHeader
        title="Approval Inbox"
        subtitle="Review what your delegates want to do on your behalf"
        actions={
          <div className="flex items-center gap-2">
            <div className="flex text-xs border border-slate-200 rounded-md overflow-hidden">
              {["All", "Pending", "Approved", "Rejected"].map((tab) => (
                <button
                  key={tab}
                  className={`px-3 py-1.5 font-medium transition-colors ${
                    tab === "All"
                      ? "bg-slate-900 text-white"
                      : "text-slate-500 hover:bg-slate-50"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
        }
      />

      {/* Split view placeholder */}
      <div className="flex gap-4 h-[calc(100vh-12rem)]">
        {/* List panel */}
        <div className="w-80 flex-shrink-0 bg-white border border-slate-200 rounded-lg overflow-hidden flex flex-col">
          <div className="p-3 border-b border-slate-100">
            <p className="text-xs font-medium text-slate-400">0 items</p>
          </div>
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              icon={Inbox}
              title="All clear"
              description="No approvals waiting right now"
              size="sm"
            />
          </div>
        </div>

        {/* Detail panel */}
        <div className="flex-1 bg-white border border-slate-200 rounded-lg flex items-center justify-center">
          <EmptyState
            icon={Inbox}
            title="Select an item"
            description="Choose an approval from the list to review it"
            size="sm"
          />
        </div>
      </div>

      {/* Keyboard hint */}
      <div className="mt-3 flex items-center gap-4 text-[11px] text-slate-300">
        <span><kbd className="font-mono bg-slate-100 border border-slate-200 rounded px-1">j</kbd>/<kbd className="font-mono bg-slate-100 border border-slate-200 rounded px-1">k</kbd> navigate</span>
        <span><kbd className="font-mono bg-slate-100 border border-slate-200 rounded px-1">a</kbd> approve</span>
        <span><kbd className="font-mono bg-slate-100 border border-slate-200 rounded px-1">r</kbd> reject</span>
        <span><kbd className="font-mono bg-slate-100 border border-slate-200 rounded px-1">e</kbd> edit draft</span>
        <span><kbd className="font-mono bg-slate-100 border border-slate-200 rounded px-1">s</kbd> skip</span>
      </div>
    </div>
  );
}
