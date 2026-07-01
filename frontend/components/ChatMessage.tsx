import type { Message } from "@/lib/types";
import SourceChip from "./SourceChip";

interface Props {
  message: Message;
  repoUrl?: string | null;
}

export default function ChatMessage({ message, repoUrl }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-md border px-4 py-3 ${
          isUser
            ? "border-accent/30 bg-accent/10"
            : "border-border bg-panel"
        }`}
      >
        <div className="mb-1 font-mono text-[11px] uppercase tracking-wider text-muted">
          {isUser ? "vous" : "copilot"}
        </div>
        <p className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-foreground">
          {message.content}
        </p>

        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 border-t border-border pt-3">
            <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-muted">
              sources
            </div>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((s, i) => (
                <SourceChip key={`${s.label}-${i}`} source={s} repoUrl={repoUrl} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
