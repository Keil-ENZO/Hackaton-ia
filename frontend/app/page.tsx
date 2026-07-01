"use client";

import { useEffect, useState } from "react";
import IngestPanel from "@/components/IngestPanel";
import ChatPanel from "@/components/ChatPanel";
import { getHealth } from "@/lib/api";
import type { IndexedRepo } from "@/lib/types";

export default function Home() {
  const [online, setOnline] = useState(false);
  const [indexed, setIndexed] = useState<IndexedRepo | null>(null);

  // Réveille le backend (Render s'endort après 15 min) et récupère l'état.
  useEffect(() => {
    getHealth()
      .then((h) => {
        setOnline(true);
        if (h.indexed_chunks > 0 && h.repo_name && h.repo_url) {
          setIndexed({
            repoName: h.repo_name,
            repoUrl: h.repo_url,
            chunks: h.indexed_chunks,
          });
        }
      })
      .catch(() => setOnline(false));
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-4 py-8 sm:px-6">
      <header className="flex flex-col gap-1 border-b border-border pb-5">
        <h1 className="font-mono text-2xl font-semibold tracking-tight text-foreground">
          DevOnboard <span className="text-accent">Copilot</span>
        </h1>
        <p className="font-sans text-sm text-muted">
          Indexe un dépôt Git public et interroge son code — réponses sourcées à
          la ligne près.
        </p>
        {online && (
          <p className="mt-1 font-mono text-xs text-muted">
            backend en ligne
            {indexed ? (
              <>
                {" · "}
                {indexed.chunks} chunks indexés
                {" · "}
                <span className="text-source">{indexed.repoName}</span>
              </>
            ) : (
              " · aucun dépôt indexé"
            )}
          </p>
        )}
      </header>

      <IngestPanel
        indexed={indexed}
        onIndexed={(summary) =>
          setIndexed({
            repoName: summary.repo_name,
            repoUrl: summary.repo_url,
            chunks: summary.chunks_created,
          })
        }
        onCleared={() => setIndexed(null)}
      />

      <ChatPanel ready={Boolean(indexed)} repoUrl={indexed?.repoUrl ?? null} />

      <footer className="border-t border-border pt-4 text-center font-mono text-xs text-muted">
        DevOnboard Copilot · FastAPI + Next.js + Groq + ChromaDB
      </footer>
    </main>
  );
}
