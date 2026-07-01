"use client";

import { useState } from "react";
import { clearIndex, ingestRepo } from "@/lib/api";
import type { IndexedRepo, IngestSummary } from "@/lib/types";

interface Props {
  indexed: IndexedRepo | null;
  onIndexed: (summary: IngestSummary) => void;
  onCleared: () => void;
}

export default function IngestPanel({ indexed, onIndexed, onCleared }: Props) {
  const [url, setUrl] = useState("");
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Formulaire visible si aucun repo indexé, ou si l'on remplace explicitement.
  const showForm = !indexed || editing;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim() || loading) return;

    setLoading(true);
    setError(null);
    try {
      // replace=true quand on remplace un dépôt déjà indexé
      const result = await ingestRepo(url.trim(), Boolean(indexed));
      onIndexed(result);
      setUrl("");
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }

  async function handleClear() {
    if (clearing || loading) return;
    setClearing(true);
    setError(null);
    try {
      await clearIndex();
      onCleared();
      setEditing(false);
      setUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setClearing(false);
    }
  }

  return (
    <section className="border border-border bg-panel p-5">
      <h2 className="mb-1 font-mono text-sm font-medium uppercase tracking-wider text-accent">
        1 · Indexer un dépôt
      </h2>
      <p className="mb-4 font-sans text-sm text-muted">
        Un seul dépôt à la fois. Colle l&apos;URL d&apos;un dépôt GitHub public ;
        le code et la doc seront clonés puis indexés.
      </p>

      {/* État : un dépôt est déjà indexé */}
      {indexed && !editing && (
        <div className="flex flex-col gap-3 rounded-sm border border-accent/30 bg-accent/5 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="font-sans text-sm text-foreground">
            <span className="font-mono text-accent">✓</span>{" "}
            <span className="font-mono text-source">{indexed.repoName}</span>{" "}
            est indexé
            <span className="text-muted"> · {indexed.chunks} chunks</span>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                setEditing(true);
                setError(null);
              }}
              disabled={clearing}
              className="rounded-sm border border-accent bg-accent/10 px-4 py-1.5 font-mono text-xs font-medium text-accent transition-colors hover:bg-accent/20 disabled:opacity-40"
            >
              Remplacer
            </button>
            <button
              type="button"
              onClick={handleClear}
              disabled={clearing}
              className="rounded-sm border border-border px-4 py-1.5 font-mono text-xs font-medium text-muted transition-colors hover:border-red-500/50 hover:text-red-400 disabled:opacity-40"
            >
              {clearing ? "Suppression…" : "Vider"}
            </button>
          </div>
        </div>
      )}

      {/* Formulaire d'indexation / remplacement */}
      {showForm && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            disabled={loading}
            autoFocus={editing}
            className="flex-1 rounded-sm border border-border bg-base px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted/60 focus:border-accent disabled:opacity-50"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-sm border border-accent bg-accent/10 px-5 py-2 font-mono text-sm font-medium text-accent transition-colors hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-40 sm:flex-none"
            >
              {loading ? (
                <>
                  <Spinner />
                  Indexation…
                </>
              ) : indexed ? (
                "Remplacer"
              ) : (
                "Indexer"
              )}
            </button>
            {editing && !loading && (
              <button
                type="button"
                onClick={() => {
                  setEditing(false);
                  setUrl("");
                  setError(null);
                }}
                className="rounded-sm border border-border px-4 py-2 font-mono text-sm text-muted transition-colors hover:text-foreground"
              >
                Annuler
              </button>
            )}
          </div>
        </form>
      )}

      {loading && (
        <div className="mt-4 flex items-center gap-2 font-sans text-sm text-muted">
          <span className="inline-block h-2 w-2 rounded-full bg-accent [animation:pulse-dot_1.2s_ease-in-out_infinite]" />
          Clonage, parsing AST et génération des embeddings en cours — cela peut
          prendre plusieurs dizaines de secondes.
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-sm border border-red-500/40 bg-red-500/10 px-3 py-2 font-mono text-sm text-red-400">
          {error}
        </div>
      )}
    </section>
  );
}

function Spinner() {
  return (
    <svg className="spinner h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden>
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
