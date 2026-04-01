"use client";

import { useRef, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";
import { cn } from "@/lib/utils";

interface TrustThermostatProps {
  engageThreshold: number;   // 0-1 — above this = engage (review)
  declineThreshold: number;  // 0-1 — below this = decline (review)
  onEngageChange?: (value: number) => void;
  onDeclineChange?: (value: number) => void;
  readonly?: boolean;
  className?: string;
}

// Distribution counts given thresholds (used for impact preview)
function computeZones(engageT: number, declineT: number) {
  return {
    engage: Math.round((1 - engageT) * 100),
    hold: Math.round((engageT - declineT) * 100),
    decline: Math.round(declineT * 100),
  };
}

export function TrustThermostat({
  engageThreshold,
  declineThreshold,
  onEngageChange,
  onDeclineChange,
  readonly = false,
  className,
}: TrustThermostatProps) {
  const trackRef = useRef<HTMLDivElement>(null);

  // Convert 0-1 score to % position on track
  const toPercent = (v: number) => `${v * 100}%`;

  const getValueFromEvent = useCallback(
    (e: MouseEvent | TouchEvent | React.MouseEvent | React.TouchEvent) => {
      const track = trackRef.current;
      if (!track) return null;
      const rect = track.getBoundingClientRect();
      const clientX = "touches" in e ? e.touches[0].clientX : (e as React.MouseEvent).clientX;
      const ratio = (clientX - rect.left) / rect.width;
      return Math.max(0, Math.min(1, ratio));
    },
    []
  );

  // Drag logic
  const startDrag = useCallback(
    (
      handle: "engage" | "decline",
      onMove: (v: number) => void
    ) => {
      if (readonly) return;

      const handleMove = (e: MouseEvent | TouchEvent) => {
        const v = getValueFromEvent(e as any);
        if (v === null) return;

        if (handle === "engage") {
          // engage threshold can't go below declineThreshold + 0.05
          onMove(Math.max(declineThreshold + 0.05, Math.round(v * 20) / 20));
        } else {
          // decline threshold can't exceed engageThreshold - 0.05
          onMove(Math.min(engageThreshold - 0.05, Math.round(v * 20) / 20));
        }
      };

      const stopDrag = () => {
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", stopDrag);
        window.removeEventListener("touchmove", handleMove);
        window.removeEventListener("touchend", stopDrag);
      };

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", stopDrag);
      window.addEventListener("touchmove", handleMove, { passive: true });
      window.addEventListener("touchend", stopDrag);
    },
    [readonly, declineThreshold, engageThreshold, getValueFromEvent]
  );

  const zones = computeZones(engageThreshold, declineThreshold);

  return (
    <div className={cn("select-none", className)}>
      {/* Zone legend */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-1.5 text-xs text-green-600">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="font-medium">Engage</span>
          <span className="text-slate-400">({zones.engage}% of opps)</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-amber-600">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span className="font-medium">Hold / info</span>
          <span className="text-slate-400">({zones.hold}%)</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-red-500">
          <ShieldX className="w-3.5 h-3.5" />
          <span className="font-medium">Decline</span>
          <span className="text-slate-400">({zones.decline}%)</span>
        </div>
      </div>

      {/* Track */}
      <div
        ref={trackRef}
        className="relative h-8 rounded-full overflow-hidden cursor-default"
      >
        {/* Background gradient zones */}
        <div
          className="absolute inset-0 flex"
          style={{ flexDirection: "row" }}
        >
          {/* Decline zone (left) */}
          <div
            className="h-full bg-red-100 transition-all duration-200"
            style={{ width: toPercent(declineThreshold) }}
          />
          {/* Hold zone (middle) */}
          <div
            className="h-full bg-amber-50 transition-all duration-200"
            style={{ width: toPercent(engageThreshold - declineThreshold) }}
          />
          {/* Engage zone (right) */}
          <div
            className="h-full bg-green-50 transition-all duration-200 flex-1"
          />
        </div>

        {/* Score labels on track */}
        <div className="absolute inset-0 flex items-center px-3 gap-1 pointer-events-none">
          {[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0].map((v) => (
            <div key={v} className="flex-1 flex items-center justify-center">
              {v === 0 || v === 0.5 || v === 1.0 ? (
                <span className="text-[9px] text-slate-400 font-mono">{Math.round(v * 100)}</span>
              ) : null}
            </div>
          ))}
        </div>

        {/* Decline handle */}
        <motion.div
          className={cn(
            "absolute top-0 h-full flex items-center justify-center",
            !readonly && "cursor-col-resize"
          )}
          style={{ left: toPercent(declineThreshold), transform: "translateX(-50%)" }}
          onMouseDown={() => startDrag("decline", onDeclineChange ?? (() => {}))}
          onTouchStart={() => startDrag("decline", onDeclineChange ?? (() => {}))}
          drag={false}
        >
          <div className="w-1 h-6 bg-red-400 rounded-full shadow-sm" />
        </motion.div>

        {/* Engage handle */}
        <motion.div
          className={cn(
            "absolute top-0 h-full flex items-center justify-center",
            !readonly && "cursor-col-resize"
          )}
          style={{ left: toPercent(engageThreshold), transform: "translateX(-50%)" }}
          onMouseDown={() => startDrag("engage", onEngageChange ?? (() => {}))}
          onTouchStart={() => startDrag("engage", onEngageChange ?? (() => {}))}
          drag={false}
        >
          <div className="w-1 h-6 bg-green-400 rounded-full shadow-sm" />
        </motion.div>
      </div>

      {/* Threshold labels */}
      <div className="flex justify-between mt-2 text-[10px] text-slate-400 font-mono">
        <span>0</span>
        <span
          className="text-red-400"
          style={{ marginLeft: `calc(${declineThreshold * 100}% - 2rem)` }}
        >
          {Math.round(declineThreshold * 100)}
        </span>
        <span
          className="text-green-500"
          style={{ marginLeft: `calc(${(engageThreshold - declineThreshold - 0.15) * 100}%)` }}
        >
          {Math.round(engageThreshold * 100)}
        </span>
        <span>100</span>
      </div>
    </div>
  );
}
