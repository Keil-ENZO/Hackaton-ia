"use client";

import { useState } from "react";
import { ingestRepo } from "@/lib/api";
import type { IngestSummary } from "@/lib/types";

interface Props {
  onIndexed: (summary: IngestSummary) => void;
}

export default function IngestPanel({ onIndexed }: Props) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<IngestSummary | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim() || loading) return;

    setLoading(true);
    setError(null);
    setSummary(null);
    try {
      const result = await ingestRepo(url.trim());
      setSummary(result);
      onIndexed(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="border border-border bg-panel p-5">
      <h2 className="mb-1 font-mono text-sm font-medium uppercase tracking-wider text-accent">
        1 · Indexer un dépôt
      </h2>
      <p className="mb-4 font-sans text-sm text-muted">
        Colle l&apos;URL d&apos;un dépôt GitHub public. Le code et la doc seront
        clonés puis indexés localement.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          disabled={loading}
          className="flex-1 rounded-sm border border-border bg-base px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted/60 focus:border-accent disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="inline-flex items-center justify-center gap-2 rounded-sm border border-accent bg-accent/10 px-5 py-2 font-mono text-sm font-medium text-accent transition-colors hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? (
            <>
              <Spinner />
              Indexation…
            </>
          ) : (
            "Indexer"
          )}
        </button>
      </form>

      {loading && (
        <div className="mt-4 flex items-center gap-2 font-sans text-sm text-muted">
          <span className="inline-block h-2 w-2 rounded-full bg-accent [animation:pulse-dot_1.2s_ease-in-out_infinite]" />
          Clonage, parsing AST et génération des embeddings en cours — cela peut
          prendre plusieurs dizaines de secondes sur un gros dépôt.
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-sm border border-red-500/40 bg-red-500/10 px-3 py-2 font-mono text-sm text-red-400">
          {error}
        </div>
      )}

      {summary && (
        <div className="mt-4 rounded-sm border border-accent/30 bg-accent/5 px-3 py-2 font-sans text-sm text-foreground">
          <span className="font-mono text-accent">✓</span> {summary.files_indexed}{" "}
          fichiers · {summary.chunks_created} chunks
          {summary.languages.length > 0 && (
            <> · langages : {summary.languages.join(", ")}</>
          )}
        </div>
      )}
    </section>
  );
}

function Spinner() {
  return (
    <svg
      className="spinner h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
        strokeOpacity="0.3"
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
