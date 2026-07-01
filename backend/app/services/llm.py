"""Client Groq + construction du prompt anti-hallucination."""
from typing import Dict, List

from app.config import settings

SYSTEM_PROMPT = """Tu es DevOnboard Copilot, un assistant d'onboarding pour développeurs.
Tu réponds UNIQUEMENT à partir du CONTEXTE fourni ci-dessous, extrait du code source,
de la documentation et des fichiers de configuration d'un dépôt Git.

Règles strictes :
- N'invente JAMAIS de réponse. Si le contexte ne contient pas l'information, réponds
  clairement : "Je ne trouve pas cette information dans le code indexé."
- Cite tes sources en te basant sur les extraits fournis (nom de fichier, symbole, ligne).
- Sois concis, technique et précis. Réponds en français.
- N'utilise aucune connaissance externe au contexte pour affirmer des faits sur ce dépôt.
- Pour les questions opérationnelles (comment lancer, déployer, installer, configurer),
  prioritise les fichiers [CONFIG] : docker-compose.yml, Dockerfile, Makefile, README,
  scripts shell et fichiers .env. Ces fichiers contiennent les commandes exactes.
- Reproduis les commandes shell exactes trouvées dans le contexte, sans les paraphraser.
"""


def _build_context(retrieved: List[Dict]) -> str:
    """Formate les chunks récupérés en un bloc de contexte lisible par le LLM."""
    blocks = []
    for i, item in enumerate(retrieved, start=1):
        meta = item["metadata"]
        source = meta.get("source", "?")
        symbol = meta.get("symbol") or ""
        line = meta.get("line") or 0
        kind = meta.get("kind", "doc")

        if kind == "code":
            header = f"[{i}] CODE — {source}::{symbol} (ligne {line})"
        elif kind == "config":
            header = f"[{i}] CONFIG — {source}"
            if symbol:
                header += f" :: {symbol}"
        else:
            header = f"[{i}] DOC — {source}"
            if symbol:
                header += f" :: {symbol}"

        blocks.append(f"{header}\n```\n{item['text']}\n```")

    return "\n\n".join(blocks)


def generate_answer(question: str, retrieved: List[Dict]) -> str:
    """Appelle Groq avec le contexte + la question et retourne la réponse."""
    from groq import Groq

    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY manquante dans l'environnement.")

    context = _build_context(retrieved)
    user_content = (
        f"CONTEXTE :\n{context}\n\n"
        f"QUESTION :\n{question}\n\n"
        "Réponds en te basant strictement sur le contexte ci-dessus."
    )

    client = Groq(api_key=settings.GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        max_tokens=1024,
    )
    return completion.choices[0].message.content or ""
