"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Send, Plus, Bot, User, Mic, Volume2, Clock } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { VoiceButton } from "@/components/chat/voice-button";
import { useVoiceSession } from "@/hooks/use-voice-session";
import { cn } from "@/lib/utils";
import {
  chat as chatApi,
  voice as voiceApi,
  type ChatSession,
  type ChatMessage,
  type VoiceTimings,
} from "@/lib/api";

const DELEGATES = [
  { id: "recruiter", label: "Recruiter" },
  { id: "calendar", label: "Calendar" },
  { id: "comms", label: "Comms" },
  { id: "finance", label: "Finance" },
  { id: "shopping", label: "Shopping" },
  { id: "learning", label: "Learning" },
  { id: "health", label: "Health" },
];

function DebugTimings({ t }: { t: VoiceTimings }) {
  return (
    <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
      <Clock className="w-3 h-3" />
      <span>STT {t.stt_ms ?? "—"}ms</span>
      <span>·</span>
      <span>LLM {t.workflow_ms ?? "—"}ms</span>
      <span>·</span>
      <span>TTS {t.tts_ms ?? "—"}ms</span>
      <span>·</span>
      <span className="text-slate-500">total {t.total_ms ?? "—"}ms</span>
    </div>
  );
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [lastTimings, setLastTimings] = useState<VoiceTimings | null>(null);
  const [debug, setDebug] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeId) ?? null,
    [sessions, activeId],
  );

  // Dev panel toggle: Ctrl+Shift+D (Rose convention)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "d") {
        e.preventDefault();
        setDebug((d) => !d);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const loadSessions = useCallback(async () => {
    const rows = await chatApi.sessions();
    setSessions(rows);
    if (!activeId && rows.length) setActiveId(rows[0].id);
  }, [activeId]);

  useEffect(() => {
    loadSessions().catch(console.error);
  }, [loadSessions]);

  useEffect(() => {
    if (!activeId) return;
    chatApi.messages(activeId).then(setMessages).catch(console.error);
  }, [activeId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const createSession = async (delegateId: string) => {
    const s = await chatApi.createSession(delegateId);
    setSessions((prev) => [s, ...prev]);
    setActiveId(s.id);
    setMessages([]);
  };

  const sendText = async () => {
    const content = input.trim();
    if (!content || !activeId || sending) return;
    setInput("");
    setSending(true);
    try {
      const result = await chatApi.send(activeId, content);
      setMessages((prev) => [...prev, result.user_message, result.assistant_message]);
    } catch (e) {
      console.error(e);
    } finally {
      setSending(false);
    }
  };

  const handleVoiceStop = useCallback(
    async (blob: Blob) => {
      if (!activeId) return;
      setSending(true);
      try {
        const result = await voiceApi.chat(activeId, blob);
        setLastTimings(result.timings);

        // Reload the thread so we see the persisted user + assistant turns.
        const msgs = await chatApi.messages(activeId);
        setMessages(msgs);

        if (result.audio_url && audioRef.current) {
          audioRef.current.src = voiceApi.audioUrl(result.audio_url);
          audioRef.current.play().catch(() => {});
        }
      } catch (e) {
        console.error(e);
      } finally {
        setSending(false);
      }
    },
    [activeId],
  );

  const voice = useVoiceSession({
    onStop: handleVoiceStop,
    onError: (e) => console.error("voice error", e),
  });

  return (
    <div>
      <PageHeader
        title="Chat"
        subtitle="Talk to a delegate — text or voice"
        actions={
          <div className="flex items-center gap-2">
            {debug && lastTimings && <DebugTimings t={lastTimings} />}
            <span className="text-[10px] text-slate-400">Ctrl+Shift+D for timings</span>
          </div>
        }
      />

      <div className="flex gap-4 h-[calc(100vh-10rem)]">
        {/* Session list */}
        <aside className="w-64 flex-shrink-0 bg-white border border-slate-200 rounded-xl overflow-hidden flex flex-col">
          <div className="p-3 border-b border-slate-100">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
              New chat
            </p>
            <div className="grid grid-cols-2 gap-1">
              {DELEGATES.map((d) => (
                <button
                  key={d.id}
                  onClick={() => createSession(d.id)}
                  className="text-[11px] py-1 px-2 bg-slate-50 hover:bg-brand-50 hover:text-brand-600 rounded transition-colors text-left truncate"
                  title={`Chat with ${d.label}`}
                >
                  <Plus className="inline w-3 h-3 -mt-0.5 mr-1" />
                  {d.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => setActiveId(s.id)}
                className={cn(
                  "w-full text-left px-3 py-2 border-b border-slate-50 hover:bg-slate-50 transition-colors",
                  activeId === s.id && "bg-brand-50",
                )}
              >
                <div className="flex items-center gap-2">
                  <Bot className="w-3.5 h-3.5 text-brand-500" />
                  <span className="text-sm font-medium text-slate-800 capitalize">
                    {s.delegate_id}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  {new Date(s.updated_at).toLocaleString()}
                </p>
              </button>
            ))}
            {!sessions.length && (
              <div className="p-6 text-center text-xs text-slate-400">
                No sessions yet. Pick a delegate above to start one.
              </div>
            )}
          </div>
        </aside>

        {/* Conversation */}
        <main className="flex-1 bg-white border border-slate-200 rounded-xl flex flex-col overflow-hidden">
          {activeSession ? (
            <>
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-slate-800 capitalize">
                    {activeSession.delegate_id}
                  </div>
                  <div className="text-[10px] text-slate-400">Session {activeSession.id.slice(0, 8)}</div>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={cn(
                      "flex gap-2",
                      m.role === "user" ? "justify-end" : "justify-start",
                    )}
                  >
                    {m.role === "assistant" && (
                      <div className="w-6 h-6 rounded-full bg-brand-50 border border-brand-200 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-3.5 h-3.5 text-brand-600" />
                      </div>
                    )}
                    <div
                      className={cn(
                        "max-w-[70%] px-3 py-2 rounded-xl text-sm whitespace-pre-wrap leading-relaxed",
                        m.role === "user"
                          ? "bg-brand-500 text-white rounded-br-sm"
                          : "bg-slate-100 text-slate-800 rounded-bl-sm",
                      )}
                    >
                      {m.content}
                    </div>
                    {m.role === "user" && (
                      <div className="w-6 h-6 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center flex-shrink-0">
                        <User className="w-3.5 h-3.5 text-slate-500" />
                      </div>
                    )}
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>

              <div className="px-3 py-3 border-t border-slate-100 flex items-center gap-2">
                <VoiceButton
                  state={voice.state}
                  amplitude={voice.amplitude}
                  onStart={voice.start}
                  onStop={voice.stop}
                  disabled={sending}
                />
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendText();
                    }
                  }}
                  placeholder="Message or press 🎤 to speak..."
                  disabled={sending}
                  className="flex-1 text-sm px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
                />
                <button
                  onClick={sendText}
                  disabled={sending || !input.trim()}
                  className={cn(
                    "inline-flex items-center gap-1 px-3 py-2 text-xs font-medium rounded-lg transition-colors",
                    input.trim()
                      ? "bg-brand-500 text-white hover:bg-brand-600"
                      : "bg-slate-100 text-slate-300 cursor-not-allowed",
                  )}
                >
                  <Send className="w-3.5 h-3.5" />
                  Send
                </button>
              </div>
              <audio ref={audioRef} autoPlay />
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-center p-10">
              <div className="max-w-sm">
                <Mic className="w-10 h-10 text-slate-200 mx-auto mb-3" />
                <p className="text-sm font-medium text-slate-600 mb-1">No active chat</p>
                <p className="text-xs text-slate-400">
                  Pick a delegate on the left to start a new conversation. Voice requires{" "}
                  <span className="font-mono">GROQ_API_KEY</span> and{" "}
                  <span className="font-mono">ELEVENLABS_API_KEY</span> in Settings.
                </p>
                <p className="text-[10px] text-slate-300 mt-4 flex items-center justify-center gap-1">
                  <Volume2 className="w-3 h-3" /> Replies with valid TTS autoplay.
                </p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
