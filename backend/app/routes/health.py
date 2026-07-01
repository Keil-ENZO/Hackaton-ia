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
    return HealthResponse(status="ok", indexed_chunks=indexed)
