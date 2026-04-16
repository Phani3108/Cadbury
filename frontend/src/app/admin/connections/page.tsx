"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { Check, Loader2, Link2, Unlink } from "lucide-react";
import { auth as authApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface StatusRow {
  id: "microsoft" | "google";
  label: string;
  description: string;
}

const PROVIDERS: StatusRow[] = [
  {
    id: "microsoft",
    label: "Microsoft Graph",
    description: "Read & send Outlook email, manage calendar events. OAuth2 PKCE flow.",
  },
  {
    id: "google",
    label: "Google Calendar",
    description: "Read & write calendar events and find available slots. OAuth2 PKCE flow.",
  },
];

export default function ConnectionsPage() {
  const [status, setStatus] = useState<{ microsoft: boolean; google: boolean } | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setStatus(await authApi.status());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const disconnect = async (id: StatusRow["id"]) => {
    setBusy(id);
    try {
      await authApi.disconnect(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Disconnect failed");
    } finally {
      setBusy(null);
    }
  };

  const connect = (id: StatusRow["id"]) => {
    window.location.href = authApi.loginUrl(id);
  };

  return (
    <div>
      <PageHeader
        title="Connections"
        subtitle="Link or unlink the OAuth providers that back your email and calendar access."
      />

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
        </div>
      ) : (
        <div className="max-w-2xl space-y-3">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs text-red-600">{error}</div>
          )}
          {PROVIDERS.map((p) => {
            const connected = status?.[p.id] ?? false;
            return (
              <div key={p.id} className="bg-white border border-slate-200 rounded-xl p-4 flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-800">{p.label}</span>
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium",
                        connected
                          ? "bg-green-50 text-green-700 border border-green-200"
                          : "bg-slate-100 text-slate-500 border border-slate-200",
                      )}
                    >
                      {connected ? <Check className="w-3 h-3" /> : null}
                      {connected ? "Connected" : "Not connected"}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{p.description}</p>
                </div>
                {connected ? (
                  <button
                    onClick={() => disconnect(p.id)}
                    disabled={busy === p.id}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-slate-200 hover:bg-slate-50"
                  >
                    {busy === p.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Unlink className="w-3.5 h-3.5" />
                    )}
                    Disconnect
                  </button>
                ) : (
                  <button
                    onClick={() => connect(p.id)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-brand-500 text-white hover:bg-brand-600"
                  >
                    <Link2 className="w-3.5 h-3.5" />
                    Connect
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
