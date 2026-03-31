"use client";
import { useGoalsStore } from "@/stores/goals-store";
import { Bot, Target, DollarSign, MapPin, Building2, Mail } from "lucide-react";

export function GoalsSidebar() {
  const goals = useGoalsStore((s) => s.goals);

  if (!goals) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Bot className="h-4 w-4 text-brand-600" />
          <p className="text-sm font-semibold text-slate-700">What your delegate sees</p>
        </div>
        <p className="text-xs text-slate-400">Fill in your goals to see how your delegate interprets them.</p>
      </div>
    );
  }

  const lines: { icon: React.ReactNode; text: string }[] = [];

  if (goals.target_roles.length) {
    lines.push({
      icon: <Target className="h-3.5 w-3.5 text-green-600" />,
      text: `Looking for: ${goals.target_roles.slice(0, 3).join(", ")}${goals.target_roles.length > 3 ? " + more" : ""}`,
    });
  }

  if (goals.min_comp_usd) {
    lines.push({
      icon: <DollarSign className="h-3.5 w-3.5 text-brand-600" />,
      text: `Minimum comp: $${(goals.min_comp_usd / 1000).toFixed(0)}k/year (~₹${(goals.min_comp_usd * 83 / 100_000).toFixed(0)}L)`,
    });
  }

  if (goals.work_style) {
    const styles: Record<string, string> = {
      remote: "Fully remote only",
      hybrid: "Open to hybrid",
      onsite: "Onsite preferred",
      any: "Flexible on location",
    };
    lines.push({
      icon: <MapPin className="h-3.5 w-3.5 text-slate-500" />,
      text: styles[goals.work_style] || goals.work_style,
    });
  }

  if (goals.preferred_locations.length) {
    lines.push({
      icon: <MapPin className="h-3.5 w-3.5 text-slate-400" />,
      text: `Preferred cities: ${goals.preferred_locations.join(", ")}`,
    });
  }

  if (goals.company_stages.length) {
    lines.push({
      icon: <Building2 className="h-3.5 w-3.5 text-slate-500" />,
      text: `Company stage: ${goals.company_stages.join(", ")}`,
    });
  }

  if (goals.dealbreakers.length) {
    lines.push({
      icon: <span className="h-3.5 w-3.5 rounded-full bg-red-500 flex-shrink-0" />,
      text: `Never: ${goals.dealbreakers.join(", ")}`,
    });
  }

  if (goals.must_have_criteria.length) {
    lines.push({
      icon: <span className="h-3.5 w-3.5 rounded-full bg-green-500 flex-shrink-0" />,
      text: `Must include: ${goals.must_have_criteria.join(", ")}`,
    });
  }

  if (goals.communication_tone) {
    lines.push({
      icon: <Mail className="h-3.5 w-3.5 text-slate-400" />,
      text: `Tone: ${goals.communication_tone}`,
    });
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50">
          <Bot className="h-4 w-4 text-brand-600" />
        </span>
        <p className="text-sm font-semibold text-slate-700">What your delegate sees</p>
      </div>

      {lines.length === 0 ? (
        <p className="text-xs text-slate-400">Your delegate has no guidance yet — fill in the sections on the left.</p>
      ) : (
        <ul className="space-y-2.5">
          {lines.map((l, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="mt-0.5 flex-shrink-0">{l.icon}</span>
              <span className="text-xs text-slate-600 leading-relaxed">{l.text}</span>
            </li>
          ))}
        </ul>
      )}

      <p className="mt-4 text-[11px] text-slate-400 leading-relaxed">
        This summary updates as you type. Your delegate uses these rules to score and respond to every recruiter message.
      </p>
    </div>
  );
}
