"""GET /health — statut + nombre de chunks indexés (réveil du service)."""
from fastapi import APIRouter

from app.models import HealthResponse
from app.services import vector_store

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        indexed = vector_store.count()
    except Exception:
        indexed = 0

    # On n'expose les infos du dépôt que si l'index est réellement peuplé
    meta = vector_store.get_repo_meta() if indexed > 0 else None
    return HealthResponse(
        status="ok",
        indexed_chunks=indexed,
        repo_name=(meta or {}).get("repo_name"),
        repo_url=(meta or {}).get("repo_url"),
    )
