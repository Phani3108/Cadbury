import { Shield, ShieldCheck, ShieldAlert, ShieldX, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";

const POLICY_ZONES = [
  {
    zone: "auto",
    label: "Auto-Approve",
    icon: ShieldCheck,
    color: "green",
    description: "Delegate acts without asking you",
    rules: ["Read & analyze emails", "Extract opportunity details", "Score against your goals"],
    threshold: "Score ≥ 65 + known recruiter",
    borderColor: "border-green-200",
    bgColor: "bg-green-50",
    iconColor: "text-green-600",
    textColor: "text-green-700",
  },
  {
    zone: "review",
    label: "Needs Your Review",
    icon: ShieldAlert,
    color: "amber",
    description: "Delegate prepares everything, you decide",
    rules: ["Sending any email reply", "Booking calendar slots", "Engaging with recruiter"],
    threshold: "Score 30–65, or first contact",
    borderColor: "border-amber-200",
    bgColor: "bg-amber-50",
    iconColor: "text-amber-600",
    textColor: "text-amber-700",
  },
  {
    zone: "block",
    label: "Auto-Reject",
    icon: ShieldX,
    color: "red",
    description: "Delegate discards without involving you",
    rules: ["Score below threshold", "Dealbreaker criteria matched", "Blocked domains"],
    threshold: "Score < 30 (disabled in MVP)",
    borderColor: "border-red-200",
    bgColor: "bg-red-50",
    iconColor: "text-red-600",
    textColor: "text-red-700",
  },
];

export default function PolicyPage({ params }: { params: { id: string } }) {
  const delegateName = params.id.charAt(0).toUpperCase() + params.id.slice(1);

  return (
    <div>
      <PageHeader
        title={`${delegateName} Delegate Policy`}
        subtitle="Control what your delegate can do automatically"
        actions={
          <button className="px-3 py-1.5 text-xs font-medium text-slate-600 border border-slate-200 rounded-md hover:bg-slate-50 transition-colors">
            Edit Policy
          </button>
        }
      />

      {/* Trust Thermostat visualization */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Trust Thermostat</p>
          <div className="flex items-center gap-1 text-xs text-slate-400">
            <Sparkles className="w-3.5 h-3.5 text-brand-400" />
            Adjust thresholds to control autonomy
          </div>
        </div>

        {/* Score range visual */}
        <div className="relative h-8 flex rounded-lg overflow-hidden mb-3">
          <div className="bg-red-100 flex items-center justify-center flex-shrink-0" style={{ width: "30%" }}>
            <span className="text-[10px] font-medium text-red-500">0 – 30</span>
          </div>
          <div className="bg-amber-100 flex items-center justify-center flex-1">
            <span className="text-[10px] font-medium text-amber-600">30 – 65</span>
          </div>
          <div className="bg-green-100 flex items-center justify-center flex-shrink-0" style={{ width: "35%" }}>
            <span className="text-[10px] font-medium text-green-600">65 – 100</span>
          </div>
        </div>
        <div className="flex justify-between text-[10px] text-slate-400">
          <span className="flex items-center gap-1"><ShieldX className="w-3 h-3 text-red-400" /> Auto-reject</span>
          <span className="flex items-center gap-1"><ShieldAlert className="w-3 h-3 text-amber-400" /> Review</span>
          <span className="flex items-center gap-1"><ShieldCheck className="w-3 h-3 text-green-500" /> Auto-approve</span>
        </div>
      </div>

      {/* Policy impact preview */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-brand-400" />
          <p className="text-xs font-semibold text-slate-700">Policy Impact (Last 30 days)</p>
        </div>
        <div className="grid grid-cols-4 gap-4 text-center">
          {[
            { label: "Processed", value: "0" },
            { label: "Auto-approved", value: "0" },
            { label: "Reviewed", value: "0" },
            { label: "Time saved", value: "0h" },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-lg font-bold text-slate-900 tabular-nums">{value}</p>
              <p className="text-[10px] text-slate-400">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Three zone cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {POLICY_ZONES.map(({ zone, label, icon: Icon, description, rules, threshold, borderColor, bgColor, iconColor, textColor }) => (
          <div key={zone} className={`border ${borderColor} ${bgColor} rounded-lg p-4`}>
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-4 h-4 ${iconColor}`} />
              <span className={`text-sm font-semibold ${textColor}`}>{label}</span>
            </div>
            <p className="text-xs text-slate-500 mb-3">{description}</p>
            <div className="space-y-1.5 mb-3">
              {rules.map((rule) => (
                <div key={rule} className="flex items-start gap-1.5 text-xs text-slate-600">
                  <span className="text-slate-300 mt-0.5">·</span>
                  {rule}
                </div>
              ))}
            </div>
            <div className="pt-3 border-t border-white/60">
              <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wide mb-0.5">Threshold</p>
              <p className="text-xs text-slate-600">{threshold}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
