"""Schémas Pydantic pour les requêtes/réponses de l'API."""
from typing import List, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    repo_url: str = Field(..., description="URL d'un repo GitHub public")
    replace: bool = Field(
        default=False,
        description="Autorise le remplacement d'un dépôt déjà indexé",
    )


class IngestResponse(BaseModel):
    files_indexed: int
    chunks_created: int
    languages: List[str]
    message: str
    repo_url: str   # URL web du dépôt (ex. https://github.com/owner/repo)
    repo_name: str  # owner/repo


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


class Source(BaseModel):
    file: str
    symbol: Optional[str] = None
    line: Optional[int] = None
    kind: str  # "code" ou "doc"
    label: str  # "fichier::symbole (ligne X)" ou "fichier"


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]


class HealthResponse(BaseModel):
    status: str
    indexed_chunks: int
    repo_name: Optional[str] = None  # owner/repo actuellement indexé, si présent
    repo_url: Optional[str] = None


class ClearResponse(BaseModel):
    status: str
    indexed_chunks: int
