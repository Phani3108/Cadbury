"use client";

import { useEffect, useCallback } from "react";

type ShortcutHandler = (e: KeyboardEvent) => void;

interface Shortcut {
  key: string;
  meta?: boolean;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  handler: ShortcutHandler;
  description?: string;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Don't fire when typing in inputs
      const target = e.target as HTMLElement;
      const isInput =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      for (const shortcut of shortcuts) {
        const metaMatch = shortcut.meta ? (e.metaKey || e.ctrlKey) : !e.metaKey && !e.ctrlKey;
        const ctrlMatch = shortcut.ctrl ? e.ctrlKey : shortcut.ctrl === undefined ? true : !e.ctrlKey;
        const shiftMatch = shortcut.shift ? e.shiftKey : shortcut.shift === undefined ? true : !e.shiftKey;
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();

        if (keyMatch && metaMatch && shiftMatch) {
          // Allow meta+key shortcuts even in inputs (e.g., Cmd+K, Cmd+Enter)
          if (isInput && !shortcut.meta) continue;
          e.preventDefault();
          shortcut.handler(e);
          return;
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}
