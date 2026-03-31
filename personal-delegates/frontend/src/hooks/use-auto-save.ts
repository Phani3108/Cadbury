"use client";

import { useEffect, useRef, useState, useCallback } from "react";

type SaveStatus = "idle" | "saving" | "saved" | "error";

export function useAutoSave<T>(
  data: T,
  saveFn: (data: T) => Promise<void>,
  debounceMs = 500
) {
  const [status, setStatus] = useState<SaveStatus>("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);
  const isFirstRender = useRef(true);

  const save = useCallback(
    async (d: T) => {
      setStatus("saving");
      try {
        await saveFn(d);
        if (isMountedRef.current) setStatus("saved");
        setTimeout(() => {
          if (isMountedRef.current) setStatus("idle");
        }, 2000);
      } catch {
        if (isMountedRef.current) setStatus("error");
      }
    },
    [saveFn]
  );

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => save(data), debounceMs);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [data, debounceMs, save]);

  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);

  return { status };
}
