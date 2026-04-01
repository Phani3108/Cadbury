"use client";

import { useRef, useEffect, useState } from "react";
import { PenLine, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

interface DraftEditorProps {
  draft: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
  focused?: boolean;
  className?: string;
  originalDraft?: string;
}

export function DraftEditor({
  draft,
  onChange,
  readOnly = false,
  focused = false,
  className,
  originalDraft,
}: DraftEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isDirty, setIsDirty] = useState(false);

  // Auto-resize
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [draft]);

  // Focus when requested
  useEffect(() => {
    if (focused && textareaRef.current) {
      textareaRef.current.focus();
      // Place cursor at end
      const len = textareaRef.current.value.length;
      textareaRef.current.setSelectionRange(len, len);
    }
  }, [focused]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    setIsDirty(originalDraft !== undefined && e.target.value !== originalDraft);
  };

  const handleRevert = () => {
    if (originalDraft !== undefined) {
      onChange(originalDraft);
      setIsDirty(false);
    }
  };

  return (
    <div className={cn("relative", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <PenLine className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs font-medium text-slate-500">Draft reply</span>
          {isDirty && (
            <span className="text-[10px] text-brand-500 font-medium">edited</span>
          )}
        </div>
        {isDirty && !readOnly && (
          <button
            type="button"
            onClick={handleRevert}
            className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-600 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Revert
          </button>
        )}
      </div>

      {/* Textarea */}
      <textarea
        ref={textareaRef}
        value={draft}
        onChange={handleChange}
        readOnly={readOnly}
        rows={6}
        className={cn(
          "w-full resize-none rounded-lg border text-sm leading-relaxed p-3 transition-colors font-[inherit] focus:outline-none",
          readOnly
            ? "bg-slate-50 border-slate-100 text-slate-600 cursor-default"
            : "bg-white border-slate-200 text-slate-800 focus:border-brand-400 focus:ring-1 focus:ring-brand-200"
        )}
        placeholder="No draft yet…"
      />
    </div>
  );
}
