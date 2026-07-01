"""Chunking Markdown par section (header # / ## / ###).

Contrairement à chunk_text qui coupe sur les doubles sauts de ligne,
ce chunker garde chaque section (titre + contenu) dans un seul chunk.
C'est crucial pour que les commandes shell d'une section « Installation »
restent attachées à leur titre et soient retrouvées par similarité.
"""
import re
from typing import Dict, List

from app.services.chunker_text import chunk_text

# Regex qui détecte les titres Markdown (H1 à H4)
HEADER_RE = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)

MAX_SECTION_SIZE = 1200  # Si une section est trop longue, on la re-coupe


def chunk_markdown(content: str, rel_path: str) -> List[Dict]:
    """Découpe un fichier Markdown en sections (un chunk par header).

    - Chaque chunk contient : le titre de section + son contenu.
    - Les sections trop longues (> MAX_SECTION_SIZE) sont re-découpées
      par chunk_text pour éviter de dépasser la fenêtre de contexte.
    - Retourne une liste de dicts {text, source, symbol, line, kind}.
    """
    # Trouver tous les headers et leurs positions
    matches = list(HEADER_RE.finditer(content))

    if not matches:
        # Pas de headers : fallback sur chunk_text standard
        return chunk_text(content, rel_path)

    chunks: List[Dict] = []

    for i, match in enumerate(matches):
        section_start = match.start()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)

        section_text = content[section_start:section_end].strip()
        if not section_text:
            continue

        header_text = match.group(2).strip()  # Texte du titre sans les #
        line_number = content[:section_start].count("\n") + 1

        if len(section_text) <= MAX_SECTION_SIZE:
            chunks.append(
                {
                    "text": section_text,
                    "source": rel_path,
                    "symbol": header_text,  # Le titre = le "symbole" de la section
                    "line": line_number,
                    "kind": "doc",
                    "node_type": "markdown_section",
                }
            )
        else:
            # Section trop longue : on la re-coupe mais on garde le titre en header
            sub_chunks = chunk_text(section_text, rel_path)
            for j, sc in enumerate(sub_chunks):
                sc["symbol"] = header_text if j == 0 else f"{header_text} (suite)"
                sc["line"] = line_number
                sc["node_type"] = "markdown_section"
                chunks.append(sc)

    # Contenu avant le premier header (ex : intro du README)
    if matches and matches[0].start() > 0:
        intro = content[: matches[0].start()].strip()
        if intro:
            chunks.insert(
                0,
                {
                    "text": intro,
                    "source": rel_path,
                    "symbol": "intro",
                    "line": 1,
                    "kind": "doc",
                    "node_type": "markdown_section",
                },
            )

    return chunks if chunks else chunk_text(content, rel_path)
