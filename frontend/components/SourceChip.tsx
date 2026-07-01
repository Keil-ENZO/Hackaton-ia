import type { Source } from "@/lib/types";

interface Props {
  source: Source;
  repoUrl?: string | null;
}

function buildGithubLink(source: Source, repoUrl: string): string {
  // repoUrl = https://github.com/owner/repo — HEAD résout la branche par défaut
  const path = source.file.split("/").map(encodeURIComponent).join("/");
  const base = `${repoUrl.replace(/\/$/, "")}/blob/HEAD/${path}`;
  return source.line ? `${base}#L${source.line}` : base;
}

export default function SourceChip({ source, repoUrl }: Props) {
  const className =
    "inline-flex items-center gap-1 rounded-sm border border-source/40 bg-source/10 px-2 py-0.5 font-mono text-xs text-source transition-colors";
  const icon = (
    <span aria-hidden className="text-source/70">
      {source.kind === "code" ? "{}" : "#"}
    </span>
  );

  if (repoUrl) {
    return (
      <a
        href={buildGithubLink(source, repoUrl)}
        target="_blank"
        rel="noopener noreferrer"
        title={`Ouvrir ${source.label} sur GitHub`}
        className={`${className} hover:bg-source/20 hover:underline`}
      >
        {icon}
        {source.label}
      </a>
    );
  }

  return (
    <span className={className} title={source.label}>
      {icon}
      {source.label}
    </span>
  );
}
