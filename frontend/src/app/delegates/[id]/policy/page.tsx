"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, RefreshCw, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { TrustThermostat } from "@/components/policy/trust-thermostat";
import { RuleCard } from "@/components/policy/rule-card";
import { PolicyImpactCard } from "@/components/policy/policy-impact";
import { api } from "@/lib/api";
import type { DelegationPolicy, PolicyImpact, TrustZone } from "@/lib/types";

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-100 rounded-md ${className ?? ""}`} />;
}

export default function PolicyPage({ params }: { params: { id: string } }) {
  const delegateId = params.id;
  const delegateName = delegateId.charAt(0).toUpperCase() + delegateId.slice(1);

  const [pol, setPol] = useState<DelegationPolicy | null>(null);
  const [impact, setImpact] = useState<PolicyImpact | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.policy.get(delegateId).catch(() => null),
      api.policy.impact(delegateId).catch(() => null),
    ]).then(([p, i]) => {
      setPol(p as DelegationPolicy | null);
      setImpact(i as PolicyImpact | null);
      setLoading(false);
    });
  }, [delegateId]);

  // Derive threshold values from policy (0-1 scale)
  const engageThreshold = pol ? pol.thresholds.auto_approve_above / 100 : 0.65;
  const declineThreshold = pol ? pol.thresholds.auto_reject_below / 100 : 0.3;

  // Group actions by zone
  const actionsByZone: Record<TrustZone, typeof pol extends null ? [] : NonNullable<typeof pol>["allowed_actions"]> = {
    auto: pol?.allowed_actions.filter((a) => a.zone === "auto") ?? [],
    review: pol?.allowed_actions.filter((a) => a.zone === "review") ?? [],
    block: pol?.allowed_actions.filter((a) => a.zone === "block") ?? [],
  };

  return (
    <div>
      <PageHeader
        title={`${delegateName} · Policy`}
        subtitle="Control what your delegate can do automatically"
        actions={
          <div className="flex items-center gap-2">
            <Link
              href={`/delegates/${delegateId}`}
              className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
            >
              <ChevronLeft className="w-3 h-3" />
              Back to delegate
            </Link>
          </div>
        }
      />


      {/* Trust Thermostat */}
      <div className="mb-6">
        {loading ? (
          <Skeleton className="h-36 w-full" />
        ) : pol ? (
          <TrustThermostat
            engageThreshold={engageThreshold}
            declineThreshold={declineThreshold}
            readonly
          />
        ) : (
          <div className="bg-white border border-slate-200 rounded-lg p-6 text-center text-sm text-slate-400">
            Policy not loaded
          </div>
        )}
      </div>

      {/* Impact + Rule grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Impact card spans full width at top on small screens, 1 col on lg */}
        <div className="lg:col-span-1">
          {loading ? (
            <Skeleton className="h-36 w-full" />
          ) : impact ? (
            <PolicyImpactCard impact={impact} />
          ) : (
            <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center justify-center h-36">
              <div className="flex flex-col items-center gap-1.5 text-slate-300">
                <RefreshCw className="w-5 h-5" />
                <span className="text-xs">No impact data yet</span>
              </div>
            </div>
          )}
        </div>

        {/* Rule Cards — 2 columns */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {loading ? (
            <>
              <Skeleton className="h-36 w-full" />
              <Skeleton className="h-36 w-full" />
            </>
          ) : (
            <>
              <RuleCard zone="auto" actions={actionsByZone.auto} />
              <RuleCard zone="review" actions={actionsByZone.review} />
            </>
          )}
        </div>
      </div>

      {/* Block zone full-width */}
      {!loading && actionsByZone.block.length > 0 && (
        <RuleCard zone="block" actions={actionsByZone.block} />
      )}

      {/* Empty state for no policy */}
      {!loading && !pol && (
        <div className="mt-8 flex flex-col items-center gap-3 text-slate-300 py-16">
          <ShieldCheck className="w-10 h-10" />
          <p className="text-sm">No policy configured for this delegate yet.</p>
        </div>
      )}
    </div>
  );
}
