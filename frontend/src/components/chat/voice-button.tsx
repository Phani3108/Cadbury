"use client";

import { Mic, Square, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { VoiceState } from "@/hooks/use-voice-session";

interface Props {
  state: VoiceState;
  amplitude: number;
  onStart: () => void;
  onStop: () => void;
  disabled?: boolean;
}

export function VoiceButton({ state, amplitude, onStart, onStop, disabled }: Props) {
  const isRecording = state === "recording";
  const isProcessing = state === "processing";
  const pulseScale = 1 + Math.min(amplitude * 8, 0.5);

  const handleClick = () => {
    if (disabled || isProcessing) return;
    if (isRecording) onStop();
    else onStart();
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled || isProcessing}
      aria-label={isRecording ? "Stop recording" : "Start recording"}
      className={cn(
        "relative inline-flex items-center justify-center w-10 h-10 rounded-full transition-all",
        "disabled:opacity-40 disabled:cursor-not-allowed",
        isRecording
          ? "bg-red-500 text-white hover:bg-red-600"
          : "bg-brand-50 text-brand-600 hover:bg-brand-100 border border-brand-200",
      )}
      style={isRecording ? { transform: `scale(${pulseScale})` } : undefined}
    >
      {isProcessing ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : isRecording ? (
        <Square className="w-4 h-4" />
      ) : (
        <Mic className="w-4 h-4" />
      )}
      {isRecording && (
        <span className="absolute -inset-1 rounded-full border-2 border-red-300 animate-ping" />
      )}
    </button>
  );
}
