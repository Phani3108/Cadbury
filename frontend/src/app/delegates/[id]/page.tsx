import { Bot, Download, FileSearch, BarChart3, Shield, PenLine, Send, History } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { StatusPill } from "@/components/shared/status-pill";
import { EmptyState } from "@/components/shared/empty-state";

const PIPELINE_STAGES = [
  { id: "ingest", label: "Ingest", icon: Download },
  { id: "extract", label: "Extract", icon: FileSearch },
  { id: "score", label: "Score", icon: BarChart3 },
  { id: "policy", label: "Policy", icon: Shield },
  { id: "draft", label: "Draft", icon: PenLine },
  { id: "act", label: "Act", icon: Send },
];

export default function DelegateDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const delegateId = params.id;
  const delegateName = delegateId.charAt(0).toUpperCase() + delegateId.slice(1);

  return (
    <div>
      <PageHeader
        title={`${delegateName} Delegate`}
        subtitle="Active since today · 0 processed"
        actions={
          <div className="flex items-center gap-2">
            <StatusPill variant="active" />
            <button className="px-3 py-1.5 text-xs font-medium text-slate-600 border border-slate-200 rounded-md hover:bg-slate-50 transition-colors">
              Pause
            </button>
            <a
              href={`/delegates/${delegateId}/policy`}
              className="px-3 py-1.5 text-xs font-medium text-brand-600 border border-brand-200 rounded-md hover:bg-brand-50 transition-colors"
            >
              View Policy
            </a>
          </div>
        }
      />

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: "Processed today", value: "0" },
          { label: "Pending approvals", value: "0" },
          { label: "Auto-approve rate", value: "0%" },
          { label: "Avg match score", value: "—" },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white border border-slate-200 rounded-lg p-4">
            <p className="text-xl font-bold text-slate-900 tabular-nums">{value}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Pipeline visualizer */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 mb-6">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Pipeline</p>
        <div className="flex items-center justify-between">
          {PIPELINE_STAGES.map((stage, i) => {
            const Icon = stage.icon;
            return (
              <div key={stage.id} className="flex items-center">
                <div className="flex flex-col items-center gap-2">
                  <div className="w-9 h-9 rounded-full border-2 border-slate-200 bg-slate-50 flex items-center justify-center">
                    <Icon className="w-4 h-4 text-slate-300" />
                  </div>
                  <span className="text-[10px] font-medium text-slate-300">{stage.label}</span>
                </div>
                {i < PIPELINE_STAGES.length - 1 && (
                  <div className="w-full h-px bg-slate-100 mx-3 mb-5 flex-1" style={{ minWidth: 20 }} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Two column: timeline + learning */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900">Event Timeline</h2>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg">
            <EmptyState
              icon={History}
              title="No events yet"
              description="Events will appear here as your delegate processes emails"
              size="sm"
            />
          </div>
        </div>

        {/* Learning panel */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900">Learning & Patterns</h2>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-4">
            <div>
              <p className="text-xs text-slate-400 mb-2">Delegation breakdown</p>
              <div className="flex h-2 rounded-full overflow-hidden bg-slate-100">
                <div className="bg-green-400 w-0 transition-all" />
                <div className="bg-amber-400 w-0 transition-all" />
                <div className="bg-red-400 w-0 transition-all" />
              </div>
              <div className="flex justify-between mt-1.5 text-[10px] text-slate-400">
                <span>Auto 0%</span>
                <span>Review 0%</span>
                <span>Blocked 0%</span>
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-2">Detected patterns</p>
              <p className="text-xs text-slate-300 italic">None yet. Patterns emerge after processing 10+ opportunities.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
