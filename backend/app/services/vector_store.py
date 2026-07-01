"""Wrapper autour de ChromaDB (PersistentClient)."""
import json
import os
from functools import lru_cache
from typing import Dict, List, Optional

from app.config import settings

# Métadonnées du dépôt courant (nom, url, stats) — persistées à côté de Chroma
# pour que le front connaisse le repo indexé même après un rechargement de page.
_META_PATH = os.path.join(settings.CHROMA_PERSIST_DIR, "repo_meta.json")


def set_repo_meta(meta: Dict) -> None:
    """Enregistre les métadonnées du dépôt actuellement indexé."""
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    with open(_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f)


def get_repo_meta() -> Optional[Dict]:
    """Retourne les métadonnées du dépôt indexé, ou None."""
    try:
        with open(_META_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _delete_repo_meta() -> None:
    try:
        os.remove(_META_PATH)
    except OSError:
        pass


def _make_client():
    """Crée un PersistentClient avec la télémétrie coupée (bug PostHog bruyant)."""
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    return chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


@lru_cache(maxsize=1)
def _get_collection():
    client = _make_client()
    # On fournit nous-mêmes les embeddings -> pas de fonction d'embedding interne.
    return client.get_or_create_collection(
        name=settings.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _clean_metadata(chunk: Dict) -> Dict:
    """Prépare des métadonnées compatibles Chroma (pas de None)."""
    return {
        "source": chunk.get("source") or "",
        "symbol": chunk.get("symbol") or "",
        "line": int(chunk.get("line") or 0),
        "kind": chunk.get("kind") or "doc",
        "node_type": chunk.get("node_type") or "",
    }


def reset() -> None:
    """Vide la collection (l'outil gère un seul dépôt à la fois)."""
    client = _make_client()
    try:
        client.delete_collection(settings.COLLECTION_NAME)
    except Exception:
        pass  # la collection peut ne pas exister encore
    # Invalide le cache pour recréer une collection vide au prochain accès
    _get_collection.cache_clear()


def clear() -> None:
    """Vide l'index ET oublie le dépôt courant (bouton « Vider » côté front)."""
    reset()
    _delete_repo_meta()


def add_chunks(chunks: List[Dict], embeddings: List[List[float]]) -> None:
    """Ajoute des chunks + embeddings à la collection."""
    if not chunks:
        return

    collection = _get_collection()
    base = collection.count()
    ids = [f"chunk-{base + i}" for i in range(len(chunks))]
    documents = [c["text"] for c in chunks]
    metadatas = [_clean_metadata(c) for c in chunks]

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def query(embedding: List[float], top_k: int) -> List[Dict]:
    """Recherche les top_k chunks les plus proches. Retourne texte + métadonnées."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, collection.count()),
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    out: List[Dict] = []
    for doc, meta in zip(documents, metadatas):
        out.append({"text": doc, "metadata": meta})
    return out


def count() -> int:
    """Nombre de chunks indexés."""
    return _get_collection().count()
