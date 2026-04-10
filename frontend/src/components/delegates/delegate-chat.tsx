"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { MessageSquare, Send, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { chat, type ChatSession, type ChatMessage } from "@/lib/api";

interface DelegateChatProps {
  delegateId: string;
  delegateLabel?: string;
}

export function DelegateChat({ delegateId, delegateLabel }: DelegateChatProps) {
  const [open, setOpen] = useState(false);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Create or fetch session when opened
  useEffect(() => {
    if (!open) return;
    chat
      .sessions(delegateId, 1)
      .then((sessions) => {
        if (sessions.length > 0) {
          setSession(sessions[0]);
          return chat.messages(sessions[0].id);
        } else {
          return chat.createSession(delegateId).then((s) => {
            setSession(s);
            return chat.messages(s.id);
          });
        }
      })
      .then((msgs) => setMessages(msgs ?? []))
      .catch(() => {});
  }, [open, delegateId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || !session || sending) return;
    const text = input.trim();
    setInput("");
    setSending(true);

    // Optimistic user message
    const tempMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: session.id,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempMsg]);

    try {
      const res = await chat.send(session.id, text);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempMsg.id),
        res.user_message,
        res.assistant_message,
      ]);
    } catch {
      // keep optimistic message, show error
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          session_id: session.id,
          role: "assistant",
          content: "Sorry, something went wrong. Try again.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  }, [input, session, sending]);

  return (
    <>
      {/* Floating toggle button */}
      <button
        onClick={() => setOpen((prev) => !prev)}
        className={cn(
          "fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full px-4 py-3 text-sm font-medium shadow-lg transition-all",
          open
            ? "bg-slate-800 text-white"
            : "bg-brand-600 text-white hover:bg-brand-700"
        )}
      >
        {open ? (
          <X className="w-4 h-4" />
        ) : (
          <MessageSquare className="w-4 h-4" />
        )}
        {!open && <span>Chat with {delegateLabel ?? delegateId}</span>}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-20 right-6 z-40 w-96 max-h-[500px] bg-white border border-slate-200 rounded-xl shadow-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100 bg-slate-50">
            <MessageSquare className="w-4 h-4 text-brand-600" />
            <span className="text-sm font-semibold text-slate-800">
              {delegateLabel ?? delegateId} Assistant
            </span>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[250px]">
            {messages.length === 0 && (
              <p className="text-xs text-slate-400 text-center pt-8">
                Ask anything about this delegate...
              </p>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                  msg.role === "user"
                    ? "ml-auto bg-brand-600 text-white"
                    : "bg-slate-100 text-slate-800"
                )}
              >
                {msg.content}
              </div>
            ))}
            {sending && (
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <Loader2 className="w-3 h-3 animate-spin" />
                Thinking...
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-slate-100 p-3">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
              <button
                type="submit"
                disabled={!input.trim() || sending}
                className="p-2 rounded-lg bg-brand-600 text-white disabled:opacity-50 hover:bg-brand-700 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
