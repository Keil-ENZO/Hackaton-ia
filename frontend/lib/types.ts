export interface Source {
  file: string;
  symbol: string | null;
  line: number | null;
  kind: "code" | "doc";
  label: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

export interface IngestSummary {
  files_indexed: number;
  chunks_created: number;
  languages: string[];
  message: string;
  repo_url: string;
  repo_name: string;
}

export interface HealthResponse {
  status: string;
  indexed_chunks: number;
  repo_name?: string | null;
  repo_url?: string | null;
}

// Dépôt actuellement indexé, tel que suivi côté front
export interface IndexedRepo {
  repoName: string;
  repoUrl: string;
  chunks: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}
