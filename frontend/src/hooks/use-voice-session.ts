"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Voice capture hook — mirrors Rose's asymmetric VAD.
 *
 *   activation threshold: RMS > 0.002 for 1 frame → start recording
 *   deactivation threshold: RMS < 0.001 for 15 frames (~250ms) → stop recording
 *   hard stop: 30s max duration
 *
 * The hook exposes a tap-to-start, tap-to-stop interface. Callers pass a
 * `onStop` callback that receives the recorded Blob.
 */
export type VoiceState = "idle" | "listening" | "recording" | "processing" | "error";

const ACTIVATION_THRESHOLD = 0.002;
const DEACTIVATION_THRESHOLD = 0.001;
const ACTIVATION_FRAMES = 1;
const DEACTIVATION_FRAMES = 15;
const MAX_DURATION_MS = 30_000;

export interface VoiceSessionOptions {
  onStop: (blob: Blob) => void | Promise<void>;
  onError?: (err: Error) => void;
}

export function useVoiceSession({ onStop, onError }: VoiceSessionOptions) {
  const [state, setState] = useState<VoiceState>("idle");
  const [amplitude, setAmplitude] = useState(0);

  const streamRef = useRef<MediaStream | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const rafRef = useRef<number | null>(null);
  const activationFramesRef = useRef(0);
  const deactivationFramesRef = useRef(0);
  const isRecordingRef = useRef(false);
  const startTimeRef = useRef(0);
  const hardStopTimerRef = useRef<number | null>(null);

  const cleanup = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (hardStopTimerRef.current) window.clearTimeout(hardStopTimerRef.current);
    rafRef.current = null;
    hardStopTimerRef.current = null;
    recorderRef.current?.state === "recording" && recorderRef.current.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    ctxRef.current?.close().catch(() => {});
    recorderRef.current = null;
    streamRef.current = null;
    ctxRef.current = null;
    analyserRef.current = null;
    activationFramesRef.current = 0;
    deactivationFramesRef.current = 0;
    isRecordingRef.current = false;
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  const stop = useCallback(() => {
    if (!recorderRef.current) return;
    if (recorderRef.current.state !== "recording") {
      cleanup();
      setState("idle");
      return;
    }
    setState("processing");
    recorderRef.current.stop(); // onstop will assemble chunks and call onStop
  }, [cleanup]);

  const start = useCallback(async () => {
    if (state !== "idle") return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ctx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      ctxRef.current = ctx;
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      const source = ctx.createMediaStreamSource(stream);
      source.connect(analyser);
      analyserRef.current = analyser;

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        chunksRef.current = [];
        cleanup();
        try {
          await onStop(blob);
        } finally {
          setState("idle");
        }
      };
      recorderRef.current = recorder;

      recorder.start();
      isRecordingRef.current = true;
      startTimeRef.current = performance.now();
      setState("recording");

      hardStopTimerRef.current = window.setTimeout(() => stop(), MAX_DURATION_MS);

      const buffer = new Float32Array(analyser.fftSize);
      const tick = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getFloatTimeDomainData(buffer);
        let sumSq = 0;
        for (let i = 0; i < buffer.length; i++) sumSq += buffer[i] * buffer[i];
        const rms = Math.sqrt(sumSq / buffer.length);
        setAmplitude(rms);

        if (rms > ACTIVATION_THRESHOLD) {
          activationFramesRef.current++;
          deactivationFramesRef.current = 0;
        } else if (rms < DEACTIVATION_THRESHOLD) {
          deactivationFramesRef.current++;
          activationFramesRef.current = 0;
        }

        const elapsed = performance.now() - startTimeRef.current;
        if (
          isRecordingRef.current &&
          elapsed > 600 && // don't auto-stop in the first 600ms
          deactivationFramesRef.current >= DEACTIVATION_FRAMES &&
          activationFramesRef.current < ACTIVATION_FRAMES
        ) {
          isRecordingRef.current = false;
          stop();
          return;
        }

        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e));
      setState("error");
      onError?.(err);
      cleanup();
    }
  }, [state, stop, cleanup, onStop, onError]);

  return { state, amplitude, start, stop };
}
