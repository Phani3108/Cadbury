import { Settings, Mail } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";

export default function SettingsPage() {
  return (
    <div>
      <PageHeader title="Settings" subtitle="Configure your delegates and connections" />

      <div className="max-w-2xl space-y-4">
        {/* Email connection */}
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-md bg-slate-100 flex items-center justify-center">
              <Mail className="w-4 h-4 text-slate-500" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">Email Connection</p>
              <p className="text-xs text-slate-400">Connect your mailbox so delegates can read and respond to emails</p>
            </div>
          </div>
          <button className="px-4 py-2 text-sm font-medium bg-brand-500 text-white rounded-md hover:bg-brand-600 transition-colors">
            Connect Microsoft 365
          </button>
        </div>

        {/* API config */}
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-md bg-slate-100 flex items-center justify-center">
              <Settings className="w-4 h-4 text-slate-500" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">API Configuration</p>
              <p className="text-xs text-slate-400">Backend connection and LLM settings</p>
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">API URL</label>
              <input
                type="text"
                defaultValue="http://localhost:8000"
                className="w-full text-sm border border-slate-200 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
