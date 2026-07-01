"""POST /chat — retrieval + génération Groq + sources citées."""
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ChatRequest, ChatResponse, Source
from app.services import embeddings, llm, vector_store

router = APIRouter()


def _to_source(meta: dict) -> Source:
    kind = meta.get("kind", "doc")
    source = meta.get("source", "?")
    symbol = meta.get("symbol") or None
    line = meta.get("line") or None

    if kind == "code":
        symbol_part = symbol or "?"
        label = f"{source}::{symbol_part}"
        if line:
            label += f" (ligne {line})"
    else:
        label = source

    return Source(file=source, symbol=symbol, line=line, kind=kind, label=label)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide.")

    if vector_store.count() == 0:
        raise HTTPException(
            status_code=409,
            detail="Aucun dépôt indexé. Lance d'abord une indexation.",
        )

    # 1. Embed la question + recherche top_k
    query_vec = embeddings.embed_query(question)
    retrieved = vector_store.query(query_vec, settings.TOP_K)

    if not retrieved:
        return ChatResponse(
            answer="Je ne trouve pas cette information dans le code indexé.",
            sources=[],
        )

    # 2. Génération via Groq
    try:
        answer = llm.generate_answer(question, retrieved)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur Groq : {exc}") from exc

    # 3. Déduplication des sources en conservant l'ordre
    sources = []
    seen = set()
    for item in retrieved:
        src = _to_source(item["metadata"])
        if src.label not in seen:
            seen.add(src.label)
            sources.append(src)

    return ChatResponse(answer=answer, sources=sources)
