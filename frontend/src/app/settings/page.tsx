"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Brain,
  Mail,
  Building2,
  Server,
  Settings2,
  Check,
  X,
  Loader2,
  RotateCcw,
  FlaskConical,
  Save,
  Eye,
  EyeOff,
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  RefreshCw,
  Mic,
} from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface IntegrationStatus {
  key: string;
  label: string;
  description: string;
  configured: boolean;
  masked_value: string;
  source: "env" | "override" | "none";
  required: boolean;
  category: string;
}

interface TestResult {
  success: boolean;
  message: string;
}

type CategoryMeta = {
  id: string;
  label: string;
  icon: React.ElementType;
  description: string;
};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CATEGORIES: CategoryMeta[] = [
  { id: "ai", label: "AI Engine", icon: Brain, description: "Language model configuration for all AI-powered features" },
  { id: "voice", label: "Voice", icon: Mic, description: "Speech-to-text and text-to-speech keys for the voice chat interface" },
  { id: "email", label: "Email Integration", icon: Mail, description: "Microsoft Graph connection for email and calendar access" },
  { id: "enrichment", label: "Company Enrichment", icon: Building2, description: "Third-party data providers for company and contact enrichment" },
  { id: "infrastructure", label: "Infrastructure", icon: Server, description: "Core infrastructure services and connections" },
  { id: "general", label: "General", icon: Settings2, description: "Application behavior and tuning parameters" },
];

const TESTABLE_KEYS = new Set([
  "openai_api_key",
  "msgraph_client_id",
  "apollo_api_key",
  "redis_url",
]);

