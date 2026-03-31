import { Inbox, TrendingUp, CheckCheck, Bot, Calendar, DollarSign, MessageSquare, Target } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusPill } from "@/components/shared/status-pill";
import { cn } from "@/lib/utils";

// Stat card component
function StatCard({
  icon: Icon,
  label,
  value,
  href,
  accent,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
  href: string;
  accent?: string;
}) {
  return (
    <Link
      href={href}
      className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-150 group"
    >
      <div className="flex items-center justify-between mb-3">
        <div className={cn("w-8 h-8 rounded-md flex items-center justify-center", accent ?? "bg-slate-100")}>
          <Icon className={cn("w-4 h-4", accent ? "text-white" : "text-slate-500")} />
        </div>
      </div>
      <p className="text-2xl font-bold text-slate-900 tabular-nums">{value}</p>
      <p className="text-xs text-slate-400 mt-0.5">{label}</p>
    </Link>
  );
}

// Delegate card (active)
function DelegateCard() {
  return (
    <Link
      href="/delegates/recruiter"
      className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-150"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="w-9 h-9 rounded-lg bg-brand-50 flex items-center justify-center">
          <Bot className="w-5 h-5 text-brand-500" />
        </div>
        <StatusPill variant="active" size="sm" />
      </div>
      <p className="text-sm font-semibold text-slate-900">Recruiter Delegate</p>
      <p className="text-xs text-slate-400 mt-0.5 mb-3">Screens inbound opportunities</p>
      <div className="grid grid-cols-3 gap-2 text-center">
        {[
          { label: "Today", value: "0" },
          { label: "Pending", value: "0" },
          { label: "Auto", value: "0%" },
        ].map(({ label, value }) => (
          <div key={label}>
            <p className="text-sm font-semibold text-slate-900 tabular-nums">{value}</p>
            <p className="text-[10px] text-slate-400">{label}</p>
          </div>
        ))}
      </div>
    </Link>
  );
}

// Coming soon delegate card
function EmptyDelegateCard({ name, icon: Icon }: { name: string; icon: React.ComponentType<{ className?: string }> }) {
  return (
    <div className="bg-white border border-dashed border-slate-200 rounded-lg p-4 cursor-default">
      <div className="flex items-start justify-between mb-3">
        <div className="w-9 h-9 rounded-lg bg-slate-50 flex items-center justify-center">
          <Icon className="w-5 h-5 text-slate-300" />
        </div>
        <span className="text-[10px] font-medium text-slate-300 bg-slate-50 rounded px-1.5 py-0.5">
          Soon
        </span>
      </div>
      <p className="text-sm font-medium text-slate-300">{name} Delegate</p>
      <p className="text-xs text-slate-200 mt-0.5">Coming soon</p>
    </div>
  );
}

export default function DashboardPage() {
  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  })();

  return (
    <div>
      <PageHeader
        title={`${greeting}`}
        subtitle="Here's what your delegates need from you today"
      />

      {/* Attention strip */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard
          icon={Inbox}
          label="Approvals waiting"
          value={0}
          href="/approvals"
          accent="bg-amber-400"
        />
        <StatCard
          icon={TrendingUp}
          label="High-match opportunities"
          value={0}
          href="/opportunities"
          accent="bg-brand-500"
        />
        <StatCard
          icon={CheckCheck}
          label="Handled automatically today"
          value={0}
          href="/delegates/recruiter"
          accent="bg-green-500"
        />
      </div>

      {/* Main 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Pending approvals */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900">Pending Approvals</h2>
            <Link href="/approvals" className="text-xs text-brand-500 hover:text-brand-600 font-medium">
              View all →
            </Link>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg">
            <EmptyState
              icon={Inbox}
              title="All clear"
              description="No approvals waiting. Your delegates are all caught up."
              size="sm"
            />
          </div>
        </div>

        {/* Right: Activity feed */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900">Activity</h2>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg">
            <EmptyState
              icon={Target}
              title="No activity yet"
              description="Connect your email to get started."
              size="sm"
              action={
                <Link
                  href="/settings"
                  className="text-xs font-medium text-brand-500 hover:text-brand-600"
                >
                  Connect email →
                </Link>
              }
            />
          </div>
        </div>
      </div>

      {/* Delegates row */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-slate-900">Your Delegates</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <DelegateCard />
          <EmptyDelegateCard name="Calendar" icon={Calendar} />
          <EmptyDelegateCard name="Finance" icon={DollarSign} />
          <EmptyDelegateCard name="Comms" icon={MessageSquare} />
        </div>
      </div>
    </div>
  );
}
