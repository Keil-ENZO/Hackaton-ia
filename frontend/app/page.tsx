"use client";

import { useEffect, useState } from "react";
import IngestPanel from "@/components/IngestPanel";
import ChatPanel from "@/components/ChatPanel";
import { getHealth } from "@/lib/api";

export default function Home() {
  const [ready, setReady] = useState(false);
  const [indexedChunks, setIndexedChunks] = useState<number | null>(null);
  const [repoUrl, setRepoUrl] = useState<string | null>(null);
  const [repoName, setRepoName] = useState<string | null>(null);

  // Réveille le backend (Render s'endort après 15 min) et récupère l'état.
  useEffect(() => {
    getHealth()
      .then((h) => {
        setIndexedChunks(h.indexed_chunks);
        setReady(h.indexed_chunks > 0);
      })
      .catch(() => setIndexedChunks(null));
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
        {indexedChunks !== null && (
          <p className="mt-1 font-mono text-xs text-muted">
            backend en ligne · {indexedChunks} chunks indexés
            {repoName && (
              <>
                {" · "}
                <span className="text-source">{repoName}</span>
              </>
            )}
          </p>
        )}
      </header>

      <IngestPanel
        onIndexed={(summary) => {
          setReady(summary.chunks_created > 0);
          setIndexedChunks(summary.chunks_created);
          setRepoUrl(summary.repo_url);
          setRepoName(summary.repo_name);
        }}
      />

      <ChatPanel ready={ready} repoUrl={repoUrl} />

      <footer className="border-t border-border pt-4 text-center font-mono text-xs text-muted">
        DevOnboard Copilot · FastAPI + Next.js + Groq + ChromaDB
      </footer>
    </main>
  );
}
