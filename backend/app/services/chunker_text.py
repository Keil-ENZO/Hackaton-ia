"""Chunking par paragraphe pour la doc et fallback général."""
from typing import Dict, List

TARGET_SIZE = 800
OVERLAP = 150


def chunk_text(content: str, rel_path: str) -> List[Dict]:
    """Découpe le texte en chunks ~800c avec chevauchement ~150c.

    Respecte les frontières de paragraphe (double saut de ligne) quand possible.
    Retourne une liste de dicts {text, source, symbol, line, kind}.
    """
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: List[Dict] = []
    buffer = ""
    # Ligne de départ approximative du buffer courant (1-indexée)
    buffer_start_line = 1
    consumed_lines = 0

    def flush(text: str, start_line: int) -> None:
        text = text.strip()
        if text:
            chunks.append(
                {
                    "text": text,
                    "source": rel_path,
                    "symbol": None,
                    "line": start_line,
                    "kind": "doc",
                }
            )

    for para in paragraphs:
        para_lines = para.count("\n") + 1

        if buffer and len(buffer) + len(para) + 2 > TARGET_SIZE:
            flush(buffer, buffer_start_line)
            # Chevauchement : on garde la fin du buffer précédent
            tail = buffer[-OVERLAP:]
            buffer = tail + "\n\n" + para
            buffer_start_line = max(1, consumed_lines - tail.count("\n"))
        else:
            if not buffer:
                buffer_start_line = consumed_lines + 1
                buffer = para
            else:
                buffer += "\n\n" + para

        # +2 pour le double saut de ligne séparateur
        consumed_lines += para_lines + 1

    flush(buffer, buffer_start_line)
    return chunks