const SECRET_KEYS = new Set([
  "openai_api_key",
  "msgraph_client_secret",
  "apollo_api_key",
  "redis_url",
  "groq_api_key",
  "elevenlabs_api_key",
]);

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  const [integrations, setIntegrations] = useState<IntegrationStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Per-field state maps
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});
  const [testResults, setTestResults] = useState<Record<string, TestResult | null>>({});
  const [saveResults, setSaveResults] = useState<Record<string, { success: boolean; message: string } | null>>({});
  const [deleting, setDeleting] = useState<Record<string, boolean>>({});
  const [showValues, setShowValues] = useState<Record<string, boolean>>({});

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API}/v1/settings`);
      if (!res.ok) throw new Error(`Failed to load settings (${res.status})`);
      const data = await res.json();
      setIntegrations(data.integrations ?? []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  const handleSave = async (key: string) => {
    const value = values[key];
    if (!value || value.trim() === "") return;

    setSaving((p) => ({ ...p, [key]: true }));
    setSaveResults((p) => ({ ...p, [key]: null }));
    setTestResults((p) => ({ ...p, [key]: null }));

    try {
      const res = await fetch(`${API}/v1/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value: value.trim() }),
      });
      if (!res.ok) throw new Error(`Save failed (${res.status})`);
      const data = await res.json();
      setSaveResults((p) => ({ ...p, [key]: { success: data.success !== false, message: "Saved successfully" } }));
      setValues((p) => ({ ...p, [key]: "" }));
      await fetchSettings();
    } catch (err: unknown) {
      setSaveResults((p) => ({
        ...p,
        [key]: { success: false, message: err instanceof Error ? err.message : "Save failed" },
      }));
    } finally {
      setSaving((p) => ({ ...p, [key]: false }));
      setTimeout(() => setSaveResults((p) => ({ ...p, [key]: null })), 4000);
    }
  };

  const handleTest = async (key: string) => {
    setTesting((p) => ({ ...p, [key]: true }));
    setTestResults((p) => ({ ...p, [key]: null }));

    try {
      const res = await fetch(`${API}/v1/settings/test/${key}`, { method: "POST" });
      if (!res.ok) throw new Error(`Test failed (${res.status})`);
      const data = await res.json();
      setTestResults((p) => ({ ...p, [key]: { success: data.success, message: data.message } }));
    } catch (err: unknown) {
      setTestResults((p) => ({
        ...p,
        [key]: { success: false, message: err instanceof Error ? err.message : "Connection test failed" },
      }));
    } finally {
      setTesting((p) => ({ ...p, [key]: false }));
      setTimeout(() => setTestResults((p) => ({ ...p, [key]: null })), 6000);
    }
  };

  const handleDelete = async (key: string) => {
    setDeleting((p) => ({ ...p, [key]: true }));
    try {
      const res = await fetch(`${API}/v1/settings/${key}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`Delete failed (${res.status})`);
      setValues((p) => ({ ...p, [key]: "" }));
      setTestResults((p) => ({ ...p, [key]: null }));
      setSaveResults((p) => ({ ...p, [key]: null }));
      await fetchSettings();
    } catch {
      // silently ignore
    } finally {
      setDeleting((p) => ({ ...p, [key]: false }));
    }
  };

  // ---------------------------------------------------------------------------
  // Derived data
  // ---------------------------------------------------------------------------

  const configuredCount = integrations.filter((i) => i.configured).length;
  const totalCount = integrations.length;
  const progressPct = totalCount > 0 ? Math.round((configuredCount / totalCount) * 100) : 0;

  const grouped = CATEGORIES.map((cat) => ({
    ...cat,
    items: integrations.filter((i) => i.category === cat.id),
  })).filter((g) => g.items.length > 0);

  // ---------------------------------------------------------------------------
  // Sub-components
  // ---------------------------------------------------------------------------

  function StatusBadge({ item }: { item: IntegrationStatus }) {
    if (item.configured && item.source === "override") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
          <ShieldCheck className="w-3 h-3" />
          Connected
        </span>
      );
    }
    if (item.configured && item.source === "env") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
          <AlertCircle className="w-3 h-3" />
          From .env
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-600 border border-red-200">
        <ShieldAlert className="w-3 h-3" />
        Not configured
      </span>
    );
  }

  function SettingRow({ item }: { item: IntegrationStatus }) {
    const isSecret = SECRET_KEYS.has(item.key);
    const isTestable = TESTABLE_KEYS.has(item.key);
    const isSaving = saving[item.key] ?? false;
    const isTesting = testing[item.key] ?? false;
    const isDeleting = deleting[item.key] ?? false;
    const testResult = testResults[item.key] ?? null;
    const saveResult = saveResults[item.key] ?? null;
    const fieldValue = values[item.key] ?? "";
    const visible = showValues[item.key] ?? false;

    return (
      <div className="py-4 first:pt-0 last:pb-0">
        {/* Row: responsive flex */}
        <div className="flex flex-col lg:flex-row lg:items-start gap-4">
          {/* Left: label + description + badge */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-slate-800">{item.label}</span>
              {item.required && (
                <span className="text-[10px] font-semibold uppercase tracking-wider text-red-400">Required</span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{item.description}</p>
            <div className="mt-1.5 flex items-center gap-2">
              <StatusBadge item={item} />
              {item.configured && item.masked_value && (
                <span className="text-xs text-slate-400 font-mono">{item.masked_value}</span>
              )}
            </div>
          </div>

          {/* Right: input + actions */}
          <div className="flex-shrink-0 w-full lg:w-[380px] space-y-2">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <input
                  type={isSecret && !visible ? "password" : "text"}
                  value={fieldValue}
                  onChange={(e) => setValues((p) => ({ ...p, [item.key]: e.target.value }))}
                  placeholder={item.configured ? item.masked_value || "Update value..." : "Enter value..."}
                  className={cn(
                    "w-full text-sm border rounded-lg px-3 py-2 pr-8 font-mono transition-colors",
                    "border-slate-200 bg-white placeholder:text-slate-300",
                    "focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
                  )}
                />
                {isSecret && (
                  <button
                    type="button"
                    onClick={() => setShowValues((p) => ({ ...p, [item.key]: !visible }))}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500 transition-colors"
                  >
                    {visible ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>

              {/* Save button */}
              <button
                onClick={() => handleSave(item.key)}
                disabled={isSaving || !fieldValue.trim()}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg transition-all",
                  fieldValue.trim()
                    ? "bg-brand-500 text-white hover:bg-brand-600 shadow-sm"
                    : "bg-slate-100 text-slate-300 cursor-not-allowed"
                )}
              >
                {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                Save
              </button>

              {/* Test button */}
              {isTestable && (
                <button
                  onClick={() => handleTest(item.key)}
                  disabled={isTesting || !item.configured}
                  className={cn(
                    "inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg transition-all",
                    item.configured
                      ? "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      : "bg-slate-50 text-slate-300 cursor-not-allowed"
                  )}
                >
                  {isTesting ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <FlaskConical className="w-3.5 h-3.5" />
                  )}
                  Test
                </button>
              )}
            </div>

            {/* Inline feedback */}
            <div className="min-h-[20px]">
              {testResult && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 text-xs font-medium animate-in fade-in slide-in-from-top-1 duration-200",
                    testResult.success ? "text-green-600" : "text-red-500"
                  )}
                >
                  {testResult.success ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                  {testResult.message}
                </div>
              )}
              {saveResult && !testResult && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 text-xs font-medium animate-in fade-in slide-in-from-top-1 duration-200",
                    saveResult.success ? "text-green-600" : "text-red-500"
                  )}
                >
                  {saveResult.success ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                  {saveResult.message}
                </div>
              )}
              {item.source === "override" && !testResult && !saveResult && (
                <button
                  onClick={() => handleDelete(item.key)}
                  disabled={isDeleting}
                  className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-red-500 transition-colors"
                >
                  {isDeleting ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <RotateCcw className="w-3 h-3" />
                  )}
                  Reset to default
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Manage integrations, API keys, and application configuration"
        actions={
          <button
            onClick={fetchSettings}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
            Refresh
          </button>
        }
      />

      <div className="max-w-4xl space-y-6">
        {/* ------ Quick links to admin sub-pages ------ */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {[
            { href: "/admin/connections", label: "Connections", hint: "OAuth providers" },
            { href: "/admin/budgets", label: "Budgets", hint: "Per-delegate limits" },
            { href: "/admin/allowlist", label: "Allowlist", hint: "Trusted senders" },
            { href: "/admin/health", label: "System Health", hint: "Live metrics" },
          ].map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="bg-white border border-slate-200 rounded-lg px-3 py-2 hover:border-brand-300 hover:bg-brand-50/40 transition-colors"
            >
              <div className="text-sm font-medium text-slate-800">{link.label}</div>
              <div className="text-[10px] text-slate-400">{link.hint}</div>
            </a>
          ))}
        </div>

        {/* ------ Status banner ------ */}
        {!loading && !error && totalCount > 0 && (
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div
                  className={cn(
                    "w-2 h-2 rounded-full",
                    configuredCount === totalCount ? "bg-green-500" : configuredCount > 0 ? "bg-amber-400" : "bg-red-400"
                  )}
                />
                <span className="text-sm font-medium text-slate-700">
                  {configuredCount} of {totalCount} integrations configured
                </span>
              </div>
              <span className="text-xs font-medium text-slate-400">{progressPct}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-500",
                  configuredCount === totalCount
                    ? "bg-green-500"
                    : configuredCount > 0
                    ? "bg-brand-500"
                    : "bg-slate-200"
                )}
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        )}

        {/* ------ Loading ------ */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
            <span className="ml-2 text-sm text-slate-400">Loading settings...</span>
          </div>
        )}

        {/* ------ Error ------ */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-center">
            <ShieldAlert className="w-8 h-8 text-red-300 mx-auto mb-2" />
            <p className="text-sm font-medium text-red-700 mb-1">Failed to load settings</p>
            <p className="text-xs text-red-400 mb-3">{error}</p>
            <button
              onClick={fetchSettings}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry
            </button>
          </div>
        )}

        {/* ------ Category cards ------ */}
        {!loading &&
          !error &&
          grouped.map((group) => {
            const Icon = group.icon;
            return (
              <div
                key={group.id}
                className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden"
              >
                {/* Card header */}
                <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-brand-50 border border-brand-100 flex items-center justify-center">
                      <Icon className="w-4 h-4 text-brand-600" />
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-slate-800">{group.label}</h2>
                      <p className="text-xs text-slate-400">{group.description}</p>
                    </div>
                  </div>
                </div>

                {/* Setting rows */}
                <div className="px-5 divide-y divide-slate-100">
                  {group.items.map((item) => (
                    <SettingRow key={item.key} item={item} />
                  ))}
                </div>
              </div>
            );
          })}

        {/* ------ Empty state (no integrations returned at all) ------ */}
        {!loading && !error && integrations.length === 0 && (
          <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
            <Settings2 className="w-10 h-10 text-slate-200 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-600 mb-1">No settings available</p>
            <p className="text-xs text-slate-400">The backend did not return any configuration entries.</p>
          </div>
        )}
      </div>
    </div>
  );
}
