"use client";

import { useEffect, useCallback, ReactNode } from "react";
import {
  Target,
  DollarSign,
  MapPin,
  Building2,
  Mail,
  Check,
  Loader2,
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { GoalSection } from "@/components/goals/goal-section";
import { TagInput } from "@/components/goals/tag-input";
import { GoalsSidebar } from "@/components/goals/goals-sidebar";
import { useAutoSave } from "@/hooks/use-auto-save";
import { useGoalsStore } from "@/stores/goals-store";
import { api } from "@/lib/api";
import type { CareerGoals } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function GoalsPage() {
  const { goals, setGoals, patchGoals } = useGoalsStore();

  useEffect(() => {
    api.goals.get().then((g: CareerGoals | null) => {
      if (g) setGoals(g);
    });
  }, [setGoals]);

  const saveFn = useCallback(async (data: CareerGoals | null) => {
    if (data) await api.goals.update(data);
  }, []);

  const { status } = useAutoSave(goals, saveFn, 500);

  if (!goals) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8">
        <PageHeader
          title="Career Goals"
          subtitle="Help your delegate understand what you're looking for"
        />
        <div className="mt-8 space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-xl bg-slate-200" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Career Goals"
          subtitle="Help your delegate understand what you're looking for"
        />
        <SaveIndicator status={status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6 items-start">
        {/* Left: goal sections */}
        <div className="space-y-3">
          {/* 1. Role Preferences */}
          <GoalSection
            icon={<Target className="h-5 w-5" />}
            title="Role Preferences"
            description="What kind of role are you targeting?"
            defaultOpen
          >
            <div className="space-y-4">
              <Field label="Target titles" hint="Your delegate screens for these roles first">
                <TagInput
                  tags={goals.target_roles}
                  onChange={(v) => patchGoals({ target_roles: v })}
                  placeholder="Senior PM, VP Product, Product Lead..."
                  variant="must-have"
                />
              </Field>
              <Field label="Must-have keywords" hint="Skills or domains that must appear in the JD">
                <TagInput
                  tags={goals.must_have_criteria}
                  onChange={(v) => patchGoals({ must_have_criteria: v })}
                  placeholder="fintech, payments, SaaS..."
                  variant="must-have"
                />
              </Field>
              <Field label="Dealbreakers" hint="Your delegate will decline these automatically">
                <TagInput
                  tags={goals.dealbreakers}
                  onChange={(v) => patchGoals({ dealbreakers: v })}
                  placeholder="crypto, trading, insurance..."
                  variant="dealbreaker"
                />
              </Field>
            </div>
          </GoalSection>

          {/* 2. Compensation */}
          <GoalSection
            icon={<DollarSign className="h-5 w-5" />}
            title="Compensation"
            description="What's your minimum and ideal comp?"
          >
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Field label="Minimum base (USD/year)">
                  <input
                    type="number"
                    value={goals.min_comp_usd || ""}
                    onChange={(e) =>
                      patchGoals({ min_comp_usd: parseInt(e.target.value) || 0 })
                    }
                    placeholder="e.g. 100000"
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                  />
                </Field>
                <Field label="INR equivalent">
                  <div className="flex items-center h-[38px] rounded-lg border border-slate-100 bg-slate-50 px-3 text-sm text-slate-500">
                    {goals.min_comp_usd
                      ? `₹${((goals.min_comp_usd * 83) / 100_000).toFixed(1)}L/year`
                      : "—"}
                  </div>
                </Field>
              </div>
              <div className="flex gap-4">
                <CheckboxField
                  label="Equity matters"
                  checked={goals.comp_includes_equity}
                  onChange={(v) => patchGoals({ comp_includes_equity: v })}
                />
                <CheckboxField
                  label="Bonus included"
                  checked={goals.comp_includes_bonus}
                  onChange={(v) => patchGoals({ comp_includes_bonus: v })}
                />
              </div>
            </div>
          </GoalSection>

          {/* 3. Location */}
          <GoalSection
            icon={<MapPin className="h-5 w-5" />}
            title="Location & Work Style"
            description="Where and how do you want to work?"
          >
            <div className="space-y-4">
              <Field label="Work style">
                <div className="flex gap-2">
                  {(["remote", "hybrid", "onsite", "any"] as const).map((style) => (
                    <button
                      key={style}
                      type="button"
                      onClick={() => patchGoals({ work_style: style })}
                      className={cn(
                        "flex-1 rounded-lg border py-2 text-xs font-medium capitalize transition-colors",
                        goals.work_style === style
                          ? "border-brand-500 bg-brand-50 text-brand-700"
                          : "border-slate-200 text-slate-500 hover:border-slate-300"
                      )}
                    >
                      {style}
                    </button>
                  ))}
                </div>
              </Field>
              <Field label="Preferred cities">
                <TagInput
                  tags={goals.preferred_locations}
                  onChange={(v) => patchGoals({ preferred_locations: v })}
                  placeholder="Bangalore, Hyderabad, Remote..."
                />
              </Field>
              <CheckboxField
                label="Open to relocation"
                checked={goals.open_to_relocation}
                onChange={(v) => patchGoals({ open_to_relocation: v })}
              />
            </div>
          </GoalSection>

          {/* 4. Company */}
          <GoalSection
            icon={<Building2 className="h-5 w-5" />}
            title="Company Preferences"
            description="What kind of company do you want to join?"
          >
            <div className="space-y-4">
              <Field label="Company stage">
                <div className="flex flex-wrap gap-2">
                  {["Pre-seed", "Seed", "Series A", "Series B", "Series C", "Growth", "Public"].map(
                    (stage) => {
                      const selected = goals.company_stages.includes(stage);
                      return (
                        <button
                          key={stage}
                          type="button"
                          onClick={() => {
                            const next = selected
                              ? goals.company_stages.filter((s) => s !== stage)
                              : [...goals.company_stages, stage];
                            patchGoals({ company_stages: next });
                          }}
                          className={cn(
                            "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                            selected
                              ? "border-brand-500 bg-brand-50 text-brand-700"
                              : "border-slate-200 text-slate-500 hover:border-slate-300"
                          )}
                        >
                          {stage}
                        </button>
                      );
                    }
                  )}
                </div>
              </Field>
              <Field label="Preferred industries">
                <TagInput
                  tags={goals.preferred_industries}
                  onChange={(v) => patchGoals({ preferred_industries: v })}
                  placeholder="Fintech, SaaS, B2B..."
                  variant="must-have"
                />
              </Field>
              <Field label="Companies to avoid" hint="Your delegate will flag or decline roles from these">
                <TagInput
                  tags={goals.avoid_companies}
                  onChange={(v) => patchGoals({ avoid_companies: v })}
                  placeholder="Add company names..."
                  variant="dealbreaker"
                />
              </Field>
            </div>
          </GoalSection>

          {/* 5. Communication */}
          <GoalSection
            icon={<Mail className="h-5 w-5" />}
            title="Communication Style"
            description="How should your delegate write on your behalf?"
          >
            <div className="space-y-4">
              <Field label="Tone for outbound messages">
                <div className="flex gap-2">
                  {(["professional", "casual", "formal"] as const).map((tone) => (
                    <button
                      key={tone}
                      type="button"
                      onClick={() => patchGoals({ communication_tone: tone })}
                      className={cn(
                        "flex-1 rounded-lg border py-2 text-xs font-medium capitalize transition-colors",
                        goals.communication_tone === tone
                          ? "border-brand-500 bg-brand-50 text-brand-700"
                          : "border-slate-200 text-slate-500 hover:border-slate-300"
                      )}
                    >
                      {tone}
                    </button>
                  ))}
                </div>
              </Field>
              <p className="text-xs text-slate-400">
                {goals.communication_tone === "professional" &&
                  "Warm but business-like. Complete sentences, no slang."}
                {goals.communication_tone === "casual" &&
                  "Conversational and friendly. Contractions okay, first-name basis."}
                {goals.communication_tone === "formal" &&
                  "Structured and polished. Full titles, no contractions."}
              </p>
            </div>
          </GoalSection>
        </div>

        {/* Right: delegate preview */}
        <div className="lg:sticky lg:top-6">
          <GoalsSidebar />
        </div>
      </div>
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-medium text-slate-700">{label}</label>
      {hint && <p className="text-[11px] text-slate-400">{hint}</p>}
      {children}
    </div>
  );
}

function CheckboxField({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <div
        onClick={() => onChange(!checked)}
        className={cn(
          "h-4 w-4 rounded border flex items-center justify-center transition-colors cursor-pointer",
          checked ? "border-brand-500 bg-brand-500" : "border-slate-300 bg-white"
        )}
      >
        {checked && <Check className="h-2.5 w-2.5 text-white" />}
      </div>
      <span className="text-sm text-slate-600">{label}</span>
    </label>
  );
}

function SaveIndicator({ status }: { status: string }) {
  if (status === "saving") {
    return (
      <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-1">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Saving...
      </div>
    );
  }
  if (status === "saved") {
    return (
      <div className="flex items-center gap-1.5 text-xs text-green-600 mt-1">
        <Check className="h-3.5 w-3.5" />
        Saved
      </div>
    );
  }
  if (status === "error") {
    return <span className="text-xs text-red-500 mt-1">Save failed</span>;
  }
  return null;
}
