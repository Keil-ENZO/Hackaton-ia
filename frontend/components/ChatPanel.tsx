"use client";

import { useEffect, useRef, useState } from "react";
import { askQuestion } from "@/lib/api";
import type { Message } from "@/lib/types";
import ChatMessage from "./ChatMessage";

interface Props {
  ready: boolean;
  repoUrl?: string | null;
}

export default function ChatPanel({ ready, repoUrl }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await askQuestion(question);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: res.answer,
          sources: res.sources,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="flex min-h-0 flex-1 flex-col border border-border bg-panel">
      <div className="border-b border-border px-5 py-4">
        <h2 className="font-mono text-sm font-medium uppercase tracking-wider text-accent">
          2 · Poser une question
        </h2>
        <p className="mt-1 font-sans text-sm text-muted">
          Les réponses citent leurs sources (fichier, symbole, ligne).
        </p>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 space-y-4 overflow-y-auto px-5 py-4"
      >
        {messages.length === 0 && !loading && (
          <div className="flex h-full items-center justify-center text-center">
            <p className="max-w-sm font-sans text-sm text-muted">
              {ready
                ? "Pose ta première question sur le code indexé — par ex. « Où est géré l'authentification ? »"
                : "Indexe d'abord un dépôt ci-dessus pour activer le chat."}
            </p>
          </div>
        )}

        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} repoUrl={repoUrl} />
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-md border border-border bg-panel px-4 py-3 font-mono text-sm text-muted">
              <span className="inline-flex gap-1">
                <span className="[animation:pulse-dot_1s_ease-in-out_infinite]">
                  ●
                </span>
                <span className="[animation:pulse-dot_1s_ease-in-out_0.2s_infinite]">
                  ●
                </span>
                <span className="[animation:pulse-dot_1s_ease-in-out_0.4s_infinite]">
                  ●
                </span>
              </span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mx-5 mb-3 rounded-sm border border-red-500/40 bg-red-500/10 px-3 py-2 font-mono text-sm text-red-400">
          {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="flex gap-3 border-t border-border p-4"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            ready ? "Écris ta question…" : "Indexe un dépôt d'abord…"
          }
          disabled={!ready || loading}
          className="flex-1 rounded-sm border border-border bg-base px-3 py-2 font-sans text-sm text-foreground placeholder:text-muted/60 focus:border-accent disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!ready || loading || !input.trim()}
          className="rounded-sm border border-accent bg-accent/10 px-5 py-2 font-mono text-sm font-medium text-accent transition-colors hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Envoyer
        </button>
      </form>
    </section>
  );
}
