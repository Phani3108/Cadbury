"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/layout/page-header";
import { ShieldCheck, Trash2, Plus, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { allowlist as allowlistApi, type AllowlistRow } from "@/lib/api";

export default function AllowlistPage() {
  const [rows, setRows] = useState<AllowlistRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [newId, setNewId] = useState("");
  const [newService, setNewService] = useState("email");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRows(await allowlistApi.list());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const add = async () => {
    const id = newId.trim();
    if (!id) return;
    setBusy("add");
    try {
      await allowlistApi.add(id, newService);
      setNewId("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Add failed");
    } finally {
      setBusy(null);
    }
  };

  const remove = async (id: string) => {
    setBusy(id);
    try {
      await allowlistApi.remove(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Remove failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="Allowlist"
        subtitle="Senders & identifiers permitted to trigger delegate actions. The LLM cannot modify this list."
      />

      <div className="max-w-3xl bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {/* Add row */}
        <div className="p-4 border-b border-slate-100 flex gap-2 items-end">
          <div className="flex-1">
            <label className="block text-[11px] font-medium text-slate-500 mb-1">Identifier</label>
            <input
              value={newId}
              onChange={(e) => setNewId(e.target.value)}
              placeholder="alice@example.com, +15551234567, @handle"
              className="w-full text-sm px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
              onKeyDown={(e) => e.key === "Enter" && add()}
            />
          </div>
          <div className="w-32">
            <label className="block text-[11px] font-medium text-slate-500 mb-1">Service</label>
            <select
              value={newService}
              onChange={(e) => setNewService(e.target.value)}
              className="w-full text-sm px-2 py-2 border border-slate-200 rounded-lg bg-white"
            >
              <option value="email">email</option>
              <option value="sms">sms</option>
              <option value="slack">slack</option>
              <option value="telegram">telegram</option>
              <option value="whatsapp">whatsapp</option>
            </select>
          </div>
          <button
            onClick={add}
            disabled={!newId.trim() || busy === "add"}
            className={cn(
              "inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg transition-colors",
              newId.trim()
                ? "bg-brand-500 text-white hover:bg-brand-600"
                : "bg-slate-100 text-slate-300 cursor-not-allowed",
            )}
          >
            {busy === "add" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
            Add
          </button>
        </div>

        {/* Table */}
        {error && (
          <div className="px-4 py-2 text-xs text-red-600 bg-red-50 border-b border-red-100">{error}</div>
        )}
        {loading ? (
          <div className="p-10 flex justify-center">
            <Loader2 className="w-5 h-5 text-brand-500 animate-spin" />
          </div>
        ) : rows.length === 0 ? (
          <div className="p-10 text-center text-sm text-slate-400">
            <ShieldCheck className="w-8 h-8 text-slate-200 mx-auto mb-2" />
            Allowlist is empty. Seed one from the <span className="font-mono">ALLOWLIST</span> env var or add one above.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-slate-400">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Identifier</th>
                <th className="text-left px-4 py-2 font-medium">Service</th>
                <th className="text-left px-4 py-2 font-medium">Source</th>
                <th className="text-left px-4 py-2 font-medium">Added</th>
                <th className="text-right px-4 py-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.identifier} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-mono text-xs">{r.identifier}</td>
                  <td className="px-4 py-2 text-xs text-slate-500 capitalize">{r.service}</td>
                  <td className="px-4 py-2">
                    <span
                      className={cn(
                        "text-[10px] font-medium px-1.5 py-0.5 rounded-full uppercase",
                        r.source === "env"
                          ? "bg-amber-50 text-amber-700 border border-amber-200"
                          : "bg-slate-100 text-slate-600 border border-slate-200",
                      )}
                    >
                      {r.source}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-500">
                    {r.added_at?.slice(0, 10) ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => remove(r.identifier)}
                      disabled={busy === r.identifier || r.source === "env"}
                      title={r.source === "env" ? "Remove from the env var first" : "Remove"}
                      className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      {busy === r.identifier ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Trash2 className="w-3 h-3" />
                      )}
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
